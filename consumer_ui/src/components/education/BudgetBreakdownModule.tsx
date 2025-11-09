import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  fetchSignals, 
  fetchInsights,
  fetchBudgetBreakdown,
  type BudgetBreakdown
} from "@/lib/api"
import { TrendingUp, ArrowRight, CheckCircle, AlertTriangle, Info } from "lucide-react"

interface BudgetBreakdownModuleProps {
  userId: string
}

export function BudgetBreakdownModule({ userId }: BudgetBreakdownModuleProps) {
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [incomeMin, setIncomeMin] = useState(0)
  const [incomeMax, setIncomeMax] = useState(0)
  const [incomeAvg, setIncomeAvg] = useState(0)
  const [currentSpending, setCurrentSpending] = useState(0)
  const [budget, setBudget] = useState<BudgetBreakdown | null>(null)
  const [loadingBudget, setLoadingBudget] = useState(false)

  useEffect(() => {
    loadData()
  }, [userId])

  async function loadData() {
    try {
      setLoading(true)
      const [signals, insights] = await Promise.all([
        fetchSignals(userId, "180d"),
        fetchInsights(userId, "30d")
      ])

      const incomeSignal = signals.income_stability
      setIncomeMin(incomeSignal?.income_min || 0)
      setIncomeMax(incomeSignal?.income_max || 0)
      setIncomeAvg(incomeSignal?.avg_monthly_income || 0)

      const totalSpending = insights.data.summary.total_spending
      setCurrentSpending(totalSpending)

      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data")
      setLoading(false)
    }
  }

  async function handleGenerateBudget() {
    try {
      setLoadingBudget(true)
      const result = await fetchBudgetBreakdown(userId)
      setBudget(result)
      setStep(2)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate budget breakdown")
    } finally {
      setLoadingBudget(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">Loading your financial information...</div>
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
          <TrendingUp className="h-6 w-6" />
          Budget Breakdown
        </CardTitle>
        <CardDescription>
          Get a personalized budget recommendation based on your income
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Step 0: Income Overview with variability */}
        {step === 0 && (
          <div className="space-y-4">
            <div className="text-lg font-semibold">
              Your income varies over time
            </div>
            
            {/* Income range visualization */}
            <div className="bg-muted p-4 rounded-lg space-y-3">
              <div className="flex justify-between items-center">
                <div className="text-sm text-muted-foreground">Minimum</div>
                <div className="font-semibold text-red-600">
                  ${incomeMin.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })}
                </div>
              </div>
              
              {/* Visual income range bar */}
              <div className="relative h-8 bg-gradient-to-r from-red-200 via-yellow-200 to-green-200 rounded-full">
                <div 
                  className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-blue-600 rounded-full border-2 border-white"
                  style={{ 
                    left: `${((incomeAvg - incomeMin) / (incomeMax - incomeMin)) * 100}%`,
                    transform: 'translate(-50%, -50%)'
                  }}
                  title="Average"
                />
              </div>
              
              <div className="flex justify-between items-center">
                <div className="text-sm text-muted-foreground">Maximum</div>
                <div className="font-semibold text-green-600">
                  ${incomeMax.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2 p-3 bg-blue-50 border-l-4 border-blue-600 rounded">
              <Info className="h-5 w-5 text-blue-600 flex-shrink-0" />
              <div className="text-sm">
                <span className="font-semibold">Your average income:</span> ${incomeAvg.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}/month
              </div>
            </div>
            
            <Button onClick={() => setStep(1)} className="w-full">
              Continue <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Step 1: Spending Comparison */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="text-lg font-semibold">
              You currently spend ${currentSpending.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              })}/month.
            </div>
            <div className="text-muted-foreground">
              Would you like me to recommend a budget breakdown?
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(0)}>Back</Button>
              <Button 
                onClick={handleGenerateBudget} 
                disabled={loadingBudget}
                className="flex-1"
              >
                {loadingBudget ? "Generating..." : "Generate Budget Breakdown"}
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Budget Breakdown with better visuals */}
        {step === 2 && budget && (
          <div className="space-y-6">
            <div className="space-y-2">
              <div className="text-lg font-semibold">Recommended Budget Breakdown</div>
              <div className="flex items-start gap-2 p-3 bg-muted rounded-lg">
                <Info className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                <div className="text-sm text-muted-foreground">{budget.rationale}</div>
              </div>
            </div>

            {/* Budget Categories with color coding */}
            <div className="space-y-4">
              {/* Essentials */}
              <div className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <div className="font-semibold">Essentials</div>
                    <Badge variant="secondary">{budget.essentials_percent.toFixed(0)}%</Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    ${budget.current_essentials.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })} / ${budget.essentials_target.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })}
                  </div>
                </div>
                <div className="w-full bg-muted rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      budget.current_essentials > budget.essentials_target 
                        ? 'bg-red-600' 
                        : budget.current_essentials > budget.essentials_target * 0.9
                          ? 'bg-yellow-600'
                          : 'bg-blue-600'
                    }`}
                    style={{
                      width: `${Math.min(100, (budget.current_essentials / budget.essentials_target) * 100)}%`
                    }}
                  />
                </div>
                {budget.current_essentials > budget.essentials_target && (
                  <div className="flex items-center gap-1 mt-2 text-xs text-red-600">
                    <AlertTriangle className="h-3 w-3" />
                    <span>Over budget by ${(budget.current_essentials - budget.essentials_target).toFixed(2)}</span>
                  </div>
                )}
              </div>

              {/* Savings */}
              <div className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <div className="font-semibold">Savings</div>
                    <Badge variant="secondary">{budget.savings_percent.toFixed(0)}%</Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Target: ${budget.savings_target.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })}/month
                  </div>
                </div>
                <div className="w-full bg-muted rounded-full h-3">
                  <div
                    className="bg-green-600 h-3 rounded-full transition-all"
                    style={{
                      width: `100%`
                    }}
                  />
                </div>
                <div className="flex items-center gap-1 mt-2 text-xs text-green-600">
                  <CheckCircle className="h-3 w-3" />
                  <span>Build your emergency fund and long-term savings</span>
                </div>
              </div>

              {/* Discretionary */}
              <div className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <div className="font-semibold">Discretionary</div>
                    <Badge variant="secondary">{budget.discretionary_percent.toFixed(0)}%</Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    ${budget.current_discretionary.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })} / ${budget.discretionary_target.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })}
                  </div>
                </div>
                <div className="w-full bg-muted rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      budget.current_discretionary > budget.discretionary_target 
                        ? 'bg-red-600' 
                        : budget.current_discretionary > budget.discretionary_target * 0.9
                          ? 'bg-yellow-600'
                          : 'bg-purple-600'
                    }`}
                    style={{
                      width: `${Math.min(100, (budget.current_discretionary / budget.discretionary_target) * 100)}%`
                    }}
                  />
                </div>
                {budget.current_discretionary > budget.discretionary_target && (
                  <div className="flex items-center gap-1 mt-2 text-xs text-red-600">
                    <AlertTriangle className="h-3 w-3" />
                    <span>Over budget by ${(budget.current_discretionary - budget.discretionary_target).toFixed(2)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Category Details - Expandable */}
            <details className="border rounded-lg">
              <summary className="cursor-pointer p-4 font-semibold hover:bg-muted transition-colors">
                View Category Details ({budget.category_allocations.length} categories)
              </summary>
              <div className="p-4 pt-0 space-y-2 max-h-60 overflow-y-auto">
                {budget.category_allocations.map((cat, index) => (
                  <div 
                    key={index} 
                    className={`flex justify-between items-center text-sm p-3 rounded ${
                      cat.over_budget ? 'bg-red-50' : 'bg-muted'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{cat.category}</span>
                      <Badge variant={cat.type === 'essential' ? 'default' : 'secondary'} className="text-xs">
                        {cat.type}
                      </Badge>
                      {cat.over_budget && (
                        <AlertTriangle className="h-3 w-3 text-red-600" />
                      )}
                    </div>
                    <div className="text-muted-foreground text-right">
                      <div>${cat.current_spending.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })} / ${cat.recommended_max.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}</div>
                    </div>
                  </div>
                ))}
              </div>
            </details>

            {/* Tips for Variable Income */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 border-2 border-purple-600 p-4 rounded-lg">
              <div className="font-semibold mb-2">Tips for Managing Variable Income:</div>
              <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
                <li>Budget based on your minimum expected income</li>
                <li>Build a larger emergency fund (3-6 months)</li>
                <li>Set aside extra income during good months</li>
                <li>Consider percentage-based budgeting for flexibility</li>
              </ul>
            </div>

            <Button onClick={() => setStep(0)} variant="outline" className="w-full">
              Start Over
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

