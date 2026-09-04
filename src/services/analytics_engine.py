import math
import logging
import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("analytics_engine")

RISK_FREE_RATE = 0.071  # Indian 10-Year G-Sec yield ~7.1%


class QuantitativeAnalyticsEngine:

    def calculate_portfolio_metrics(self, holdings: List[Dict[str, Any]],
                                    trades: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if not holdings:
            return self._empty_metrics()

        total_invested = sum(h.get("quantity", 0) * h.get("average_price", 0) for h in holdings)
        total_current  = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in holdings)
        total_pnl      = total_current - total_invested
        overall_return = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

        # XIRR: use real trade cash flows when available, else estimate
        xirr = self._xirr_from_trades(trades, total_current) if trades else self._estimate_xirr(total_invested, total_current)

        weighted_pe = weighted_roe = portfolio_beta = hhi = 0.0
        for h in holdings:
            val    = h.get("quantity", 0) * h.get("last_price", 0)
            weight = (val / total_current) if total_current > 0 else 0.0
            weighted_pe   += weight * h.get("pe_ratio", 20.0)
            weighted_roe  += weight * h.get("roe", 15.0)
            portfolio_beta += weight * self._infer_beta(h.get("tradingsymbol", ""), h.get("sector", ""))
            hhi            += (weight * 100) ** 2

        ann_return       = xirr / 100.0
        est_vol          = max(0.12 * portfolio_beta, 0.08)
        sharpe           = (ann_return - RISK_FREE_RATE) / est_vol if est_vol > 0 else 0.0
        sortino          = (ann_return - RISK_FREE_RATE) / (est_vol * 0.7) if est_vol > 0 else 0.0

        return {
            "xirr_percentage":        round(xirr, 2),
            "overall_return_percentage": round(overall_return, 2),
            "portfolio_beta":         round(portfolio_beta, 2),
            "sharpe_ratio":           round(sharpe, 2),
            "sortino_ratio":          round(sortino, 2),
            "herfindahl_index":       round(hhi, 0),
            "weighted_pe":            round(weighted_pe, 2),
            "weighted_roe":           round(weighted_roe, 2),
            "risk_profile_tag":       self._risk_tag(portfolio_beta, hhi),
        }

    # ------------------------------------------------------------------
    # XIRR — Newton-Raphson solver using actual trade cash flows
    # ------------------------------------------------------------------
    def _xirr_from_trades(self, trades: List[Dict[str, Any]], current_value: float) -> float:
        """
        Builds cash flow series from trade history:
          - BUY  → negative cash flow (money out)
          - SELL → positive cash flow (money in)
          - Final portfolio value → positive cash flow at today's date
        """
        today = datetime.date.today()
        cash_flows: List[tuple] = []  # (date, amount)

        for t in trades:
            try:
                trade_date = datetime.datetime.strptime(
                    str(t.get("fill_timestamp", t.get("order_timestamp", ""))).split(" ")[0],
                    "%Y-%m-%d"
                ).date()
            except Exception:
                continue

            qty   = float(t.get("quantity", 0) or 0)
            price = float(t.get("average_price", t.get("price", 0)) or 0)
            txn   = t.get("transaction_type", "BUY").upper()
            amount = qty * price
            cash_flows.append((trade_date, -amount if txn == "BUY" else amount))

        if not cash_flows:
            return 0.0

        # Add current portfolio value as terminal cash flow
        cash_flows.append((today, current_value))
        cash_flows.sort(key=lambda x: x[0])

        base_date = cash_flows[0][0]
        amounts   = [cf[1] for cf in cash_flows]
        days      = [(cf[0] - base_date).days for cf in cash_flows]

        return self._newton_xirr(amounts, days)

    def _newton_xirr(self, amounts: List[float], days: List[int],
                     guess: float = 0.1, max_iter: int = 100, tol: float = 1e-6) -> float:
        rate = guess
        for _ in range(max_iter):
            npv  = sum(a / (1 + rate) ** (d / 365.0) for a, d in zip(amounts, days))
            dnpv = sum(-d / 365.0 * a / (1 + rate) ** (d / 365.0 + 1) for a, d in zip(amounts, days))
            if dnpv == 0:
                break
            new_rate = rate - npv / dnpv
            if abs(new_rate - rate) < tol:
                return round(new_rate * 100, 2)
            rate = new_rate
        return 0.0

    def _estimate_xirr(self, invested: float, current: float, holding_years: float = 1.2) -> float:
        """Fallback CAGR estimate when no trade history is available."""
        if invested <= 0 or current <= 0:
            return 0.0
        try:
            return round((math.pow(current / invested, 1.0 / holding_years) - 1.0) * 100, 2)
        except Exception:
            return 0.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _infer_beta(self, symbol: str, sector: str) -> float:
        beta_map = {
            "RELIANCE": 0.95, "TCS": 0.78, "INFY": 0.85, "HDFCBANK": 0.92,
            "ICICIBANK": 1.05, "SBIN": 1.15, "TATAMOTORS": 1.35,
            "SUNPHARMA": 0.65, "LTIM": 1.20, "LT": 1.10,
        }
        if symbol.upper() in beta_map:
            return beta_map[symbol.upper()]
        if "Technology" in sector:   return 0.90
        if "Financial" in sector:    return 1.10
        if "Pharma" in sector or "Healthcare" in sector: return 0.70
        if "Automotive" in sector or "Metals" in sector: return 1.25
        return 1.00

    def _risk_tag(self, beta: float, hhi: float) -> str:
        if beta > 1.20 or hhi > 2500:
            return "High risk / Aggressive growth"
        if beta < 0.85 and hhi < 1500:
            return "Low volatility / Defensive"
        return "Moderate risk / Balanced growth"

    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            "xirr_percentage": 0.0, "overall_return_percentage": 0.0,
            "portfolio_beta": 1.0, "sharpe_ratio": 0.0, "sortino_ratio": 0.0,
            "herfindahl_index": 0.0, "weighted_pe": 0.0, "weighted_roe": 0.0,
            "risk_profile_tag": "Moderate risk / Balanced growth",
        }


analytics_engine = QuantitativeAnalyticsEngine()
