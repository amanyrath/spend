import { RetroCard, RetroCardContent } from "@/components/ui/retro-card"
import { RetroBadge } from "@/components/ui/retro-badge"
import type { Account } from "@/lib/api"
import { formatCurrency, formatPercentage } from "@/lib/utils"
import { CreditCard, Wallet, TrendingUp, Home, GraduationCap, Car } from "lucide-react"

interface AccountCardProps {
  account: Account
  onClick?: () => void
}

export function AccountCard({ account, onClick }: AccountCardProps) {
  const { type, subtype, balance, mask, name, limit, utilization, liability } = account
  
  // Get account icon
  const getAccountIcon = () => {
    if (type === 'credit') return CreditCard
    if (type === 'depository') {
      return subtype === 'checking' ? Wallet : TrendingUp
    }
    if (type === 'loan') {
      if (subtype === 'mortgage') return Home
      if (subtype === 'student') return GraduationCap
      if (subtype === 'auto') return Car
    }
    return Wallet
  }
  
  const Icon = getAccountIcon()
  
  // Get key metric based on account type
  const getKeyMetric = () => {
    if (type === 'credit' && liability?.apr_percentage) {
      return {
        label: 'APR',
        value: `${liability.apr_percentage.toFixed(2)}%`,
        variant: 'default' as const
      }
    }
    if (type === 'credit' && utilization !== undefined) {
      return {
        label: 'Utilization',
        value: formatPercentage(utilization),
        variant: (utilization >= 80 ? 'destructive' : utilization >= 50 ? 'warning' : 'success') as const
      }
    }
    if (type === 'loan' && liability?.interest_rate) {
      return {
        label: 'Interest Rate',
        value: `${liability.interest_rate.toFixed(2)}%`,
        variant: 'default' as const
      }
    }
    return null
  }
  
  const keyMetric = getKeyMetric()
  
  // Check if overdue
  const isOverdue = liability?.is_overdue
  
  return (
    <RetroCard 
      className={`cursor-pointer transition-all hover:shadow-md hover:border-retro-charcoal ${isOverdue ? 'border-trust-error' : ''}`}
      onClick={onClick}
    >
      <RetroCardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          {/* Left side: Icon and account info */}
          <div className="flex items-start gap-3 flex-1">
            <div className="p-2 bg-retro-bg-light rounded-md">
              <Icon className="h-5 w-5 text-retro-charcoal" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-mono text-retro-charcoal-light mb-1">
                ****{mask}
              </div>
              <div className="text-sm font-mono font-medium text-retro-charcoal mb-2 truncate">
                {name}
              </div>
              <div className="text-2xl font-mono font-bold text-retro-charcoal tabular-nums">
                {formatCurrency(balance)}
              </div>
              {limit && type === 'credit' && (
                <div className="text-xs font-mono text-retro-charcoal-light mt-1">
                  Limit: {formatCurrency(limit)}
                </div>
              )}
            </div>
          </div>
          
          {/* Right side: Key metric or status */}
          <div className="flex flex-col items-end gap-2">
            {isOverdue && (
              <RetroBadge variant="destructive" className="text-xs">
                OVERDUE
              </RetroBadge>
            )}
            {keyMetric && (
              <div className="text-right">
                <div className="text-xs font-mono text-retro-charcoal-light mb-1 uppercase tracking-wider">
                  {keyMetric.label}
                </div>
                <RetroBadge variant={keyMetric.variant}>
                  {keyMetric.value}
                </RetroBadge>
              </div>
            )}
          </div>
        </div>
        
        {/* Additional info for credit cards */}
        {type === 'credit' && liability?.next_payment_due_date && (
          <div className="mt-3 pt-3 border-t border-retro-border">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-retro-charcoal-light">Next Due</span>
              <span className="text-retro-charcoal font-medium">
                {new Date(liability.next_payment_due_date).toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric' 
                })}
              </span>
            </div>
            {liability.minimum_payment_amount && (
              <div className="flex justify-between text-xs font-mono mt-1">
                <span className="text-retro-charcoal-light">Min Payment</span>
                <span className="text-retro-charcoal font-medium tabular-nums">
                  {formatCurrency(liability.minimum_payment_amount)}
                </span>
              </div>
            )}
          </div>
        )}
        
        {/* Additional info for loans */}
        {type === 'loan' && liability?.next_payment_due_date && (
          <div className="mt-3 pt-3 border-t border-retro-border">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-retro-charcoal-light">Next Payment</span>
              <span className="text-retro-charcoal font-medium">
                {new Date(liability.next_payment_due_date).toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric' 
                })}
              </span>
            </div>
          </div>
        )}
      </RetroCardContent>
    </RetroCard>
  )
}

