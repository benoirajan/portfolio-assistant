import logging
import time
import requests
from typing import Dict, List, Any, Optional
from src.core.config import settings

logger = logging.getLogger("market_data")

# TTL cache: {symbol: (data, expiry_timestamp)}
_FUNDAMENTALS_CACHE: Dict[str, tuple] = {}
_CACHE_TTL_SECONDS = 86400  # 24 hours

# Static fallback metadata for common Indian equities
STOCK_METADATA_DB = {
    "RELIANCE":   {"sector": "Energy & Petrochemicals",       "cap_category": "Large Cap", "pe_ratio": 26.5, "pb_ratio": 2.4,  "roe": 9.5,  "sma_200": 2850.0, "div_yield": 0.35},
    "TCS":        {"sector": "Information Technology",         "cap_category": "Large Cap", "pe_ratio": 32.1, "pb_ratio": 13.2, "roe": 48.0, "sma_200": 3950.0, "div_yield": 1.20},
    "HDFCBANK":   {"sector": "Financial Services",             "cap_category": "Large Cap", "pe_ratio": 18.4, "pb_ratio": 2.7,  "roe": 16.2, "sma_200": 1590.0, "div_yield": 1.10},
    "INFY":       {"sector": "Information Technology",         "cap_category": "Large Cap", "pe_ratio": 28.3, "pb_ratio": 8.1,  "roe": 31.5, "sma_200": 1680.0, "div_yield": 2.10},
    "TATAMOTORS": {"sector": "Automotive",                     "cap_category": "Large Cap", "pe_ratio": 10.2, "pb_ratio": 3.1,  "roe": 22.4, "sma_200": 940.0,  "div_yield": 0.60},
    "LTIM":       {"sector": "Information Technology",         "cap_category": "Mid Cap",   "pe_ratio": 34.5, "pb_ratio": 8.9,  "roe": 26.1, "sma_200": 5300.0, "div_yield": 1.30},
    "SUNPHARMA":  {"sector": "Healthcare & Pharma",            "cap_category": "Large Cap", "pe_ratio": 38.2, "pb_ratio": 5.4,  "roe": 16.8, "sma_200": 1580.0, "div_yield": 0.75},
    "ICICIBANK":  {"sector": "Financial Services",             "cap_category": "Large Cap", "pe_ratio": 17.8, "pb_ratio": 3.0,  "roe": 18.5, "sma_200": 1120.0, "div_yield": 0.90},
    "SBIN":       {"sector": "Financial Services",             "cap_category": "Large Cap", "pe_ratio": 10.5, "pb_ratio": 1.5,  "roe": 17.2, "sma_200": 780.0,  "div_yield": 1.80},
    "BHARTIARTL": {"sector": "Telecommunication",              "cap_category": "Large Cap", "pe_ratio": 42.0, "pb_ratio": 7.2,  "roe": 14.5, "sma_200": 1350.0, "div_yield": 0.50},
    "ITC":        {"sector": "Consumer Goods (FMCG)",          "cap_category": "Large Cap", "pe_ratio": 27.4, "pb_ratio": 7.8,  "roe": 29.2, "sma_200": 440.0,  "div_yield": 3.20},
    "LT":         {"sector": "Capital Goods & Infrastructure", "cap_category": "Large Cap", "pe_ratio": 31.0, "pb_ratio": 4.8,  "roe": 15.6, "sma_200": 3550.0, "div_yield": 0.85},
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
        self._nse = None

    def _get_yfinance(self):
        if self._yf is None:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                logger.warning("yfinance not installed.")
        return self._yf

    def _get_nsepython(self):
        if self._nse is None:
            try:
                import nsepython as nse
                self._nse = nse
            except ImportError:
                logger.warning("nsepython not installed.")
        return self._nse

    # ------------------------------------------------------------------
    # Primary provider: nsepython (NSE-native, no API key required)
    # ------------------------------------------------------------------
    def _fetch_nsepython(self, symbol: str) -> Optional[Dict[str, Any]]:
        nse = self._get_nsepython()
        if not nse:
            return None
        try:
            quote = nse.nse_eq(symbol)
            info  = quote.get("priceInfo", {})
            meta  = quote.get("metadata", {})
            ind   = quote.get("industryInfo", {})
            market_cap = float(meta.get("pdSectorPe", 0) or 0)  # used for cap inference via sector PE

            pe  = float(info.get("pdSymbolPe", 0) or 0)
            sma = float(info.get("priceBand", {}).get("lowerPrice", 0) or 0)  # best available proxy
            sector = ind.get("sector", "") or self._infer_sector(symbol)

            if pe == 0:
                return None  # incomplete data — fall through to next provider

            return {
                "symbol":       symbol,
                "sector":       sector,
                "cap_category": self._sebi_cap_category(meta.get("pdSectorInd", "")),
                "pe_ratio":     round(pe, 2),
                "pb_ratio":     0.0,   # not available in basic NSE quote
                "roe":          0.0,   # not available in basic NSE quote
                "div_yield":    0.0,
                "sma_200":      sma,
            }
        except Exception as e:
            logger.warning(f"nsepython fetch failed for {symbol}: {e}")
            return None

    # ------------------------------------------------------------------
    # Secondary provider: yfinance with .NS suffix
    # ------------------------------------------------------------------
    def _fetch_yfinance(self, symbol: str) -> Optional[Dict[str, Any]]:
        yf = self._get_yfinance()
        if not yf:
            return None
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info
            if not info or "trailingPE" not in info:
                return None
            return {
                "symbol":       symbol,
                "sector":       info.get("sector") or self._infer_sector(symbol),
                "cap_category": self._infer_cap_category(info.get("marketCap", 0) or 0),
                "pe_ratio":     round(float(info.get("trailingPE", 0) or 0), 2),
                "pb_ratio":     round(float(info.get("priceToBook", 0) or 0), 2),
                "roe":          round((float(info.get("returnOnEquity", 0) or 0)) * 100, 2),
                "div_yield":    round((float(info.get("dividendYield", 0) or 0)) * 100, 2),
                "sma_200":      round(float(info.get("twoHundredDayAverage", 0) or 0), 2),
            }
        except Exception as e:
            logger.warning(f"yfinance fallback failed for {symbol}: {e}")
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_stock_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        clean = symbol.upper().replace(".NS", "").replace(".BO", "")

        # 1. TTL cache hit
        cached = _FUNDAMENTALS_CACHE.get(clean)
        if cached and time.time() < cached[1]:
            return cached[0]

        # 2. Primary: nsepython (NSE-native)
        data = self._fetch_nsepython(clean)

        # 3. Secondary: yfinance with .NS suffix
        if not data:
            data = self._fetch_yfinance(clean)

        # 4. Static metadata DB
        if not data and clean in STOCK_METADATA_DB:
            data = {**STOCK_METADATA_DB[clean], "symbol": clean}

        # 5. Generic defaults
        if not data:
            data = {
                "symbol": clean, "sector": self._infer_sector(clean),
                "cap_category": "Equity", "pe_ratio": 22.5, "pb_ratio": 3.2,
                "roe": 15.0, "div_yield": 1.0, "sma_200": 0.0,
            }

        _FUNDAMENTALS_CACHE[clean] = (data, time.time() + _CACHE_TTL_SECONDS)
        return data

    def enrich_holdings_with_fundamentals(self, holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        enriched = []
        for item in holdings:
            fund = self.get_stock_fundamental_data(item.get("tradingsymbol", ""))
            h = item.copy()
            h["sector"]       = fund.get("sector", h.get("sector", "Diversified"))
            h["cap_category"] = fund.get("cap_category", h.get("cap_category", "Large Cap"))
            h["pe_ratio"]     = fund.get("pe_ratio", 0.0)
            h["pb_ratio"]     = fund.get("pb_ratio", 0.0)
            h["roe"]          = fund.get("roe", 0.0)
            h["div_yield"]    = fund.get("div_yield", 0.0)
            h["sma_200"]      = fund.get("sma_200", 0.0)
            ltp, sma = h.get("last_price", 0.0), h.get("sma_200", 0.0)
            h["trend_200_sma"] = ("Bullish (Above SMA)" if ltp >= sma else "Bearish (Below SMA)") if sma > 0 else "Neutral"
            enriched.append(h)
        return enriched

    def _infer_sector(self, symbol: str) -> str:
        return SECTOR_MAP.get(symbol.upper(), "Diversified / Others")

    def _sebi_cap_category(self, sector_ind: str) -> str:
        """Maps NSE sector index name to SEBI-defined cap category."""
        s = sector_ind.upper()
        if any(x in s for x in ["NIFTY 50", "NIFTY100", "LARGE"]):
            return "Large Cap"
        if any(x in s for x in ["MIDCAP", "NIFTY 150", "MID"]):
            return "Mid Cap"
        if any(x in s for x in ["SMALLCAP", "SMALL"]):
            return "Small Cap"
        return "Large Cap"  # default for unclassified NSE stocks

    def _infer_cap_category(self, market_cap: float) -> str:
        """Fallback cap classification by market cap value (INR)."""
        if market_cap >= 200_000_000_000:   # ₹20,000 Cr+
            return "Large Cap"
        elif market_cap >= 50_000_000_000:  # ₹5,000 Cr - ₹20,000 Cr
            return "Mid Cap"
        return "Small Cap"


market_data_service = MarketDataService()
