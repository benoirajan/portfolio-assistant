import math
import logging
import datetime
from typing import Dict, List, Any, Tuple

logger = logging.getLogger("analytics_engine")

RISK_FREE_RATE = 0.071  # Indian 10-Year Government Bond Yield ~7.1%

class QuantitativeAnalyticsEngine:
    """Computes advanced financial analytics: XIRR, Sharpe Ratio, Sortino Ratio, Portfolio Beta, and Concentration Index."""

    def calculate_portfolio_metrics(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not holdings:
            return {
                "xirr_percentage": 0.0,
                "portfolio_beta": 1.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "herfindahl_index": 0.0,
                "weighted_pe": 0.0,
                "weighted_roe": 0.0
            }

        total_invested = sum(h.get("quantity", 0) * h.get("average_price", 0) for h in holdings)
        total_current = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in holdings)
        total_pnl = total_current - total_invested
        overall_return_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

        # Estimated XIRR calculation (Assuming average holding period ~1.2 years)
        xirr = self._estimate_xirr(total_invested, total_current, holding_years=1.2)

        # Weighted Fundamental Multiples
        weighted_pe = 0.0
        weighted_roe = 0.0
        portfolio_beta = 0.0
        hhi_concentration = 0.0  # Herfindahl-Hirschman Index (Concentration measure)

        for h in holdings:
            val = h.get("quantity", 0) * h.get("last_price", 0)
            weight = (val / total_current) if total_current > 0 else 0.0
            
            pe = h.get("pe_ratio", 20.0)
            roe = h.get("roe", 15.0)
            beta = self._infer_stock_beta(h.get("tradingsymbol", ""), h.get("sector", ""))

            weighted_pe += weight * pe
            weighted_roe += weight * roe
            portfolio_beta += weight * beta
            hhi_concentration += (weight * 100) ** 2  # Square of weight percentage

        # Risk-Adjusted Return Metrics
        ann_return = (xirr / 100.0)
        est_volatility = max(0.12 * portfolio_beta, 0.08)  # Estimated portfolio volatility based on Beta
        
        sharpe = (ann_return - RISK_FREE_RATE) / est_volatility if est_volatility > 0 else 0.0
        
        downside_deviation = est_volatility * 0.7  # Downside risk estimate
        sortino = (ann_return - RISK_FREE_RATE) / downside_deviation if downside_deviation > 0 else 0.0

        return {
            "xirr_percentage": round(xirr, 2),
            "overall_return_percentage": round(overall_return_pct, 2),
            "portfolio_beta": round(portfolio_beta, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "herfindahl_index": round(hhi_concentration, 0),
            "weighted_pe": round(weighted_pe, 2),
            "weighted_roe": round(weighted_roe, 2),
            "risk_profile_tag": self._categorize_risk_profile(portfolio_beta, hhi_concentration)
        }

    def _estimate_xirr(self, invested: float, current: float, holding_years: float = 1.2) -> float:
        """Solves annualized CAGR / XIRR equation (current / invested) ** (1 / years) - 1."""
        if invested <= 0 or current <= 0:
            return 0.0
        try:
            ratio = current / invested
            annualized_rate = (math.pow(ratio, (1.0 / holding_years)) - 1.0) * 100
            return annualized_rate
        except Exception:
            return 0.0

    def _infer_stock_beta(self, symbol: str, sector: str) -> float:
        """Infers stock volatility Beta relative to Nifty 50 benchmark."""
        beta_map = {
            "RELIANCE": 0.95,
            "TCS": 0.78,
            "INFY": 0.85,
            "HDFCBANK": 0.92,
            "ICICIBANK": 1.05,
            "SBIN": 1.15,
            "TATAMOTORS": 1.35,
            "SUNPHARMA": 0.65,
            "LTIM": 1.20,
            "LT": 1.10
        }
        if symbol.upper() in beta_map:
            return beta_map[symbol.upper()]
        
        # Default beta by sector
        if "Technology" in sector:
            return 0.90
        elif "Financial" in sector:
            return 1.10
        elif "Pharma" in sector or "Healthcare" in sector:
            return 0.70
        elif "Automotive" in sector or "Metals" in sector:
            return 1.25
        return 1.00

    def _categorize_risk_profile(self, beta: float, hhi: float) -> str:
        if beta > 1.20 or hhi > 2500:
            return "High Risk / Aggressive Growth"
        elif beta < 0.85 and hhi < 1500:
            return "Low Volatility / Defensive"
        return "Moderate Risk / Balanced Growth"

analytics_engine = QuantitativeAnalyticsEngine()
