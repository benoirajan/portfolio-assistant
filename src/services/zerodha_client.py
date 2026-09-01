import logging
import urllib.parse
import urllib.request
import json
from typing import Dict, List, Any, Optional, Tuple
from src.core.config import settings

logger = logging.getLogger("zerodha_service")

# Sample demo holdings reflecting Indian market equity portfolio
DEMO_HOLDINGS = [
    {
        "tradingsymbol": "RELIANCE",
        "exchange": "NSE",
        "instrument_token": 738561,
        "isin": "INE002A01018",
        "product": "CNC",
        "quantity": 50,
        "average_price": 2450.00,
        "last_price": 2980.50,
        "close_price": 2950.00,
        "pnl": 26525.00,
        "day_change": 30.50,
        "day_change_percentage": 1.03,
        "sector": "Energy & Petrochemicals",
        "cap_category": "Large Cap"
    },
    {
        "tradingsymbol": "TCS",
        "exchange": "NSE",
        "instrument_token": 2953217,
        "isin": "INE467B01029",
        "product": "CNC",
        "quantity": 30,
        "average_price": 3800.00,
        "last_price": 4120.00,
        "close_price": 4150.00,
        "pnl": 9600.00,
        "day_change": -30.00,
        "day_change_percentage": -0.72,
        "sector": "Information Technology",
        "cap_category": "Large Cap"
    },
    {
        "tradingsymbol": "HDFCBANK",
        "exchange": "NSE",
        "instrument_token": 341249,
        "isin": "INE040A01034",
        "product": "CNC",
        "quantity": 100,
        "average_price": 1580.00,
        "last_price": 1640.25,
        "close_price": 1630.00,
        "pnl": 6025.00,
        "day_change": 10.25,
        "day_change_percentage": 0.63,
        "sector": "Financial Services",
        "cap_category": "Large Cap"
    },
    {
        "tradingsymbol": "INFY",
        "exchange": "NSE",
        "instrument_token": 408065,
        "isin": "INE009A01021",
        "product": "CNC",
        "quantity": 60,
        "average_price": 1420.00,
        "last_price": 1810.00,
        "close_price": 1795.00,
        "pnl": 23400.00,
        "day_change": 15.00,
        "day_change_percentage": 0.84,
        "sector": "Information Technology",
        "cap_category": "Large Cap"
    },
    {
        "tradingsymbol": "TATAMOTORS",
        "exchange": "NSE",
        "instrument_token": 884737,
        "isin": "INE155A01022",
        "product": "CNC",
        "quantity": 120,
        "average_price": 620.00,
        "last_price": 1015.00,
        "close_price": 998.00,
        "pnl": 47400.00,
        "day_change": 17.00,
        "day_change_percentage": 1.70,
        "sector": "Automotive",
        "cap_category": "Large Cap"
    },
    {
        "tradingsymbol": "LTIM",
        "exchange": "NSE",
        "instrument_token": 4514305,
        "isin": "INE214T01019",
        "product": "CNC",
        "quantity": 25,
        "average_price": 5400.00,
        "last_price": 5100.00,
        "close_price": 5150.00,
        "pnl": -7500.00,
        "day_change": -50.00,
        "day_change_percentage": -0.97,
        "sector": "Information Technology",
        "cap_category": "Mid Cap"
    },
    {
        "tradingsymbol": "SUNPHARMA",
        "exchange": "NSE",
        "instrument_token": 857857,
        "isin": "INE044A01036",
        "product": "CNC",
        "quantity": 45,
        "average_price": 1150.00,
        "last_price": 1720.00,
        "close_price": 1700.00,
        "pnl": 25650.00,
        "day_change": 20.00,
        "day_change_percentage": 1.18,
        "sector": "Healthcare & Pharma",
        "cap_category": "Large Cap"
    }
]

DEMO_MARGINS = {
    "equity": {
        "enabled": True,
        "net": 145230.50,
        "available": {
            "cash": 120000.00,
            "opening_balance": 145230.50,
            "live_balance": 145230.50,
            "collateral": 25230.50
        },
        "utilised": {
            "debits": 0.0,
            "exposure": 0.0,
            "m2m_unrealised": 0.0,
            "m2m_realised": 0.0,
            "option_premium": 0.0
        }
    }
}

class ZerodhaService:
    def __init__(self):
        self.api_key = settings.KITE_API_KEY
        self.api_secret = settings.KITE_API_SECRET
        self.redirect_url = settings.KITE_REDIRECT_URL
        self.access_token: Optional[str] = None
        self.enctoken: Optional[str] = self.sanitize_token(settings.ZERODHA_ENCTOKEN) if settings.ZERODHA_ENCTOKEN else None
        self.kite_client = None

    def sanitize_token(self, raw_token: str) -> str:
        """Cleans enctoken from extraneous quotes, spaces, or cookie key names."""
        if not raw_token:
            return ""
        cleaned = raw_token.strip().strip('"').strip("'").strip()
        if cleaned.startswith("enctoken="):
            cleaned = cleaned[len("enctoken="):].strip()
        if cleaned.startswith("Authorization:"):
            cleaned = cleaned.replace("Authorization:", "").strip()
        if cleaned.startswith("enctoken "):
            cleaned = cleaned.replace("enctoken ", "").strip()
        return cleaned

    def set_enctoken(self, enctoken: str):
        self.enctoken = self.sanitize_token(enctoken)

    def _init_kite(self):
        if not self.kite_client and self.api_key:
            try:
                from kiteconnect import KiteConnect
                self.kite_client = KiteConnect(api_key=self.api_key)
                if self.access_token:
                    self.kite_client.set_access_token(self.access_token)
            except ImportError:
                logger.warning("kiteconnect package not found.")
                self.kite_client = None

    def get_login_url(self) -> str:
        if settings.DEMO_MODE or not self.api_key:
            return "http://127.0.0.1:8000/api/v1/auth/demo-login"
        self._init_kite()
        if self.kite_client:
            return self.kite_client.login_url()
        return f"https://kite.zerodha.com/connect/login?v=3&api_key={self.api_key}"

    def generate_session(self, request_token: str) -> Dict[str, Any]:
        if settings.DEMO_MODE or not self.api_key or not self.api_secret:
            self.access_token = "demo_access_token_12345"
            return {
                "status": "success",
                "access_token": self.access_token,
                "user_name": "Demo Investor",
                "user_id": "DM1001"
            }
        
        self._init_kite()
        if self.kite_client:
            data = self.kite_client.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data.get("access_token")
            self.kite_client.set_access_token(self.access_token)
            return data
        raise RuntimeError("KiteConnect client not initialized properly.")

    def _make_enctoken_request(self, path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Makes HTTP request with enctoken trying both api.kite.trade and kite.zerodha.com/oms endpoints."""
        if not self.enctoken:
            return None, "No enctoken set"

        endpoints = [
            f"https://api.kite.trade{path}",
            f"https://kite.zerodha.com/oms{path}"
        ]

        last_error = None
        for url in endpoints:
            try:
                req = urllib.request.Request(url)
                req.add_header("Authorization", f"enctoken {self.enctoken}")
                req.add_header("Cookie", f"enctoken={self.enctoken}")
                req.add_header("X-Kite-Version", "3")
                req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        body = response.read().decode('utf-8')
                        return json.loads(body), None
            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8') if e.fp else ""
                last_error = f"HTTP {e.code}: {err_body or e.reason}"
            except Exception as e:
                last_error = str(e)

        return None, last_error

    def get_holdings_with_status(self) -> Tuple[List[Dict[str, Any]], bool, Optional[str]]:
        """Returns (holdings_list, is_live_data, error_message)"""
        # 1. Enctoken Free Live Sync
        if self.enctoken:
            json_data, err_msg = self._make_enctoken_request("/portfolio/holdings")
            if json_data and json_data.get("status") == "success":
                holdings = json_data.get("data", [])
                for item in holdings:
                    if "sector" not in item:
                        item["sector"] = self._infer_sector(item.get("tradingsymbol", ""))
                    if "cap_category" not in item:
                        item["cap_category"] = "Equity"
                return holdings, True, None
            else:
                formatted_err = f"Zerodha Enctoken Error ({err_msg}). Ensure you copied the active 'enctoken' cookie string from kite.zerodha.com."
                logger.error(formatted_err)
                return DEMO_HOLDINGS, False, formatted_err

        # 2. Official KiteConnect Client
        if self.access_token and self.kite_client:
            try:
                raw_holdings = self.kite_client.holdings()
                for item in raw_holdings:
                    if "sector" not in item:
                        item["sector"] = self._infer_sector(item.get("tradingsymbol", ""))
                    if "cap_category" not in item:
                        item["cap_category"] = "Equity"
                return raw_holdings, True, None
            except Exception as e:
                err_msg = f"KiteConnect error: {str(e)}"
                logger.error(err_msg)
                return DEMO_HOLDINGS, False, err_msg

        # 3. Fallback Demo
        return DEMO_HOLDINGS, False, None

    def get_holdings(self) -> List[Dict[str, Any]]:
        holdings, _, _ = self.get_holdings_with_status()
        return holdings

    def get_positions(self) -> Dict[str, Any]:
        if self.enctoken:
            json_data, err = self._make_enctoken_request("/portfolio/positions")
            if json_data and json_data.get("status") == "success":
                return json_data.get("data", {"net": [], "day": []})

        if self.access_token and self.kite_client:
            try:
                return self.kite_client.positions()
            except Exception as e:
                logger.error(f"Positions fetch failed: {e}")
        return {"net": [], "day": []}

    def get_margins(self) -> Dict[str, Any]:
        if self.enctoken:
            json_data, err = self._make_enctoken_request("/user/margins")
            if json_data and json_data.get("status") == "success":
                return json_data.get("data", DEMO_MARGINS)
            # Try /user/margins/equity fallback
            json_data_eq, err_eq = self._make_enctoken_request("/user/margins/equity")
            if json_data_eq and json_data_eq.get("status") == "success":
                return {"equity": json_data_eq.get("data", {})}

        if self.access_token and self.kite_client:
            try:
                return self.kite_client.margins()
            except Exception as e:
                logger.error(f"Margins fetch failed: {e}")
        return DEMO_MARGINS

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
            "LT": "Capital Goods & Construction"
        }
        return sector_map.get(symbol.upper(), "Diversified / Others")

zerodha_service = ZerodhaService()
