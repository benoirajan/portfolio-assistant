"""
Tests for CSV/Excel upload feature (Issue #20).

Covers:
  - FileParserService: column normalization, alias mapping, row validation, derived fields
"""
import os
import sys
import unittest
from pathlib import Path

# Ensure backend/src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.file_parser import FileParserService, FileParserError

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: FileParserService
# ──────────────────────────────────────────────────────────────────────────────

class TestFileParserService(unittest.TestCase):
    """Unit tests for FileParserService.parse_holdings_file()."""

    def setUp(self):
        self.parser = FileParserService()

    # ── Valid CSV ─────────────────────────────────────────────────────────

    def test_parse_valid_csv(self):
        """Standard Zerodha-format CSV parses into correct holdings."""
        file_bytes = (FIXTURES_DIR / "sample_holdings.csv").read_bytes()
        holdings, skipped = self.parser.parse_holdings_file(file_bytes, "holdings.csv")

        self.assertEqual(len(holdings), 5)
        self.assertEqual(len(skipped), 0)

        # Spot-check first holding
        rel = holdings[0]
        self.assertEqual(rel["tradingsymbol"], "RELIANCE")
        self.assertEqual(rel["exchange"], "NSE")
        self.assertEqual(rel["isin"], "INE002A01018")
        self.assertEqual(rel["quantity"], 50)
        self.assertEqual(rel["average_price"], 2450.00)
        self.assertEqual(rel["last_price"], 2980.50)
        self.assertEqual(rel["pnl"], 26525.00)

    # ── Column Alias Normalization ───────────────────────────────────────

    def test_parse_aliased_columns(self):
        """CSV with aliased columns (symbol, qty, avg_price, ltp, exch) maps correctly."""
        file_bytes = (FIXTURES_DIR / "aliased_holdings.csv").read_bytes()
        holdings, skipped = self.parser.parse_holdings_file(file_bytes, "export.csv")

        self.assertEqual(len(holdings), 3)
        self.assertEqual(len(skipped), 0)

        # Verify alias resolution
        self.assertEqual(holdings[0]["tradingsymbol"], "RELIANCE")
        self.assertEqual(holdings[0]["quantity"], 50)
        self.assertEqual(holdings[0]["average_price"], 2450.00)
        self.assertEqual(holdings[0]["last_price"], 2980.50)
        self.assertEqual(holdings[0]["exchange"], "NSE")

        # Verify SBIN row
        sbin = holdings[2]
        self.assertEqual(sbin["tradingsymbol"], "SBIN")
        self.assertEqual(sbin["quantity"], 200)

    # ── Row-Level Validation (skip invalid rows) ─────────────────────────

    def test_skip_invalid_rows(self):
        """Rows with missing symbol, negative qty, or non-numeric price are skipped."""
        file_bytes = (FIXTURES_DIR / "mixed_valid_invalid.csv").read_bytes()
        holdings, skipped = self.parser.parse_holdings_file(file_bytes, "mixed.csv")

        self.assertEqual(len(holdings), 2)  # RELIANCE + TATAMOTORS
        self.assertEqual(len(skipped), 3)  # empty symbol, negative qty, non-numeric price

        valid_symbols = {h["tradingsymbol"] for h in holdings}
        self.assertEqual(valid_symbols, {"RELIANCE", "TATAMOTORS"})

        # Verify skip reasons are informative
        reasons = [s["reason"] for s in skipped]
        self.assertTrue(any("tradingsymbol" in r.lower() for r in reasons))
        self.assertTrue(any("quantity" in r.lower() for r in reasons))
        self.assertTrue(any("average_price" in r.lower() for r in reasons))

    # ── Derived Fields ───────────────────────────────────────────────────

    def test_derived_pnl_when_missing(self):
        """PnL is computed as (last_price - average_price) * quantity when not in CSV."""
        csv_content = b"tradingsymbol,quantity,average_price,last_price\nRELIANCE,10,100.00,120.00\n"
        holdings, skipped = self.parser.parse_holdings_file(csv_content, "test.csv")

        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]["pnl"], 200.00)  # (120 - 100) * 10
        self.assertEqual(holdings[0]["pnl_percentage"], 20.00)  # ((120 - 100) / 100) * 100

    def test_default_last_price_to_average_price(self):
        """When last_price is missing, it defaults to average_price."""
        csv_content = b"tradingsymbol,quantity,average_price\nTCS,5,3800.00\n"
        holdings, skipped = self.parser.parse_holdings_file(csv_content, "test.csv")

        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]["last_price"], 3800.00)  # Same as average_price
        self.assertEqual(holdings[0]["pnl"], 0.0)  # No price difference

    def test_default_exchange_to_nse(self):
        """When exchange column is missing, defaults to NSE."""
        csv_content = b"tradingsymbol,quantity,average_price\nINFY,10,1500.00\n"
        holdings, skipped = self.parser.parse_holdings_file(csv_content, "test.csv")

        self.assertEqual(holdings[0]["exchange"], "NSE")

    # ── Missing Required Columns ─────────────────────────────────────────

    def test_missing_required_columns_raises(self):
        """FileParserError raised when required columns are completely absent."""
        csv_content = b"name_col,price_col\nRELIANCE,2450.00\n"
        with self.assertRaisesRegex(FileParserError, "Missing required columns"):
            self.parser.parse_holdings_file(csv_content, "bad.csv")

    # ── Empty File ───────────────────────────────────────────────────────

    def test_empty_file_raises(self):
        """FileParserError raised for a file with no data rows."""
        csv_content = b""
        with self.assertRaises(FileParserError):
            self.parser.parse_holdings_file(csv_content, "empty.csv")

    # ── File Size Guard ──────────────────────────────────────────────────

    def test_file_size_guard(self):
        """FileParserError raised for files exceeding 5 MB."""
        large_bytes = b"x" * (5 * 1024 * 1024 + 1)
        with self.assertRaisesRegex(FileParserError, "too large"):
            self.parser.parse_holdings_file(large_bytes, "huge.csv")

    # ── Unsupported Extension ────────────────────────────────────────────

    def test_unsupported_extension(self):
        """FileParserError raised for unsupported file types."""
        with self.assertRaisesRegex(FileParserError, "Unsupported file type"):
            self.parser.parse_holdings_file(b"data", "report.pdf")

    # ── XLSX Parsing ─────────────────────────────────────────────────────

    def test_parse_xlsx(self):
        """XLSX files are parsed correctly via openpyxl engine."""
        import pandas as pd
        import io

        # Create a minimal XLSX in memory
        df = pd.DataFrame({
            "tradingsymbol": ["RELIANCE", "TCS"],
            "quantity": [50, 30],
            "average_price": [2450.00, 3800.00],
            "last_price": [2980.50, 4120.00],
            "exchange": ["NSE", "NSE"],
        })
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        xlsx_bytes = buffer.getvalue()

        holdings, skipped = self.parser.parse_holdings_file(xlsx_bytes, "holdings.xlsx")

        self.assertEqual(len(holdings), 2)
        self.assertEqual(len(skipped), 0)
        self.assertEqual(holdings[0]["tradingsymbol"], "RELIANCE")
        self.assertEqual(holdings[1]["tradingsymbol"], "TCS")

    # ── Case-Insensitive Column Matching ─────────────────────────────────

    def test_case_insensitive_columns(self):
        """Columns like 'TradingSymbol', 'QUANTITY' are normalized to lowercase."""
        csv_content = b"TradingSymbol,QUANTITY,Average_Price,Last_Price\nSBIN,100,780.00,810.00\n"
        holdings, skipped = self.parser.parse_holdings_file(csv_content, "upper.csv")

        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]["tradingsymbol"], "SBIN")
        self.assertEqual(holdings[0]["quantity"], 100)

    # ── Whitespace in Column Names ───────────────────────────────────────

    def test_whitespace_in_columns(self):
        """Leading/trailing whitespace in column names is stripped."""
        csv_content = b" tradingsymbol , quantity , average_price \nRELIANCE,50,2450.00\n"
        holdings, skipped = self.parser.parse_holdings_file(csv_content, "spaces.csv")

        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]["tradingsymbol"], "RELIANCE")

    # ── Zerodha Console Export Format ───────────────────────────────────

    def test_parse_zerodha_official_csv_export(self):
        """Zerodha Console export format with 'Instrument', 'Qty.', 'Avg. cost', trailing empty column."""
        csv_content = (
            b'"Instrument","Qty.","Avg. cost","LTP","Invested","Cur. val","P&L","Net chg.","Day chg.",""\n'
            b'"BEL",19,423.34,376.45,8043.4,7152.55,-890.85,-11.08,-0.17,""\n'
            b'"BHARTIARTL",6,1810.93,1875.2,10865.6,11251.2,385.6,3.55,-1.56,""\n'
            b'"ICICIBANK",12,1336.45,1381,16037.4,16572,534.6,3.33,-1.15,""\n'
            b'"INFY",6,1237.52,1130,7425.1,6780,-645.1,-8.69,-2.72,""\n'
            b'"ITC",35,282.67,260.8,9893.6,9128,-765.6,-7.74,-1.02,""\n'
            b'"ONGC",21,269.16,224.7,5652.36,4718.7,-933.66,-16.52,1.13,""\n'
            b'"RELIANCE",9,1374.57,1202,12371.1,10818,-1553.1,-12.55,-0.76,""\n'
            b'"SUNPHARMA",4,1796.05,1745,7184.2,6980,-204.2,-2.84,-0.85,""\n'
            b'"TCS",4,2432.06,2460.9,9728.25,9843.6,115.35,1.19,-0.17,""\n'
        )
        holdings, skipped = self.parser.parse_holdings_file(csv_content, "zerodha_holdings.csv")
        self.assertEqual(len(holdings), 9)
        self.assertEqual(len(skipped), 0)
        symbols = [h["tradingsymbol"] for h in holdings]
        self.assertEqual(symbols, ["BEL", "BHARTIARTL", "ICICIBANK", "INFY", "ITC", "ONGC", "RELIANCE", "SUNPHARMA", "TCS"])
        self.assertEqual(holdings[0]["quantity"], 19)
        self.assertEqual(holdings[0]["average_price"], 423.34)
        self.assertEqual(holdings[0]["last_price"], 376.45)
        self.assertEqual(holdings[0]["pnl"], -890.85)


if __name__ == "__main__":
    unittest.main()

