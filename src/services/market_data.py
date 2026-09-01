import logging
import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("market_data")

# Known Indian Market Symbols Metadata (Default fallback cache)
STOCK_METADATA_DB = {
    "RELIANCE": {"sector": "Energy & Petrochemicals", "cap_category": "Large Cap", "pe_ratio": 26.5, "pb_ratio": 2.4, "roe": 9.5, "sma_200": 2850.0, "div_yield": 0.35},
    "TCS": {"sector": "Information Technology", "cap_category": "Large Cap", "pe_ratio": 32.1, "pb_ratio": 13.2, "roe": 48.0, "sma_200": 3950.0, "div_yield": 1.20},
    "HDFCBANK": {"sector": "Financial Services", "cap_category": "Large Cap", "pe_ratio": 18.4, "pb_ratio": 2.7, "roe": 16.2, "sma_200": 1590.0, "div_yield": 1.10},
    "INFY": {"sector": "Information Technology", "cap_category": "Large Cap", "pe_ratio": 28.3, "pb_ratio": 8.1, "roe": 31.5, "sma_200": 1680.0, "div_yield": 2.10},
    "TATAMOTORS": {"sector": "Automotive", "cap_category": "Large Cap", "pe_ratio": 10.2, "pb_ratio": 3.1, "roe": 22.4, "sma_200": 940.0, "div_yield": 0.60},
    "LTIM": {"sector": "Information Technology", "cap_category": "Mid Cap", "pe_ratio": 34.5, "pb_ratio": 8.9, "roe": 26.1, "sma_200": 5300.0, "div_yield": 1.30},
    "SUNPHARMA": {"sector": "Healthcare & Pharma", "cap_category": "Large Cap", "pe_ratio": 38.2, "pb_ratio": 5.4, "roe": 16.8, "sma_200": 1580.0, "div_yield": 0.75},
    "ICICIBANK": {"sector": "Financial Services", "cap_category": "Large Cap", "pe_ratio": 17.8, "pb_ratio": 3.0, "roe": 18.5, "sma_200": 1120.0, "div_yield": 0.90},
    "SBIN": {"sector": "Financial Services", "cap_category": "Large Cap", "pe_ratio": 10.5, "pb_ratio": 1.5, "roe": 17.2, "sma_200": 780.0, "div_yield": 1.80},
    "BHARTIARTL": {"sector": "Telecommunication", "cap_category": "Large Cap", "pe_ratio": 42.0, "pb_ratio": 7.2, "roe": 14.5, "sma_200": 1350.0, "div_yield": 0.50},
    "ITC": {"sector": "Consumer Goods (FMCG)", "cap_category": "Large Cap", "pe_ratio": 27.4, "pb_ratio": 7.8, "roe": 29.2, "sma_200": 440.0, "div_yield": 3.20},
    "LT": {"sector": "Capital Goods & Infrastructure", "cap_category": "Large Cap", "pe_ratio": 31.0, "pb_ratio": 4.8, "roe": 15.6, "sma_200": 3550.0, "div_yield": 0.85}
}

class MarketDataService:
    def __init__(self):
        self.yf = None
        self._init_yfinance()

    def _init_yfinance(self):
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            logger.info("yfinance not installed; using fallback fundamental metadata engine.")
            self.yf = None

    def get_stock_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock fundamentals (P/E, P/B, ROE, 200 SMA) via yfinance or metadata cache."""
        clean_symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
        
        # 1. Try yfinance live fetch if available
        if self.yf:
            try:
                ticker = self.yf.Ticker(f"{clean_symbol}.NS")
                info = ticker.info
                if info and "trailingPE" in info:
                    return {
                        "symbol": clean_symbol,
                        "sector": info.get("sector", self._infer_sector(clean_symbol)),
                        "cap_category": self._infer_cap_category(info.get("marketCap", 0)),
                        "pe_ratio": round(info.get("trailingPE", 0.0), 2),
                        "pb_ratio": round(info.get("priceToBook", 0.0), 2),
                        "roe": round((info.get("returnOnEquity", 0.0) or 0.0) * 100, 2),
                        "div_yield": round((info.get("dividendYield", 0.0) or 0.0) * 100, 2),
                        "sma_200": round(info.get("twoHundredDayAverage", 0.0), 2),
                        "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0.0),
                        "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0.0)
                    }
            except Exception as e:
                logger.warning(f"yfinance fetch failed for {clean_symbol}: {e}")

        # 2. Fallback to predefined fundamental metadata DB
        if clean_symbol in STOCK_METADATA_DB:
            data = STOCK_METADATA_DB[clean_symbol].copy()
            data["symbol"] = clean_symbol
            return data

        # Default generic response for unmapped tickers
        return {
            "symbol": clean_symbol,
            "sector": self._infer_sector(clean_symbol),
            "cap_category": "Equity",
            "pe_ratio": 22.5,
            "pb_ratio": 3.2,
            "roe": 15.0,
            "div_yield": 1.0,
            "sma_200": 0.0
        }

    def enrich_holdings_with_fundamentals(self, holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enriches raw Demat holdings list with fundamental ratios and 200 SMA indicators."""
        enriched = []
        for item in holdings:
            symbol = item.get("tradingsymbol", "")
            fund = self.get_stock_fundamental_data(symbol)
            
            h_copy = item.copy()
            h_copy["sector"] = fund.get("sector", h_copy.get("sector", "Diversified"))
            h_copy["cap_category"] = fund.get("cap_category", h_copy.get("cap_category", "Large Cap"))
            h_copy["pe_ratio"] = fund.get("pe_ratio", 0.0)
            h_copy["pb_ratio"] = fund.get("pb_ratio", 0.0)
            h_copy["roe"] = fund.get("roe", 0.0)
            h_copy["div_yield"] = fund.get("div_yield", 0.0)
            h_copy["sma_200"] = fund.get("sma_200", 0.0)
            
            # Technical trend indicator (Above / Below 200 SMA)
            ltp = h_copy.get("last_price", 0.0)
            sma = h_copy.get("sma_200", 0.0)
            if sma > 0:
                h_copy["trend_200_sma"] = "Bullish (Above SMA)" if ltp >= sma else "Bearish (Below SMA)"
            else:
                h_copy["trend_200_sma"] = "Neutral"

            enriched.append(h_copy)
        return enriched

    def _infer_sector(self, symbol: str) -> str:
        sector_map = {
            "RELIANCE": "Energy & Petrochemicals",
            "TCS": "Information Technology",
            "INFY": "Information Technology",
            "HDFCBANK": "Financial Services",
            "ICICIBANK": "Financial Services",
            "SBIN": "Financial Services",
            "TATAMOTORS": "Automotive",
            "MARUTI": "Automotive",
            "SUNPHARMA": "Healthcare & Pharma",
            "CIPLA": "Healthcare & Pharma",
            "LT": "Capital Goods & Infrastructure",
            "ITC": "Consumer Goods (FMCG)",
            "BHARTIARTL": "Telecommunication"
        }
        return sector_map.get(symbol.upper(), "Diversified / Others")

    def _infer_cap_category(self, market_cap: float) -> str:
        if market_cap >= 200_000_000_000: # ₹20,000 Cr+
            return "Large Cap"
        elif market_cap >= 50_000_000_000: # ₹5,000 Cr - ₹20,000 Cr
            return "Mid Cap"
        return "Small Cap"

market_data_service = MarketDataService()
