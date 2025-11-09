import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { 
  calculateBalanceTransfer, 
  fetchOverview, 
  fetchSignals, 
  fetchTransactions,
  fetchCreditOffers,
  trackModuleInteraction,
  type BalanceTransferCalculation
} from "@/lib/api"
import { CreditCard, DollarSign, ArrowRight, AlertCircle, CheckCircle } from "lucide-react"
import confetti from "canvas-confetti"

interface BalanceTransferModuleProps {
  userId: string
}

interface CreditAccount {
  account_id: string
  account_mask: string
  balance: number
  credit_limit: number
  utilization: number
  interest_charged?: number
}

export function BalanceTransferModule({ userId }: BalanceTransferModuleProps) {
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [creditAccounts, setCreditAccounts] = useState<CreditAccount[]>([])
  const [totalBalance, setTotalBalance] = useState(0)
  const [accountCount, setAccountCount] = useState(0)
  const [monthlyInterest, setMonthlyInterest] = useState(0)
  const [comparisonMerchant, setComparisonMerchant] = useState<string | null>(null)
  const [comparisonCount, setComparisonCount] = useState(0)
  
  const [additionalPayment, setAdditionalPayment] = useState(0)
  const [calculation, setCalculation] = useState<BalanceTransferCalculation | null>(null)
  const [calculating, setCalculating] = useState(false)

  useEffect(() => {
    loadData()
  }, [userId])

  async function loadData() {
    try {
      setLoading(true)
      const [overview, signals, transactions] = await Promise.all([
        fetchOverview(userId),
        fetchSignals(userId),
        fetchTransactions(userId, undefined, 10)
      ])

      const creditAccountsData = overview.data.accounts.credit
      const total = creditAccountsData.reduce((sum, acc) => sum + acc.balance, 0)
      setTotalBalance(total)
      setAccountCount(creditAccountsData.length)

      // Get credit signals with account details
      const creditSignal = signals.credit_utilization
      const accountsWithSignals = creditAccountsData.map(acc => {
        const signalAccount = creditSignal?.accounts?.find((a: any) => 
          a.account_id === acc.account_id
        )
        return {
          account_id: acc.account_id,
          account_mask: acc.mask || acc.account_id.slice(-4),
          balance: acc.balance,
          credit_limit: (acc as any).limit || acc.limit || 0,
          utilization: signalAccount?.utilization || (acc.balance / ((acc as any).limit || acc.limit || 1)),
          interest_charged: (signalAccount as any)?.interest_charged || 0
        }
      })
      setCreditAccounts(accountsWithSignals)

      const interest = (creditSignal as any)?.interest_charged || 0
      setMonthlyInterest(interest)

      // Find a recent transaction for comparison
      const recentTxn = transactions.find(t => t.amount < 0 && Math.abs(t.amount) > 0)
      if (recentTxn) {
        setComparisonMerchant(recentTxn.merchant_name || "coffee")
        const txnAmount = Math.abs(recentTxn.amount)
        if (interest > 0 && txnAmount > 0) {
          setComparisonCount(Math.round(interest / txnAmount))
        }
      }

      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data")
      setLoading(false)
    }
  }

  async function handleCalculate() {
    try {
      setCalculating(true)
      const result = await calculateBalanceTransfer(userId, {
        balance_transfer_amount: totalBalance,
        transfer_fee_percent: 5.0,
        apr_percent: 0.0,
        additional_monthly_payment: additionalPayment
      })
      setCalculation(result)
      setStep(4)
      
      // Track the interaction
      try {
        await trackModuleInteraction(
          userId,
          'balance_transfer',
          {
            balance_transfer_amount: totalBalance,
            additional_monthly_payment: additionalPayment,
            account_count: accountCount
          },
          result,
          true
        )
      } catch (trackError) {
        console.error('Failed to track module interaction:', trackError)
        // Don't fail the whole operation if tracking fails
      }
      
      // Trigger confetti animation
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 }
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to calculate")
    } finally {
      setCalculating(false)
    }
  }

  async function handleViewOffers() {
    try {
      await fetchCreditOffers(userId)
      // Navigate to offers page or show offers modal
      window.location.href = `/${userId}/offers`
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load offers")
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">Loading your credit information...</div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Error: {error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-6 w-6" />
          Balance Transfer Calculator
        </CardTitle>
        <CardDescription>
          See how much you could save by transferring your balance
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Step 0: Account Breakdown */}
        {step === 0 && (
          <div className="space-y-4">
            <div className="text-lg font-semibold">
              Your credit card accounts:
            </div>
            
            {/* Individual Account Cards */}
            <div className="space-y-3">
              {creditAccounts.map((account) => (
                <div key={account.account_id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <CreditCard className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">Card ending in {account.account_mask}</span>
                    </div>
                    <Badge variant={account.utilization > 0.5 ? "destructive" : account.utilization > 0.3 ? "default" : "secondary"}>
                      {(account.utilization * 100).toFixed(0)}% used
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Balance:</span>
                      <span className="ml-2 font-semibold">${account.balance.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Limit:</span>
                      <span className="ml-2">${account.credit_limit.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}</span>
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          account.utilization > 0.5 ? 'bg-red-600' : 
                          account.utilization > 0.3 ? 'bg-yellow-600' : 
                          'bg-green-600'
                        }`}
                        style={{ width: `${Math.min(100, account.utilization * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-primary/10 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="font-semibold">Total Balance:</span>
                <span className="text-xl font-bold">${totalBalance.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}</span>
              </div>
            </div>
            
            <Button onClick={() => setStep(1)} className="w-full">
              Continue <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Step 1: Monthly Interest */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="text-lg font-semibold">
              You're currently paying ${monthlyInterest.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              })}/month in interest.
            </div>
            {comparisonMerchant && comparisonCount > 0 && (
              <div className="text-muted-foreground">
                That's like {comparisonCount} {comparisonMerchant} {comparisonCount === 1 ? 'purchase' : 'purchases'} per month!
              </div>
            )}
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(0)}>Back</Button>
              <Button onClick={() => setStep(2)} className="flex-1">
                Continue <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Balance Transfer Info */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="text-lg font-semibold">
              If you transfer to a 0% APR card with a 5% balance transfer fee...
            </div>
            <div className="text-muted-foreground">
              Balance transfer fee: ${(totalBalance * 0.05).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              })}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
              <Button onClick={() => setStep(3)} className="flex-1">
                See Calculator <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Payment Input */}
        {step === 3 && (
          <div className="space-y-4">
            <div className="text-lg font-semibold">
              How much additional would you pay each month?
            </div>
            <div className="space-y-2">
              <label htmlFor="additional-payment" className="text-sm font-medium">
                Additional Monthly Payment
              </label>
              <div className="flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="additional-payment"
                  type="number"
                  min="0"
                  step="10"
                  value={additionalPayment}
                  onChange={(e) => setAdditionalPayment(Number(e.target.value) || 0)}
                  placeholder="0"
                />
              </div>
              <div className="text-sm text-muted-foreground">
                Current minimum payment: ${(totalBalance * 0.02).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(2)}>Back</Button>
              <Button 
                onClick={handleCalculate} 
                disabled={calculating}
                className="flex-1"
              >
                {calculating ? "Calculating..." : "Calculate Savings"}
              </Button>
            </div>
          </div>
        )}

        {/* Step 4: Results with comparison */}
        {step === 4 && calculation && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <CheckCircle className="h-8 w-8 text-green-600" />
                <div className="text-2xl font-bold text-green-600">
                  You'll save ${calculation.total_savings.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })}!
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                After paying the ${calculation.transfer_fee.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })} transfer fee
              </p>
            </div>

            {/* Side-by-side comparison */}
            <div className="grid grid-cols-2 gap-4">
              <div className="border rounded-lg p-4 bg-red-50">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <span className="font-semibold text-sm">Current Card</span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Interest:</span>
                    <span className="font-semibold text-red-600">
                      ${calculation.total_interest_current.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Payoff Time:</span>
                    <span className="font-semibold">{calculation.payoff_months_current || 'N/A'} months</span>
                  </div>
                </div>
              </div>

              <div className="border rounded-lg p-4 bg-green-50">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="font-semibold text-sm">Balance Transfer</span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Interest:</span>
                    <span className="font-semibold text-green-600">
                      ${calculation.total_interest_new.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Payoff Time:</span>
                    <span className="font-semibold">{calculation.payoff_months} months</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Progress bar for payoff timeline */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium">Payoff Timeline</span>
                <span className="text-muted-foreground">{calculation.payoff_months} months</span>
              </div>
              <div className="w-full bg-muted rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-green-600 to-green-400 h-3 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, (calculation.payoff_months / 18) * 100)}%`
                  }}
                />
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Now</span>
                <span>18 months (0% APR period)</span>
              </div>
            </div>

            <div className="bg-muted p-4 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span>Monthly Payment Needed:</span>
                <span className="font-semibold">${calculation.monthly_payment_needed.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}</span>
              </div>
              <div className="flex justify-between">
                <span>Monthly Interest Savings:</span>
                <span className="font-semibold text-green-600">${calculation.monthly_savings.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}</span>
              </div>
            </div>
            
            <Button onClick={handleViewOffers} className="w-full">
              See 0% APR Balance Transfer Offers
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

