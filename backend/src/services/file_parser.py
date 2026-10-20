"""
File parser service for CSV/Excel holdings upload.

Parses user-uploaded holdings files (CSV, XLSX), normalizes column names via
an alias map, validates required fields, computes derived values, and returns
a clean list of holding dicts compatible with save_portfolio().
"""
import io
import re
import logging
from typing import Dict, List, Any, Tuple

import pandas as pd

logger = logging.getLogger("portfolio_assistant.file_parser")

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# Maps common CSV column headers from various brokers (Zerodha, Groww, Angel
# One, generic exports) to the internal schema used by UserHolding.
COLUMN_ALIASES: Dict[str, str] = {
    # tradingsymbol
    "symbol": "tradingsymbol",
    "trading_symbol": "tradingsymbol",
    "stock": "tradingsymbol",
    "scrip": "tradingsymbol",
    "instrument": "tradingsymbol",
    "ticker": "tradingsymbol",
    "name": "tradingsymbol",
    "stock_name": "tradingsymbol",
    "stock_symbol": "tradingsymbol",
    "company": "tradingsymbol",
    "company_name": "tradingsymbol",
    "security": "tradingsymbol",
    # exchange
    "exch": "exchange",
    "market": "exchange",
    # quantity
    "qty": "quantity",
    "shares": "quantity",
    "units": "quantity",
    "holding_quantity": "quantity",
    "total_quantity": "quantity",
    "current_qty": "quantity",
    "available_qty": "quantity",
    "net_qty": "quantity",
    "quantities": "quantity",
    # average_price
    "avg_price": "average_price",
    "avg_cost": "average_price",
    "buy_price": "average_price",
    "cost_price": "average_price",
    "purchase_price": "average_price",
    "buy_avg": "average_price",
    "buy_average": "average_price",
    "buy_avg_price": "average_price",
    "avg": "average_price",
    "cost": "average_price",
    "avg_cost_price": "average_price",
    "average_cost": "average_price",
    # last_price
    "ltp": "last_price",
    "current_price": "last_price",
    "market_price": "last_price",
    "cmp": "last_price",
    "close_price": "last_price",
    "closing_price": "last_price",
    "last_traded_price": "last_price",
    # pnl
    "profit": "pnl",
    "p&l": "pnl",
    "p_l": "pnl",
    "pl": "pnl",
    "profit_loss": "pnl",
    "unrealized_pnl": "pnl",
    "unrealised_pnl": "pnl",
    "net_pnl": "pnl",
    "total_pnl": "pnl",
    # isin
    "isin_code": "isin",
}

REQUIRED_COLUMNS = {"tradingsymbol", "quantity", "average_price"}


def normalize_column_name(col: Any) -> str:
    """
    Normalize column headers across brokers:
    - Strip whitespace & parenthesized units e.g. (Rs.), (₹), (Nos), (%)
    - Remove dots (e.g. 'Qty.' -> 'qty', 'Avg. cost' -> 'avg cost')
    - Replace slashes, hyphens, and whitespace with single underscores
    """
    s = str(col).strip()
    s = re.sub(r"\(.*?\)", "", s)
    s = s.replace(".", "")
    s = s.replace("/", "_")
    s = s.lower().strip()
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _clean_number(val: Any) -> Any:
    """Strip currency symbols, commas, and whitespace from numbers."""
    if isinstance(val, str):
        val = val.strip().replace(",", "").replace("₹", "").replace("$", "").replace(" ", "")
    return val


class FileParserError(Exception):
    """Raised when file parsing fails at a structural level."""
    pass


class FileParserService:
    """Parses CSV/XLSX holdings files into validated holding dicts."""

    def parse_holdings_file(
        self, file_bytes: bytes, filename: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parse a holdings file and return (valid_holdings, skipped_rows).

        Args:
            file_bytes: Raw file content.
            filename: Original filename (used for extension detection).

        Returns:
            Tuple of (valid_holdings list, skipped_rows list).

        Raises:
            FileParserError: If the file is too large, has an unsupported
                extension, or contains no recognizable columns.
        """
        # ── Guard: file size ─────────────────────────────────────────────
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise FileParserError(
                f"File too large ({len(file_bytes) / (1024*1024):.1f} MB). "
                f"Maximum size is {MAX_FILE_SIZE_BYTES / (1024*1024):.0f} MB."
            )

        # ── Read into DataFrame ──────────────────────────────────────────
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        try:
            if ext == "csv":
                df = pd.read_csv(io.BytesIO(file_bytes))
            elif ext in ("xlsx", "xls"):
                engine = "openpyxl" if ext == "xlsx" else None
                df = pd.read_excel(io.BytesIO(file_bytes), engine=engine)
            else:
                raise FileParserError(
                    f"Unsupported file type '.{ext}'. Please upload a .csv or .xlsx file."
                )
        except FileParserError:
            raise
        except Exception as e:
            raise FileParserError(f"Failed to read file: {e}") from e

        if df.empty:
            raise FileParserError("The uploaded file contains no data rows.")

        # ── Drop empty / unnamed columns (e.g. trailing commas in CSV) ──
        df = df.loc[:, [c for c in df.columns if not str(c).lower().startswith("unnamed") and str(c).strip() != ""]]

        # ── Normalize column names ───────────────────────────────────────
        df.columns = [normalize_column_name(c) for c in df.columns]
        df.rename(columns=COLUMN_ALIASES, inplace=True)

        # Check that required columns are present after alias resolution
        present = set(df.columns)
        missing = REQUIRED_COLUMNS - present
        if missing:
            raise FileParserError(
                f"Missing required columns: {', '.join(sorted(missing))}. "
                f"Found columns: {', '.join(sorted(present))}"
            )

        logger.info(
            "Parsing file '%s' — %d rows, columns: %s",
            filename, len(df), list(df.columns),
        )

        # ── Row-level validation & conversion ────────────────────────────
        valid_holdings: List[Dict[str, Any]] = []
        skipped_rows: List[Dict[str, Any]] = []

        for idx, row in df.iterrows():
            row_num = int(idx) + 2  # +2 for 1-indexed + header row
            row_dict = row.to_dict()

            # --- tradingsymbol ---
            symbol = row_dict.get("tradingsymbol")
            if pd.isna(symbol) or not str(symbol).strip():
                skipped_rows.append({
                    "row": row_num,
                    "reason": "Missing or empty tradingsymbol",
                    "data": _sanitize_row(row_dict),
                })
                continue
            symbol = str(symbol).strip().upper()

            # --- quantity ---
            try:
                qty_raw = _clean_number(row_dict.get("quantity", 0))
                quantity = int(float(qty_raw))
                if quantity <= 0:
                    raise ValueError("non-positive")
            except (ValueError, TypeError):
                skipped_rows.append({
                    "row": row_num,
                    "reason": f"Invalid quantity: {row_dict.get('quantity')}",
                    "data": _sanitize_row(row_dict),
                })
                continue

            # --- average_price ---
            try:
                avg_raw = _clean_number(row_dict.get("average_price", 0))
                average_price = float(avg_raw)
                if average_price < 0:
                    raise ValueError("negative")
            except (ValueError, TypeError):
                skipped_rows.append({
                    "row": row_num,
                    "reason": f"Invalid average_price: {row_dict.get('average_price')}",
                    "data": _sanitize_row(row_dict),
                })
                continue

            # --- last_price (optional, default to average_price) ---
            last_price = _safe_float(row_dict.get("last_price"), default=average_price)

            # --- exchange (optional, default NSE) ---
            exchange = str(row_dict.get("exchange", "NSE")).strip().upper()
            if not exchange or exchange == "NAN":
                exchange = "NSE"

            # --- isin (optional) ---
            isin = row_dict.get("isin")
            if pd.isna(isin) or not str(isin).strip():
                isin = None
            else:
                isin = str(isin).strip().upper()

            # --- pnl (optional, compute if missing) ---
            pnl = _safe_float(row_dict.get("pnl"))
            if pnl is None:
                pnl = (last_price - average_price) * quantity

            pnl_pct = ((last_price - average_price) / average_price * 100) if average_price > 0 else 0.0

            # --- close_price (optional) ---
            close_price = _safe_float(row_dict.get("close_price"))

            holding = {
                "tradingsymbol": symbol,
                "exchange": exchange,
                "isin": isin,
                "quantity": quantity,
                "average_price": round(average_price, 2),
                "last_price": round(last_price, 2),
                "close_price": round(close_price, 2) if close_price is not None else None,
                "pnl": round(pnl, 2),
                "pnl_percentage": round(pnl_pct, 2),
            }
            valid_holdings.append(holding)

        logger.info(
            "Parsed '%s' — %d valid holdings, %d skipped rows",
            filename, len(valid_holdings), len(skipped_rows),
        )
        return valid_holdings, skipped_rows


def _safe_float(value: Any, default: float | None = None) -> float | None:
    """Convert value to float, returning default if conversion fails or value is NaN."""
    if value is None:
        return default
    try:
        cleaned = _clean_number(value)
        f = float(cleaned)
        if pd.isna(f):
            return default
        return f
    except (ValueError, TypeError):
        return default


def _sanitize_row(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert NaN/NaT values to None for JSON serialization."""
    return {
        k: (None if pd.isna(v) else v)
        for k, v in row_dict.items()
    }


file_parser_service = FileParserService()
