import logging
import urllib.parse
import urllib.request
import json
from typing import Dict, List, Any, Optional, Tuple
from src.core.config import settings
from src.core.retry import retry_call

logger = logging.getLogger("portfolio_assistant.zerodha_client")

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

    def _make_enctoken_request(
        self,
        path: str,
        method: str = "GET",
        payload: Optional[Any] = None,
        is_json: bool = True,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Makes HTTP request with enctoken trying both kite.zerodha.com/oms and api.kite.trade endpoints."""
        if not self.enctoken:
            return None, "No enctoken set"

        endpoints = [
            f"https://kite.zerodha.com/oms{path}",
            f"https://api.kite.trade{path}"
        ]

        last_error = None
        for url in endpoints:
            def _do_request(url=url):
                headers = {
                    "Authorization": f"enctoken {self.enctoken}",
                    "Cookie": f"enctoken={self.enctoken}",
                    "X-Kite-Version": "3",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }
                data_bytes = None
                if payload is not None:
                    if is_json:
                        data_bytes = json.dumps(payload).encode("utf-8")
                        headers["Content-Type"] = "application/json"
                    else:
                        data_bytes = urllib.parse.urlencode(payload).encode("utf-8")
                        headers["Content-Type"] = "application/x-www-form-urlencoded"

                req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status in (200, 201):
                        return json.loads(response.read().decode("utf-8"))
                raise RuntimeError(f"Unexpected status from {url}")

            try:
                result = retry_call(
                    _do_request,
                    max_attempts=3,
                    base_delay=1.0,
                    multiplier=2.0,
                    retryable_on=(urllib.error.URLError, TimeoutError, ConnectionError),
                    exclude_on=(urllib.error.HTTPError,),
                )
                if result and result.get("status") == "success":
                    return result, None
                last_error = result.get("message", "Unknown error") if result else "Empty response"
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8") if e.fp else ""
                last_error = f"HTTP {e.code}: {err_body or e.reason}"
                logger.warning("Enctoken request to %s failed (HTTP %d) — not retrying", url, e.code)
            except Exception as e:
                last_error = str(e)
                logger.warning("Enctoken request to %s failed after retries: %s", url, e)

        return None, last_error

    def get_holdings_with_status(self, user_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], bool, Optional[str]]:
        """Returns (holdings_list, is_live_data, error_message).
        
        Priority:
        1. Zerodha Live API (via enctoken or KiteConnect)
        2. Historical holdings from DB (tenant-isolated by user_id or token)
        3. Empty list if unavailable (never returns fabricated/demo holdings)
        """
        last_error = None

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
                last_error = formatted_err

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
                last_error = err_msg

        # 3. Fallback to DB history if live Zerodha sync is unavailable
        try:
            from src.services.portfolio_repository import load_portfolio
            token_key = self.enctoken or (f"user_{user_id}" if user_id else "")
            persisted = load_portfolio(token_key, user_id=user_id)
            if persisted and persisted.get("holdings"):
                logger.info(
                    "Retrieved %d historical holdings from database (user_id=%s)",
                    len(persisted["holdings"]),
                    user_id,
                )
                return persisted["holdings"], False, last_error
        except Exception as db_err:
            logger.warning("Failed to load historical holdings from database: %s", db_err)

        # 4. If neither live Zerodha nor DB history is available, return empty list
        return [], False, last_error

    def get_holdings(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        holdings, _, _ = self.get_holdings_with_status(user_id=user_id)
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

    def get_trades(self) -> List[Dict[str, Any]]:
        """Fetches historical trade book for XIRR cash flow reconstruction."""
        if self.enctoken:
            json_data, err = self._make_enctoken_request("/trades")
            if json_data and json_data.get("status") == "success":
                return json_data.get("data", [])

        if self.access_token and self.kite_client:
            try:
                return self.kite_client.trades()
            except Exception as e:
                logger.error(f"Trades fetch failed: {e}")
        return []

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

    def get_baskets(self) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetches list of existing baskets from Zerodha."""
        if self.enctoken:
            json_data, err = self._make_enctoken_request("/baskets")
            if json_data and json_data.get("status") == "success":
                return json_data.get("data", []), None
            return [], err or "Failed to fetch Zerodha baskets"

        # Fallback/Demo mode
        return [
            {"id": "demo_b1", "name": "Core Long Term Equity", "item_count": 4},
            {"id": "demo_b2", "name": "Tactical Rebalance", "item_count": 2}
        ], None

    def export_to_zerodha_basket(
        self,
        basket_name: str,
        items: List[Dict[str, Any]],
        basket_id: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Creates or updates a basket in Zerodha without executing orders.
        items expected format: [{ "symbol": "RELIANCE", "action": "BUY", "quantity": 10, ... }]
        """
        formatted_orders = []
        for item in items:
            action = item.get("action", "BUY").upper()
            tx_type = "BUY" if action == "BUY" else "SELL"
            formatted_orders.append({
                "exchange": "NSE",
                "tradingsymbol": item.get("symbol"),
                "transaction_type": tx_type,
                "order_type": "MARKET",
                "product": "CNC",
                "quantity": int(item.get("quantity", 1)),
                "price": 0,
            })

        if self.enctoken:
            if basket_id:
                path = f"/baskets/{basket_id}/items"
                json_data, err = self._make_enctoken_request(path, method="POST", payload={"orders": formatted_orders})
                if json_data and json_data.get("status") == "success":
                    return {
                        "basket_id": basket_id,
                        "basket_name": basket_name,
                        "item_count": len(formatted_orders),
                        "kite_url": "https://kite.zerodha.com/orders/baskets"
                    }, None
                return None, err or f"Failed to add items to basket {basket_id}"
            else:
                path = "/baskets"
                payload = {
                    "name": basket_name,
                    "orders": formatted_orders
                }
                json_data, err = self._make_enctoken_request(path, method="POST", payload=payload)
                if json_data and json_data.get("status") == "success":
                    new_id = json_data.get("data", {}).get("id", "new_basket")
                    return {
                        "basket_id": new_id,
                        "basket_name": basket_name,
                        "item_count": len(formatted_orders),
                        "kite_url": "https://kite.zerodha.com/orders/baskets"
                    }, None
                return None, err or "Failed to create basket in Zerodha"

        # Demo mode response
        demo_id = basket_id or f"demo_basket_{abs(hash(basket_name)) % 10000}"
        logger.info("Demo Mode: Simulated creation of Zerodha basket '%s' with %d orders", basket_name, len(formatted_orders))
        return {
            "basket_id": demo_id,
            "basket_name": basket_name,
            "item_count": len(formatted_orders),
            "kite_url": "https://kite.zerodha.com/orders/baskets"
        }, None

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
