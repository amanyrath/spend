import { useState, useEffect } from "react"
import type { Account, Transaction } from "@/lib/api"
import { fetchAccountTransactions } from "@/lib/api"
import { formatCurrency, formatPercentage, cn } from "@/lib/utils"
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogDescription 
} from "@/components/ui/dialog"
import { RetroBadge } from "@/components/ui/retro-badge"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { Loader2, AlertCircle, CreditCard, DollarSign, Calendar, TrendingDown, Receipt } from "lucide-react"

interface AccountDetailPanelProps {
  account: Account | null
  userId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AccountDetailPanel({ account, userId, open, onOpenChange }: AccountDetailPanelProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    if (!open || !account) {
      setTransactions([])
      setError(null)
      return
    }
    
    setLoading(true)
    setError(null)
    
    fetchAccountTransactions(userId, account.account_id)
      .then((txns) => {
        setTransactions(txns)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [open, account, userId])
  
  if (!account) return null
  
  const { type, subtype, balance, mask, name, limit, utilization, liability } = account
  
  // Format date helper
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(date)
  }
  
  // Format transaction amount
  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Math.abs(amount))
  }
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-mono text-xl">
            {name} ****{mask}
          </DialogTitle>
          <DialogDescription className="font-mono text-sm">
            Account details and transaction history
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6 mt-4">
          {/* Account Summary */}
          <RetroCard>
            <RetroCardHeader>
              <RetroCardTitle className="text-base">ACCOUNT DETAILS</RetroCardTitle>
            </RetroCardHeader>
            <RetroCardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-1">
                    Balance
                  </div>
                  <div className="text-2xl font-mono font-bold text-retro-charcoal tabular-nums">
                    {formatCurrency(balance)}
                  </div>
                </div>
                
                {limit && (
                  <div>
                    <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-1">
                      {type === 'credit' ? 'Credit Limit' : 'Original Amount'}
                    </div>
                    <div className="text-2xl font-mono font-bold text-retro-charcoal tabular-nums">
                      {formatCurrency(limit)}
                    </div>
                  </div>
                )}
                
                {type === 'credit' && utilization !== undefined && (
                  <div>
                    <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-1">
                      Utilization
                    </div>
                    <RetroBadge 
                      variant={utilization >= 80 ? 'destructive' : utilization >= 50 ? 'warning' : 'success'}
                      className="text-base"
                    >
                      {formatPercentage(utilization)}
                    </RetroBadge>
                  </div>
                )}
                
                {type === 'credit' && account.available && (
                  <div>
                    <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-1">
                      Available Credit
                    </div>
                    <div className="text-xl font-mono font-bold text-trust-success tabular-nums">
                      {formatCurrency(account.available)}
                    </div>
                  </div>
                )}
              </div>
            </RetroCardContent>
          </RetroCard>
          
          {/* Liability Details - Credit Card */}
          {type === 'credit' && liability && (
            <RetroCard>
              <RetroCardHeader>
                <RetroCardTitle className="text-base">CREDIT CARD DETAILS</RetroCardTitle>
              </RetroCardHeader>
              <RetroCardContent>
                <div className="space-y-3">
                  {liability.apr_percentage && (
                    <div className="flex items-center gap-3">
                      <DollarSign className="h-4 w-4 text-retro-charcoal-light" />
                      <div className="flex-1">
                        <div className="text-xs font-mono text-retro-charcoal-light">APR</div>
                        <div className="text-base font-mono font-semibold text-retro-charcoal">
                          {liability.apr_percentage.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {liability.next_payment_due_date && (
                    <div className="flex items-center gap-3">
                      <Calendar className="h-4 w-4 text-retro-charcoal-light" />
                      <div className="flex-1">
                        <div className="text-xs font-mono text-retro-charcoal-light">Next Payment Due</div>
                        <div className="text-base font-mono font-semibold text-retro-charcoal">
                          {formatDate(liability.next_payment_due_date)}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {liability.minimum_payment_amount && (
                    <div className="flex items-center gap-3">
                      <TrendingDown className="h-4 w-4 text-retro-charcoal-light" />
                      <div className="flex-1">
                        <div className="text-xs font-mono text-retro-charcoal-light">Minimum Payment</div>
                        <div className="text-base font-mono font-semibold text-retro-charcoal">
                          {formatCurrency(liability.minimum_payment_amount)}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {liability.last_statement_balance && (
                    <div className="flex items-center gap-3">
                      <Receipt className="h-4 w-4 text-retro-charcoal-light" />
                      <div className="flex-1">
                        <div className="text-xs font-mono text-retro-charcoal-light">Last Statement</div>
                        <div className="text-base font-mono font-semibold text-retro-charcoal">
                          {formatCurrency(liability.last_statement_balance)}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {liability.is_overdue && (
                    <div className="mt-3 p-3 bg-trust-error-light border border-trust-error rounded">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 text-trust-error" />
                        <span className="text-sm font-mono font-semibold text-trust-error">
                          PAYMENT OVERDUE
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </RetroCardContent>
            </RetroCard>
          )}
          
          {/* Liability Details - Loan */}
          {type === 'loan' && liability && (
            <RetroCard>
              <RetroCardHeader>
                <RetroCardTitle className="text-base">LOAN DETAILS</RetroCardTitle>
              </RetroCardHeader>
              <RetroCardContent>
                <div className="space-y-3">
                  {liability.interest_rate && (
                    <div className="flex items-center gap-3">
                      <DollarSign className="h-4 w-4 text-retro-charcoal-light" />
                      <div className="flex-1">
                        <div className="text-xs font-mono text-retro-charcoal-light">Interest Rate</div>
                        <div className="text-base font-mono font-semibold text-retro-charcoal">
                          {liability.interest_rate.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {liability.next_payment_due_date && (
                    <div className="flex items-center gap-3">
                      <Calendar className="h-4 w-4 text-retro-charcoal-light" />
                      <div className="flex-1">
                        <div className="text-xs font-mono text-retro-charcoal-light">Next Payment Due</div>
                        <div className="text-base font-mono font-semibold text-retro-charcoal">
                          {formatDate(liability.next_payment_due_date)}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {liability.origination_date && (
                    <div className="flex items-center gap-3">
                      <Calendar className="h-4 w-4 text-retro-charcoal-light" />
                      <div className="flex-1">
                        <div className="text-xs font-mono text-retro-charcoal-light">Origination Date</div>
                        <div className="text-base font-mono font-semibold text-retro-charcoal">
                          {formatDate(liability.origination_date)}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {liability.original_principal_balance && (
                    <div className="flex items-center gap-3">
                      <Receipt className="h-4 w-4 text-retro-charcoal-light" />
                      <div className="flex-1">
                        <div className="text-xs font-mono text-retro-charcoal-light">Original Amount</div>
                        <div className="text-base font-mono font-semibold text-retro-charcoal">
                          {formatCurrency(liability.original_principal_balance)}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {liability.property_address && (
                    <div className="flex items-start gap-3">
                      <Receipt className="h-4 w-4 text-retro-charcoal-light mt-1" />
                      <div className="flex-1">
                        <div className="text-xs font-mono text-retro-charcoal-light">Property Address</div>
                        <div className="text-sm font-mono text-retro-charcoal">
                          {liability.property_address}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </RetroCardContent>
            </RetroCard>
          )}
          
          {/* Recent Transactions */}
          <RetroCard>
            <RetroCardHeader>
              <RetroCardTitle className="text-base">RECENT TRANSACTIONS</RetroCardTitle>
            </RetroCardHeader>
            <RetroCardContent>
              {loading && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-retro-charcoal-light" />
                </div>
              )}
              
              {error && (
                <div className="flex items-center gap-2 text-trust-error py-4">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm font-mono">{error}</span>
                </div>
              )}
              
              {!loading && !error && transactions.length === 0 && (
                <div className="text-center py-8 text-retro-charcoal-light font-mono text-sm">
                  No transactions found for this account
                </div>
              )}
              
              {!loading && !error && transactions.length > 0 && (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {transactions.slice(0, 20).map((txn) => {
                    const isDebit = txn.amount < 0
                    return (
                      <div 
                        key={txn.transaction_id}
                        className="flex items-center justify-between py-2 border-b border-retro-border last:border-0"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-mono font-medium text-retro-charcoal truncate">
                            {txn.merchant_name}
                          </div>
                          <div className="text-xs font-mono text-retro-charcoal-light">
                            {formatDate(txn.date)}
                          </div>
                        </div>
                        <div className={cn(
                          "text-base font-mono font-semibold tabular-nums ml-4",
                          isDebit ? "text-red-600" : "text-green-600"
                        )}>
                          {isDebit ? "-" : "+"}
                          {formatAmount(txn.amount)}
                        </div>
                      </div>
                    )
                  })}
                  {transactions.length > 20 && (
                    <div className="text-center pt-2 text-xs font-mono text-retro-charcoal-light">
                      Showing 20 of {transactions.length} transactions
                    </div>
                  )}
                </div>
              )}
            </RetroCardContent>
          </RetroCard>
        </div>
      </DialogContent>
    </Dialog>
  )
}

