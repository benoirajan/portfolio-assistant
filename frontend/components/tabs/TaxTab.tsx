import type { TaxAnalysis } from '@/lib/types'

interface Props { tax: TaxAnalysis }

const LTCG_LIMIT = 125000

export default function TaxTab({ tax }: Props) {
  const exemptionPct = Math.min(1, (tax.ltcg_exemption_used ?? 0) / LTCG_LIMIT)

  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-[var(--muted)]">
        Optimise capital gains tax by harvesting unrealised losses before March 31st.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Net STCG (<1 yr)', value: `₹${tax.net_stcg.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
          { label: 'STCG tax (20%)', value: `₹${tax.stcg_tax_payable.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
          { label: 'Net LTCG (>1 yr)', value: `₹${tax.net_ltcg.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
          { label: 'LTCG tax (12.5%)', value: `₹${tax.ltcg_tax_payable.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
        ].map((c) => (
          <div key={c.label} className="bg-[var(--surface)] border border-[var(--border)] rounded-lg px-4 py-3">
            <p className="text-xs text-[var(--muted)] mb-1">{c.label}</p>
            <p className="text-lg font-semibold">{c.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4">
        <p className="text-sm font-medium mb-2">LTCG annual exemption (₹1.25 lakh limit)</p>
        <div className="w-full bg-[var(--border)] rounded-full h-3">
          <div
            className="h-3 rounded-full transition-all"
            style={{ width: `${exemptionPct * 100}%`, background: exemptionPct >= 1 ? 'var(--red)' : 'var(--blue)' }}
          />
        </div>
        <p className="text-xs text-[var(--muted)] mt-1">
          Used ₹{(tax.ltcg_exemption_used ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })} of ₹1,25,000
        </p>
      </div>

      {tax.harvestable_loss_candidates?.length > 0 ? (
        <div>
          <p className="text-sm font-medium mb-2">Harvestable loss candidates</p>
          <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-[var(--muted)] text-xs">
                  {['Symbol', 'Unrealised loss', 'Holding days', 'Tax type'].map((h) => (
                    <th key={h} className="text-left px-3 py-2">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tax.harvestable_loss_candidates.map((c, i) => (
                  <tr key={`${c.tradingsymbol}-${i}`} className="border-b border-[var(--border)] hover:bg-[var(--bg)]">
                    <td className="px-3 py-2 font-medium">{c.tradingsymbol}</td>
                    <td className="px-3 py-2 text-[var(--red)]">₹{c.unrealized_loss.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                    <td className="px-3 py-2">{c.holding_period_days}</td>
                    <td className="px-3 py-2">{c.tax_type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <p className="text-sm text-[var(--green)]">✓ No tax loss harvesting candidates — portfolio is fully gain-aligned.</p>
      )}
    </div>
  )
}
