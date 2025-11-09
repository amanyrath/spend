import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { 
  fetchOverview, 
  fetchSignals, 
  calculateSavingsGoal,
  type SavingsGoalCalculation
} from "@/lib/api"
import { PiggyBank, TrendingUp, DollarSign, ArrowRight, Sparkles, Target, CheckCircle } from "lucide-react"

interface SavingsGoalModuleProps {
  userId: string
}

export function SavingsGoalModule({ userId }: SavingsGoalModuleProps) {
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [currentSavings, setCurrentSavings] = useState(0)
  const [monthlySavingsRate, setMonthlySavingsRate] = useState(0)
  const [customMonthlyRate, setCustomMonthlyRate] = useState("")
  const [weeklySavingsSlider, setWeeklySavingsSlider] = useState(0)
  const [goalAmount, setGoalAmount] = useState("")
  const [calculation, setCalculation] = useState<SavingsGoalCalculation | null>(null)
  const [calculating, setCalculating] = useState(false)
  const [showHYSAComparison, setShowHYSAComparison] = useState(false)
  
  const HYSA_APY = 4.5 // High-yield savings account APY
  const PRESET_GOALS = [
    { label: "Emergency Fund", amount: 5000 },
    { label: "Vacation", amount: 10000 },
    { label: "Down Payment", amount: 20000 },
    { label: "New Car", amount: 30000 },
  ]

  useEffect(() => {
    loadData()
  }, [userId])

  async function loadData() {
    try {
      setLoading(true)
      const [overview, signals] = await Promise.all([
        fetchOverview(userId),
        fetchSignals(userId)
      ])

      setCurrentSavings(overview.data.summary.total_savings)
      
      const savingsSignal = signals.savings_behavior
      setMonthlySavingsRate(savingsSignal?.avg_monthly_savings || 0)

      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data")
      setLoading(false)
    }
  }

  // Helper function to calculate timeline from weekly savings
  function calculateTimelineFromWeekly(weeklyAmount: number): SavingsGoalCalculation {
    if (!goalAmount) {
      return {
        months_needed: null,
        years_needed: null,
        amount_needed: 0,
        is_achievable: false
      }
    }
    
    const goal = parseFloat(goalAmount)
    
    // Check if user already has enough savings
    if (currentSavings >= goal) {
      return {
        months_needed: 0,
        years_needed: 0,
        amount_needed: 0,
        is_achievable: true
      }
    }
    
    if (weeklyAmount <= 0) {
      return {
        months_needed: null,
        years_needed: null,
        amount_needed: goal - currentSavings,
        is_achievable: false
      }
    }
    
    // Convert weekly to monthly (average of 4.33 weeks per month)
    const monthlyFromWeekly = weeklyAmount * 4.33
    const amountNeeded = goal - currentSavings
    const monthsNeeded = Math.ceil(amountNeeded / monthlyFromWeekly)
    const yearsNeeded = monthsNeeded / 12.0
    
    return {
      months_needed: monthsNeeded,
      years_needed: yearsNeeded,
      amount_needed: amountNeeded,
      is_achievable: true
    }
  }
  
  // Update calculation when slider changes (only in step 2)
  useEffect(() => {
    if (step === 2 && goalAmount && weeklySavingsSlider > 0) {
      const newCalculation = calculateTimelineFromWeekly(weeklySavingsSlider)
      setCalculation(newCalculation)
    }
  }, [weeklySavingsSlider, step, goalAmount, currentSavings])
  
  async function handleCalculate() {
    const goal = parseFloat(goalAmount)
    if (isNaN(goal) || goal <= 0) {
      setError("Please enter a valid goal amount")
      return
    }

    // Check if user already has enough savings
    if (currentSavings >= goal) {
      setCalculation({
        months_needed: 0,
        years_needed: 0,
        amount_needed: 0,
        is_achievable: true
      })
      setStep(1)
      setShowHYSAComparison(true)
      return
    }

    // Use custom monthly rate if provided, otherwise use calculated rate
    const effectiveMonthlyRate = customMonthlyRate ? parseFloat(customMonthlyRate) : monthlySavingsRate
    
    if (effectiveMonthlyRate <= 0) {
      setError("Please enter a monthly savings amount to calculate your timeline")
      return
    }

    try {
      setCalculating(true)
      
      // Calculate on frontend if we have custom rate, otherwise use backend
      if (customMonthlyRate) {
        const amountNeeded = goal - currentSavings
        const monthsNeeded = Math.ceil(amountNeeded / effectiveMonthlyRate)
        const yearsNeeded = monthsNeeded / 12.0
        
        const calc = {
          months_needed: monthsNeeded,
          years_needed: yearsNeeded,
          amount_needed: amountNeeded,
          is_achievable: true
        }
        setCalculation(calc)
        
        // Set initial slider value based on calculated rate
        const weeklyFromMonthly = effectiveMonthlyRate / 4.33
        const initialSliderValue = Math.max(10, Math.round(weeklyFromMonthly / 5) * 5) // Round to nearest 5, minimum 10
        setWeeklySavingsSlider(initialSliderValue)
      } else {
        const result = await calculateSavingsGoal(userId, goal)
        setCalculation(result)
        
        // Set initial slider value based on detected rate
        if (monthlySavingsRate > 0) {
          const weeklyFromMonthly = monthlySavingsRate / 4.33
          const initialSliderValue = Math.max(10, Math.round(weeklyFromMonthly / 5) * 5) // Round to nearest 5, minimum 10
          setWeeklySavingsSlider(initialSliderValue)
        } else {
          // Default to a reasonable starting point
          const suggestedWeekly = Math.max(10, Math.ceil((goal - currentSavings) / 52)) // Suggest saving target/52 weeks
          setWeeklySavingsSlider(Math.min(500, Math.max(10, Math.round(suggestedWeekly / 5) * 5)))
        }
      }
      
      setStep(1)
      setShowHYSAComparison(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to calculate")
    } finally {
      setCalculating(false)
    }
  }
  
  function calculateWithCompoundInterest(principal: number, monthlyDeposit: number, apr: number, months: number): number {
    const monthlyRate = apr / 12 / 100
    let balance = principal
    
    for (let i = 0; i < months; i++) {
      balance = balance * (1 + monthlyRate) + monthlyDeposit
    }
    
    return balance
  }
  
  function getEffectiveMonthlyRate(): number {
    if (weeklySavingsSlider > 0 && step === 2) {
      // Use slider value if we're in step 2
      return weeklySavingsSlider * 4.33
    }
    return customMonthlyRate ? parseFloat(customMonthlyRate) : monthlySavingsRate
  }
  
  function getHYSAComparison() {
    if (!calculation || !calculation.months_needed) return null
    
    const goal = parseFloat(goalAmount)
    const effectiveMonthlyRate = getEffectiveMonthlyRate()
    const regularSavings = currentSavings + (effectiveMonthlyRate * calculation.months_needed)
    const hysaSavings = calculateWithCompoundInterest(currentSavings, effectiveMonthlyRate, HYSA_APY, calculation.months_needed)
    const interestEarned = hysaSavings - regularSavings
    
    // Calculate months saved with HYSA
    let monthsSaved = 0
    if (effectiveMonthlyRate > 0) {
      let balance = currentSavings
      let months = 0
      while (balance < goal && months < 360) { // Cap at 30 years
        balance = balance * (1 + HYSA_APY / 12 / 100) + effectiveMonthlyRate
        months++
      }
      monthsSaved = calculation.months_needed - months
    }
    
    return {
      regularSavings,
      hysaSavings,
      interestEarned,
      monthsSaved: Math.max(0, monthsSaved)
    }
  }

  async function handleViewOffers() {
    try {
      window.location.href = `/${userId}/offers`
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load offers")
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">Loading your savings information...</div>
        </CardContent>
      </Card>
    )
  }

  if (error && step === 0) {
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
          <PiggyBank className="h-6 w-6" />
          Savings Goal Calculator
        </CardTitle>
        <CardDescription>
          See when you'll reach your savings goal
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Step 0: Input Goal with presets */}
        {step === 0 && (
          <div className="space-y-4">
            <div className="text-lg font-semibold">
              Choose a savings goal:
            </div>
            
            {/* Preset Goal Buttons */}
            <div className="grid grid-cols-2 gap-3">
              {PRESET_GOALS.map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => {
                    setGoalAmount(preset.amount.toString())
                    setError(null)
                  }}
                  className="flex flex-col items-center gap-2 p-4 border-2 rounded-lg hover:border-primary hover:bg-primary/5 transition-all"
                >
                  <Target className="h-6 w-6 text-primary" />
                  <div className="font-medium text-sm">{preset.label}</div>
                  <div className="text-lg font-bold">
                    ${preset.amount.toLocaleString('en-US')}
                  </div>
                </button>
              ))}
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">Or enter custom amount</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <Input
                  type="number"
                  min="0"
                  step="100"
                  value={goalAmount}
                  onChange={(e) => {
                    setGoalAmount(e.target.value)
                    setError(null)
                  }}
                  placeholder="Enter your goal amount"
                  className="text-lg"
                />
              </div>
              {error && (
                <div className="text-sm text-destructive">{error}</div>
              )}
            </div>
            <div className="text-sm text-muted-foreground">
              Current savings: ${currentSavings.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              })}
            </div>
            
            {/* Show monthly savings rate, or allow user to input */}
            {monthlySavingsRate > 0 ? (
              <div className="text-sm text-muted-foreground">
                Your monthly savings rate: ${monthlySavingsRate.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}/month
              </div>
            ) : (
              <div className="space-y-2">
                <label htmlFor="monthly-rate" className="text-sm font-medium">
                  Enter your monthly savings amount:
                </label>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                  <Input
                    id="monthly-rate"
                    type="number"
                    min="0"
                    step="10"
                    value={customMonthlyRate}
                    onChange={(e) => {
                      setCustomMonthlyRate(e.target.value)
                      setError(null)
                    }}
                    placeholder="e.g., 200"
                    className="text-lg"
                  />
                </div>
                <div className="text-xs text-muted-foreground">
                  We couldn't detect your monthly savings rate. Please enter how much you plan to save each month.
                </div>
              </div>
            )}
            
            <Button 
              onClick={handleCalculate} 
              disabled={calculating || !goalAmount || (monthlySavingsRate <= 0 && !customMonthlyRate)}
              className="w-full"
            >
              {calculating ? "Calculating..." : "Calculate Timeline"}
            </Button>
          </div>
        )}

        {/* Step 1: Show calculation */}
        {step === 1 && calculation && (
          <div className="space-y-4">
            {calculation.is_achievable && calculation.months_needed !== null && calculation.months_needed !== undefined ? (
              <>
                <div className="bg-muted p-4 rounded-lg space-y-2">
                  {calculation.months_needed === 0 ? (
                    <>
                      <div className="flex items-center gap-2 text-green-600">
                        <CheckCircle className="h-5 w-5" />
                        <span className="font-semibold text-lg">Congratulations! You've already reached your goal!</span>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Your current savings of ${currentSavings.toLocaleString('en-US', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        })} already exceeds your goal of ${goalAmount}.
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex justify-between items-center">
                        <span>You'll reach your goal in:</span>
                        <span className="font-semibold text-lg">
                          {calculation.months_needed} {calculation.months_needed === 1 ? 'month' : 'months'}
                        </span>
                      </div>
                      {calculation.years_needed && calculation.years_needed >= 1 && (
                        <div className="text-sm text-muted-foreground">
                          ({calculation.years_needed.toFixed(1)} years)
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span>Amount needed:</span>
                        <span className="font-semibold">
                          ${calculation.amount_needed.toLocaleString('en-US', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                          })}
                        </span>
                      </div>
                    </>
                  )}
                </div>
                {calculation.months_needed > 0 && (
                  <Button onClick={() => {
                    // Ensure slider is initialized before moving to step 2
                    if (weeklySavingsSlider === 0 && calculation.months_needed) {
                      const goal = parseFloat(goalAmount)
                      const amountNeeded = goal - currentSavings
                      const monthlyRate = amountNeeded / calculation.months_needed
                      const weeklyRate = monthlyRate / 4.33
                      const initialValue = Math.max(10, Math.round(weeklyRate / 5) * 5)
                      setWeeklySavingsSlider(initialValue)
                    }
                    setStep(2)
                  }} className="w-full">
                    See Progress <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                )}
              </>
            ) : (
              <div className="bg-muted p-4 rounded-lg">
                <div className="text-muted-foreground">
                  Your current savings rate may not be enough to reach this goal.
                  Consider increasing your monthly savings or adjusting your goal.
                </div>
                <Button onClick={() => setStep(0)} variant="outline" className="mt-4 w-full">
                  Change Goal
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Progress visualization with HYSA comparison */}
        {step === 2 && calculation && calculation.is_achievable && calculation.months_needed !== null && calculation.months_needed !== undefined && calculation.months_needed > 0 && (
          <div className="space-y-6">
            <div className="text-lg font-semibold flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Savings Progress
            </div>
            
            {/* Weekly Savings Slider */}
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-600 p-6 rounded-lg space-y-4">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-blue-600" />
                <div className="font-semibold">Adjust Your Weekly Savings</div>
              </div>
              <div className="text-sm text-muted-foreground">
                Slide to see how different weekly savings amounts affect your timeline
              </div>
              <Slider
                value={weeklySavingsSlider}
                onValueChange={(val) => {
                  setWeeklySavingsSlider(val)
                }}
                min={0}
                max={(() => {
                  const goal = parseFloat(goalAmount) || 0
                  const amountNeeded = Math.max(0, goal - currentSavings)
                  const calculatedMax = amountNeeded > 0 ? Math.ceil(amountNeeded / 52) * 2 : 500
                  return Math.max(500, calculatedMax)
                })()}
                step={5}
                label="Weekly Savings"
                formatValue={(val) => `$${val.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}/week`}
              />
              {/* Debug info - remove in production */}
              {process.env.NODE_ENV === 'development' && (
                <div className="text-xs text-muted-foreground">
                  Debug: Slider={weeklySavingsSlider}, Step={step}, Goal={goalAmount}
                </div>
              )}
              <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                <div className="text-center">
                  <div className="text-xs text-muted-foreground">Monthly Equivalent</div>
                  <div className="font-semibold text-lg">
                    ${(weeklySavingsSlider * 4.33).toLocaleString('en-US', {
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0
                    })}/mo
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground">Annual Savings</div>
                  <div className="font-semibold text-lg">
                    ${(weeklySavingsSlider * 52).toLocaleString('en-US', {
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0
                    })}/yr
                  </div>
                </div>
              </div>
            </div>
            
            {/* Timeline based on slider */}
            {calculation && calculation.months_needed && (
              <div className="bg-muted p-4 rounded-lg space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-semibold">Time to Goal:</span>
                  <span className="font-bold text-xl text-primary">
                    {calculation.months_needed < 12 
                      ? `${calculation.months_needed} ${calculation.months_needed === 1 ? 'month' : 'months'}`
                      : `${calculation.years_needed?.toFixed(1)} ${calculation.years_needed === 1 ? 'year' : 'years'}`
                    }
                  </span>
                </div>
                {calculation.years_needed && calculation.years_needed >= 1 && calculation.months_needed >= 12 && (
                  <div className="text-sm text-muted-foreground text-right">
                    ({calculation.months_needed} months)
                  </div>
                )}
              </div>
            )}
            
            {/* Progress Bar with milestones */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Current: ${currentSavings.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}</span>
                <span>Goal: ${goalAmount}</span>
              </div>
              <div className="relative">
                <div className="w-full bg-muted rounded-full h-6">
                  <div
                    className="bg-gradient-to-r from-green-600 to-green-400 h-6 rounded-full transition-all flex items-center justify-end pr-2"
                    style={{
                      width: `${Math.min(100, (currentSavings / parseFloat(goalAmount)) * 100)}%`
                    }}
                  >
                    <span className="text-white text-xs font-bold">You're here</span>
                  </div>
                </div>
                {/* Milestone markers */}
                {[25, 50, 75].map((milestone) => {
                  const milestoneAmount = parseFloat(goalAmount) * (milestone / 100)
                  const isPassed = currentSavings >= milestoneAmount
                  return (
                    <div
                      key={milestone}
                      className="absolute top-7 flex flex-col items-center"
                      style={{ left: `${milestone}%`, transform: 'translateX(-50%)' }}
                    >
                      <div className={`w-1 h-2 ${isPassed ? 'bg-green-600' : 'bg-muted-foreground'}`} />
                      <span className="text-xs text-muted-foreground mt-1">{milestone}%</span>
                    </div>
                  )
                })}
              </div>
              {calculation && calculation.months_needed && (
                <div className="text-sm text-muted-foreground text-center mt-8">
                  {calculation.months_needed} {calculation.months_needed === 1 ? 'month' : 'months'} to reach your goal
                </div>
              )}
            </div>

            {/* HYSA Comparison */}
            {showHYSAComparison && getHYSAComparison() && (
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-600 p-6 rounded-lg space-y-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-6 w-6 text-blue-600" />
                  <div className="font-semibold">High-Yield Savings Account ({HYSA_APY}% APY)</div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">Extra Interest Earned</div>
                    <div className="font-semibold text-blue-600 text-xl">
                      ${getHYSAComparison()!.interestEarned.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}
                    </div>
                  </div>
                  {getHYSAComparison()!.monthsSaved > 0 && (
                    <div className="bg-white p-3 rounded-lg">
                      <div className="text-xs text-muted-foreground">Time Saved</div>
                      <div className="font-semibold text-blue-600 text-xl">
                        {getHYSAComparison()!.monthsSaved} months
                      </div>
                    </div>
                  )}
                </div>
                <div className="text-sm text-muted-foreground">
                  With a high-yield savings account, compound interest helps you reach your goal faster.
                </div>
              </div>
            )}

            <div className="bg-muted p-4 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span>Weekly Savings Rate:</span>
                <span className="font-semibold">
                  ${weeklySavingsSlider.toLocaleString('en-US', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                  })}/week
                </span>
              </div>
              <div className="flex justify-between">
                <span>Monthly Savings Rate:</span>
                <span className="font-semibold">
                  ${(weeklySavingsSlider * 4.33).toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })}/month
                </span>
              </div>
              {calculation.years_needed && calculation.years_needed >= 1 && (
                <div className="flex justify-between">
                  <span>Timeframe:</span>
                  <span className="font-semibold">
                    {calculation.years_needed.toFixed(1)} years
                  </span>
                </div>
              )}
            </div>

            <Button onClick={handleViewOffers} className="w-full">
              See Offers for High-Yield Savings Accounts
            </Button>
            
            <Button onClick={() => setStep(0)} variant="outline" className="w-full">
              Try Different Goal
            </Button>
          </div>
        )}

      </CardContent>
    </Card>
  )
}

