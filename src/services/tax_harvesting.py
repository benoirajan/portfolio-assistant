import logging
import datetime
from typing import Dict, List, Any

logger = logging.getLogger("tax_harvesting")

STCG_TAX_RATE = 0.20  # 20% Short Term Capital Gains Tax
LTCG_TAX_RATE = 0.125  # 12.5% Long Term Capital Gains Tax
LTCG_EXEMPTION_LIMIT = 125000.0  # ₹1.25 Lakh annual exemption limit

class TaxHarvestingAnalyzer:
    """Analyzes holding periods (STCG vs LTCG), computes estimated capital gains tax liabilities, and flags tax loss harvesting opportunities."""

    def analyze_tax_harvesting(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        stcg_gains = 0.0
        stcg_losses = 0.0
        ltcg_gains = 0.0
        ltcg_losses = 0.0
        
        harvestable_loss_candidates = []

        for h in holdings:
            symbol = h.get("tradingsymbol", "")
            qty = h.get("quantity", 0)
            avg_price = h.get("average_price", 0.0)
            last_price = h.get("last_price", 0.0)
            pnl = h.get("pnl", (last_price - avg_price) * qty)

            # Determine holding age (Default estimate: ~6 months for recent purchases, ~15 months for core delivery)
            # In live Zerodha data, authorised_date / t1_quantity helps infer age
            auth_date_str = h.get("authorised_date", "")
            is_long_term = self._is_long_term(auth_date_str)

            if is_long_term:
                if pnl > 0:
                    ltcg_gains += pnl
                else:
                    ltcg_losses += abs(pnl)
                    harvestable_loss_candidates.append({
                        "symbol": symbol,
                        "holding_type": "LTCG",
                        "unrealized_loss": abs(pnl),
                        "quantity": qty,
                        "last_price": last_price,
                        "recommendation": f"Harvest ₹{abs(pnl):,.2f} loss to offset LTCG tax."
                    })
            else:
                if pnl > 0:
                    stcg_gains += pnl
                else:
                    stcg_losses += abs(pnl)
                    harvestable_loss_candidates.append({
                        "symbol": symbol,
                        "holding_type": "STCG",
                        "unrealized_loss": abs(pnl),
                        "quantity": qty,
                        "last_price": last_price,
                        "recommendation": f"Harvest ₹{abs(pnl):,.2f} loss to offset STCG (20% tax rate)."
                    })

        # Calculate Net Capital Gains
        net_stcg = max(0.0, stcg_gains - stcg_losses)
        net_ltcg = max(0.0, ltcg_gains - ltcg_losses)

        # Estimated Tax Liability
        stcg_tax_payable = net_stcg * STCG_TAX_RATE
        
        taxable_ltcg = max(0.0, net_ltcg - LTCG_EXEMPTION_LIMIT)
        ltcg_tax_payable = taxable_ltcg * LTCG_TAX_RATE

        total_tax_liability = stcg_tax_payable + ltcg_tax_payable
        potential_tax_savings = (stcg_losses * STCG_TAX_RATE) + (ltcg_losses * LTCG_TAX_RATE)

        return {
            "stcg_gains": round(stcg_gains, 2),
            "stcg_losses": round(stcg_losses, 2),
            "net_stcg": round(net_stcg, 2),
            "stcg_tax_payable": round(stcg_tax_payable, 2),
            "ltcg_gains": round(ltcg_gains, 2),
            "ltcg_losses": round(ltcg_losses, 2),
            "net_ltcg": round(net_ltcg, 2),
            "ltcg_exemption_used": round(min(net_ltcg, LTCG_EXEMPTION_LIMIT), 2),
            "ltcg_tax_payable": round(ltcg_tax_payable, 2),
            "total_estimated_tax": round(total_tax_liability, 2),
            "potential_tax_savings": round(potential_tax_savings, 2),
            "harvestable_loss_candidates": harvestable_loss_candidates
        }

    def _is_long_term(self, auth_date_str: str) -> bool:
        if not auth_date_str:
            return True # Default assume core portfolio is LTCG (> 1 year)
        try:
            dt = datetime.datetime.strptime(auth_date_str.split(" ")[0], "%Y-%m-%d")
            return (datetime.datetime.now() - dt).days >= 365
        except Exception:
            return True

tax_harvesting_analyzer = TaxHarvestingAnalyzer()
