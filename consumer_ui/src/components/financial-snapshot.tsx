import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { formatCurrency } from "@/lib/utils"

export interface FinancialSnapshotProps {
  netWorth: number
  totalSavings: number
  creditDebt: number
  availableCredit: number
}

export function FinancialSnapshot({
  netWorth,
  totalSavings,
  creditDebt,
  availableCredit
}: FinancialSnapshotProps) {
  const stats = [
    { label: "Net Worth", value: netWorth },
    { label: "Total Savings", value: totalSavings },
    { label: "Credit Debt", value: creditDebt },
    { label: "Available Credit", value: availableCredit }
  ]

  return (
    <RetroCard>
      <RetroCardHeader>
        <RetroCardTitle className="text-base">FINANCIAL SNAPSHOT</RetroCardTitle>
      </RetroCardHeader>
      <RetroCardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-6">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="bg-[#f9fafb] border border-retro-border p-4 text-center"
            >
              <div className="text-[11px] text-[#64748b] uppercase tracking-wider mb-2 font-mono">
                {stat.label}
              </div>
              <div className="text-2xl font-bold font-mono text-[#1a1a1a] tabular-nums">
                {formatCurrency(stat.value)}
              </div>
            </div>
          ))}
        </div>
      </RetroCardContent>
    </RetroCard>
  )
}

