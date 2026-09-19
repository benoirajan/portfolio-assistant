import logging
import time
from typing import Dict, List, Any, Optional
from src.core.config import settings
from src.core.retry import retry

logger = logging.getLogger("portfolio_assistant.market_data")

# TTL cache: {symbol: (data, expiry_timestamp)}
_FUNDAMENTALS_CACHE: Dict[str, tuple] = {}
_CACHE_TTL_SECONDS = 86400  # 24 hours

# Static fallback metadata for common Indian equities
STOCK_METADATA_DB = {
    "RELIANCE":   {"sector": "Energy & Petrochemicals",       "cap_category": "Large Cap", "pe_ratio": 26.5, "pb_ratio": 2.4,  "roe": 9.5,  "sma_200": 2850.0, "div_yield": 0.35, "roce": 11.2, "fcf_yield": 2.8, "debt_to_equity": 0.42, "peg_ratio": 1.8, "forward_pe": 23.5, "promoter_holding_pct": 50.3, "promoter_pledge_pct": 0.0},
    "TCS":        {"sector": "Information Technology",         "cap_category": "Large Cap", "pe_ratio": 32.1, "pb_ratio": 13.2, "roe": 48.0, "sma_200": 3950.0, "div_yield": 1.20, "roce": 54.1, "fcf_yield": 3.4, "debt_to_equity": 0.08, "peg_ratio": 2.1, "forward_pe": 28.4, "promoter_holding_pct": 72.4, "promoter_pledge_pct": 0.0},
    "HDFCBANK":   {"sector": "Financial Services",             "cap_category": "Large Cap", "pe_ratio": 18.4, "pb_ratio": 2.7,  "roe": 16.2, "sma_200": 1590.0, "div_yield": 1.10, "roce": 14.8, "fcf_yield": 1.9, "debt_to_equity": 0.85, "peg_ratio": 1.2, "forward_pe": 16.5, "promoter_holding_pct": 0.0,  "promoter_pledge_pct": 0.0},
    "INFY":       {"sector": "Information Technology",         "cap_category": "Large Cap", "pe_ratio": 28.3, "pb_ratio": 8.1,  "roe": 31.5, "sma_200": 1680.0, "div_yield": 2.10, "roce": 38.2, "fcf_yield": 3.8, "debt_to_equity": 0.09, "peg_ratio": 1.9, "forward_pe": 24.1, "promoter_holding_pct": 14.8, "promoter_pledge_pct": 0.0},
    "TATAMOTORS": {"sector": "Automotive",                     "cap_category": "Large Cap", "pe_ratio": 10.2, "pb_ratio": 3.1,  "roe": 22.4, "sma_200": 940.0,  "div_yield": 0.60, "roce": 18.9, "fcf_yield": 5.2, "debt_to_equity": 0.78, "peg_ratio": 0.6, "forward_pe": 9.8,  "promoter_holding_pct": 46.4, "promoter_pledge_pct": 0.0},
    "LTIM":       {"sector": "Information Technology",         "cap_category": "Mid Cap",   "pe_ratio": 34.5, "pb_ratio": 8.9,  "roe": 26.1, "sma_200": 5300.0, "div_yield": 1.30, "roce": 32.4, "fcf_yield": 2.6, "debt_to_equity": 0.05, "peg_ratio": 2.3, "forward_pe": 29.8, "promoter_holding_pct": 68.6, "promoter_pledge_pct": 0.0},
    "SUNPHARMA":  {"sector": "Healthcare & Pharma",            "cap_category": "Large Cap", "pe_ratio": 38.2, "pb_ratio": 5.4,  "roe": 16.8, "sma_200": 1580.0, "div_yield": 0.75, "roce": 19.5, "fcf_yield": 2.5, "debt_to_equity": 0.12, "peg_ratio": 2.0, "forward_pe": 31.2, "promoter_holding_pct": 54.5, "promoter_pledge_pct": 2.1},
    "ICICIBANK":  {"sector": "Financial Services",             "cap_category": "Large Cap", "pe_ratio": 17.8, "pb_ratio": 3.0,  "roe": 18.5, "sma_200": 1120.0, "div_yield": 0.90, "roce": 16.1, "fcf_yield": 2.1, "debt_to_equity": 0.81, "peg_ratio": 1.1, "forward_pe": 15.6, "promoter_holding_pct": 0.0,  "promoter_pledge_pct": 0.0},
    "SBIN":       {"sector": "Financial Services",             "cap_category": "Large Cap", "pe_ratio": 10.5, "pb_ratio": 1.5,  "roe": 17.2, "sma_200": 780.0,  "div_yield": 1.80, "roce": 12.8, "fcf_yield": 1.5, "debt_to_equity": 1.15, "peg_ratio": 0.7, "forward_pe": 9.2,  "promoter_holding_pct": 57.5, "promoter_pledge_pct": 0.0},
    "BHARTIARTL": {"sector": "Telecommunication",              "cap_category": "Large Cap", "pe_ratio": 42.0, "pb_ratio": 7.2,  "roe": 14.5, "sma_200": 1350.0, "div_yield": 0.50, "roce": 13.9, "fcf_yield": 4.1, "debt_to_equity": 1.45, "peg_ratio": 1.7, "forward_pe": 32.0, "promoter_holding_pct": 53.1, "promoter_pledge_pct": 0.0},
    "ITC":        {"sector": "Consumer Goods (FMCG)",          "cap_category": "Large Cap", "pe_ratio": 27.4, "pb_ratio": 7.8,  "roe": 29.2, "sma_200": 440.0,  "div_yield": 3.20, "roce": 37.8, "fcf_yield": 3.9, "debt_to_equity": 0.01, "peg_ratio": 2.2, "forward_pe": 24.5, "promoter_holding_pct": 0.0,  "promoter_pledge_pct": 0.0},
    "LT":         {"sector": "Capital Goods & Infrastructure", "cap_category": "Large Cap", "pe_ratio": 31.0, "pb_ratio": 4.8,  "roe": 15.6, "sma_200": 3550.0, "div_yield": 0.85, "roce": 17.2, "fcf_yield": 2.3, "debt_to_equity": 1.25, "peg_ratio": 1.8, "forward_pe": 26.0, "promoter_holding_pct": 0.0,  "promoter_pledge_pct": 0.0},
    "BEL":        {"sector": "Capital Goods & Infrastructure", "cap_category": "Large Cap", "pe_ratio": 48.0, "pb_ratio": 12.0, "roe": 26.5, "sma_200": 260.0,  "div_yield": 0.80, "roce": 35.5, "fcf_yield": 1.2, "debt_to_equity": 0.0,  "peg_ratio": 2.5, "forward_pe": 40.0, "promoter_holding_pct": 51.1, "promoter_pledge_pct": 0.0},
    "ONGC":       {"sector": "Energy & Petrochemicals",        "cap_category": "Large Cap", "pe_ratio": 7.5,  "pb_ratio": 1.2,  "roe": 15.5, "sma_200": 275.0,  "div_yield": 4.50, "roce": 16.2, "fcf_yield": 8.5, "debt_to_equity": 0.4,  "peg_ratio": 0.8, "forward_pe": 6.5,  "promoter_holding_pct": 58.9, "promoter_pledge_pct": 0.0},
}

SECTOR_MAP = {
    "RELIANCE": "Energy & Petrochemicals", "TCS": "Information Technology",
    "INFY": "Information Technology", "HDFCBANK": "Financial Services",
    "ICICIBANK": "Financial Services", "SBIN": "Financial Services",
    "TATAMOTORS": "Automotive", "MARUTI": "Automotive",
    "SUNPHARMA": "Healthcare & Pharma", "CIPLA": "Healthcare & Pharma",
    "LT": "Capital Goods & Infrastructure", "ITC": "Consumer Goods (FMCG)",
    "BHARTIARTL": "Telecommunication",
}


class MarketDataService:
    def __init__(self):
        self._yf = None

    def _get_yfinance(self):
        if self._yf is None:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                logger.warning("yfinance not installed.")
        return self._yf

    # ------------------------------------------------------------------
    # Primary provider: yfinance with .NS suffix
    # ------------------------------------------------------------------
    def _fetch_yfinance(self, symbol: str) -> Optional[Dict[str, Any]]:
        yf = self._get_yfinance()
        if not yf:
            return None

        class _SSLError(Exception):
            pass

        try:
            @retry(max_attempts=3, base_delay=2.0, multiplier=2.0,
                   retryable_on=(Exception,), exclude_on=(_SSLError,))
            def _fetch():
                try:
                    return yf.Ticker(f"{symbol}.NS").info
                except Exception as exc:
                    msg = str(exc)
                    if "curl: (60)" in msg or "SSL certificate" in msg or "CertificateVerify" in msg:
                        raise _SSLError(msg) from exc
                    raise
            info = _fetch()
            if not info or "trailingPE" not in info:
                return None
            return {
                "symbol":                symbol,
                "sector":                info.get("sector") or self._infer_sector(symbol),
                "cap_category":          self._infer_cap_category(info.get("marketCap", 0) or 0),
                "pe_ratio":              round(float(info.get("trailingPE", 0) or 0), 2),
                "pb_ratio":              round(float(info.get("priceToBook", 0) or 0), 2),
                "roe":                   round((float(info.get("returnOnEquity", 0) or 0)) * 100, 2),
                "div_yield":             round((float(info.get("dividendYield", 0) or 0)) * 100, 2),
                "sma_200":               round(float(info.get("twoHundredDayAverage", 0) or 0), 2),
                "roce":                  round((float(info.get("returnOnAssets", 0) or 0)) * 100 * 1.5, 2),
                "fcf_yield":             round((float(info.get("freeCashflow", 0) or 0) / (float(info.get("marketCap", 1) or 1))) * 100, 2),
                "debt_to_equity":        round(float(info.get("debtToEquity", 0) or 0) / 100.0, 2),
                "peg_ratio":             round(float(info.get("pegRatio", 0) or 0), 2),
                "forward_pe":            round(float(info.get("forwardPE", 0) or 0), 2),
                "promoter_holding_pct":  round(float(info.get("heldPercentInsiders", 0) or 0) * 100, 2),
                "promoter_pledge_pct":   0.0,
            }
        except Exception as e:
            logger.warning("yfinance fetch failed for %s after retries: %s", symbol, e)
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_live_quote(self, symbol: str) -> Optional[Dict[str, float]]:
        """Fetches live LTP, day_change, day_change_percentage via yfinance. Returns None on failure."""
        yf = self._get_yfinance()
        if not yf:
            return None
        try:
            @retry(max_attempts=2, base_delay=1.0, multiplier=2.0, retryable_on=(Exception,))
            def _fetch():
                info = yf.Ticker(f"{symbol}.NS").fast_info
                ltp = float(info.last_price or 0)
                prev_close = float(info.previous_close or 0)
                if ltp <= 0:
                    return None
                change = round(ltp - prev_close, 2)
                change_pct = round((change / prev_close * 100) if prev_close > 0 else 0.0, 2)
                return {"last_price": round(ltp, 2), "close_price": round(prev_close, 2),
                        "day_change": change, "day_change_percentage": change_pct}
            return _fetch()
        except Exception as e:
            logger.warning("Live quote fetch failed for %s: %s", symbol, e)
            return None

    def get_stock_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        clean = symbol.upper().replace(".NS", "").replace(".BO", "")

        # 1. TTL cache hit
        cached = _FUNDAMENTALS_CACHE.get(clean)
        if cached and time.time() < cached[1]:
            return cached[0]

        # 2. In demo mode, use static DB directly for known symbols
        if settings.DEMO_MODE and clean in STOCK_METADATA_DB:
            data = {**STOCK_METADATA_DB[clean], "symbol": clean}
        else:
            # 3. Primary: yfinance
            data = self._fetch_yfinance(clean)

            # 4. Static metadata DB fallback
            if data and clean in STOCK_METADATA_DB:
                fallback = STOCK_METADATA_DB[clean]
                for k in fallback:
                    if data.get(k) in (0.0, 0, None):
                        data[k] = fallback[k]
            elif not data and clean in STOCK_METADATA_DB:
                data = {**STOCK_METADATA_DB[clean], "symbol": clean}

        # 5. Generic defaults
        if not data:
            data = {
                "symbol": clean, "sector": self._infer_sector(clean),
                "cap_category": "Equity", "pe_ratio": 22.5, "pb_ratio": 3.2,
                "roe": 15.0, "div_yield": 1.0, "sma_200": 0.0,
                "roce": 18.0, "fcf_yield": 2.5, "debt_to_equity": 0.40,
                "peg_ratio": 1.5, "forward_pe": 20.0, "promoter_holding_pct": 50.0,
                "promoter_pledge_pct": 0.0,
            }

        _FUNDAMENTALS_CACHE[clean] = (data, time.time() + _CACHE_TTL_SECONDS)
        return data

    def is_valid_nse_symbol(self, symbol: str) -> bool:
        """Validates ticker symbol against known database or live market ticker info."""
        clean = symbol.upper().replace(".NS", "").replace(".BO", "")
        if clean in STOCK_METADATA_DB or clean in SECTOR_MAP:
            return True
        data = self.get_stock_fundamental_data(clean)
        return data.get("pe_ratio", 0) > 0 or data.get("sma_200", 0) > 0

    def enrich_holdings_with_fundamentals(self, holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        enriched = []
        for item in holdings:
            fund = self.get_stock_fundamental_data(item.get("tradingsymbol", ""))
            h = item.copy()
            h["sector"]               = fund.get("sector", h.get("sector", "Diversified"))
            h["cap_category"]         = fund.get("cap_category", h.get("cap_category", "Large Cap"))
            h["pe_ratio"]             = fund.get("pe_ratio", 0.0)
            h["pb_ratio"]             = fund.get("pb_ratio", 0.0)
            h["roe"]                  = fund.get("roe", 0.0)
            h["div_yield"]            = fund.get("div_yield", 0.0)
            h["sma_200"]              = fund.get("sma_200", 0.0)
            h["roce"]                 = fund.get("roce", 0.0)
            h["fcf_yield"]            = fund.get("fcf_yield", 0.0)
            h["debt_to_equity"]       = fund.get("debt_to_equity", 0.0)
            h["peg_ratio"]            = fund.get("peg_ratio", 0.0)
            h["forward_pe"]           = fund.get("forward_pe", 0.0)
            h["promoter_holding_pct"] = fund.get("promoter_holding_pct", 0.0)
            h["promoter_pledge_pct"]  = fund.get("promoter_pledge_pct", 0.0)
            ltp, sma = h.get("last_price", 0.0), h.get("sma_200", 0.0)
            h["trend_200_sma"]        = ("Bullish (Above SMA)" if ltp >= sma else "Bearish (Below SMA)") if sma > 0 else "Neutral"
            enriched.append(h)
        return enriched

    def _infer_sector(self, symbol: str) -> str:
        return SECTOR_MAP.get(symbol.upper(), "Diversified / Others")

    def _infer_cap_category(self, market_cap: float) -> str:
        if market_cap >= 200_000_000_000:
            return "Large Cap"
        elif market_cap >= 50_000_000_000:
            return "Mid Cap"
        return "Small Cap"


market_data_service = MarketDataService()

