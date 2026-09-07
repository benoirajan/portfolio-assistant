"""
Deterministic rule engine — evaluates portfolio holdings and returns
rebalancing flags before the LLM advisory step.
"""
from typing import Dict, List, Any


def evaluate_rules(
    holdings: List[Dict[str, Any]],
    max_single_stock_pct: float = 15.0,
    max_sector_pct: float = 25.0,
) -> List[Dict[str, Any]]:
    """
    Returns a list of rule flags, one per triggered rule:
      {symbol, rule, severity, detail}
    """
    if not holdings:
        return []

    total_value = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in holdings)
    if total_value <= 0:
        return []

    flags: List[Dict[str, Any]] = []

    # Aggregate sector values
    sector_values: Dict[str, float] = {}
    for h in holdings:
        val = h.get("quantity", 0) * h.get("last_price", 0)
        sector = h.get("sector", "Diversified / Others")
        sector_values[sector] = sector_values.get(sector, 0.0) + val

    for h in holdings:
        symbol = h.get("tradingsymbol", "")
        val = h.get("quantity", 0) * h.get("last_price", 0)
        weight = (val / total_value) * 100

        # Rule 1: Over-concentration (single stock > threshold)
        if weight > max_single_stock_pct:
            flags.append({
                "symbol": symbol,
                "rule": "OVER_CONCENTRATION",
                "severity": "HIGH",
                "detail": f"{symbol} is {weight:.1f}% of portfolio (limit: {max_single_stock_pct}%). Consider trimming.",
            })

        # Rule 2: Underperformance — below 200-day SMA with negative/zero ROE
        sma = h.get("sma_200", 0.0)
        ltp = h.get("last_price", 0.0)
        roe = h.get("roe", 0.0)
        if sma > 0 and ltp < sma and roe <= 0:
            flags.append({
                "symbol": symbol,
                "rule": "UNDERPERFORMANCE",
                "severity": "MEDIUM",
                "detail": f"{symbol} is trading below 200-day SMA (LTP ₹{ltp:.0f} vs SMA ₹{sma:.0f}) with ROE {roe:.1f}%.",
            })

    # Rule 3: Sector over-concentration
    for sector, sec_val in sector_values.items():
        sec_pct = (sec_val / total_value) * 100
        if sec_pct > max_sector_pct:
            flags.append({
                "symbol": None,
                "rule": "SECTOR_OVERWEIGHT",
                "severity": "MEDIUM",
                "detail": f"Sector '{sector}' is {sec_pct:.1f}% of portfolio (limit: {max_sector_pct}%). Diversify.",
            })

    return flags
