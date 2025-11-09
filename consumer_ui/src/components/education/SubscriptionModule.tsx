import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  fetchSignals, 
  calculateSubscriptionSavings,
  type SubscriptionSavingsCalculation
} from "@/lib/api"
import { CreditCard, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface SubscriptionModuleProps {
  userId: string
}

interface Subscription {
  merchant: string
  amount: number
  monthly_equivalent: number
  frequency: string
}

export function SubscriptionModule({ userId }: SubscriptionModuleProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [selectedIndices, setSelectedIndices] = useState<number[]>([])
  const [totalMonthly, setTotalMonthly] = useState(0)
  const [totalYearly, setTotalYearly] = useState(0)
  const [calculation, setCalculation] = useState<SubscriptionSavingsCalculation | null>(null)

  useEffect(() => {
    loadData()
  }, [userId])

  useEffect(() => {
    if (selectedIndices.length > 0) {
      calculateSavings()
    } else {
      setCalculation(null)
    }
  }, [selectedIndices, subscriptions])

  async function loadData() {
    try {
      setLoading(true)
      const signals = await fetchSignals(userId)
      const subscriptionSignal = signals.subscriptions

      // Use merchant_details if available, otherwise use recurring_merchants
      const merchantData = (subscriptionSignal as any)?.merchant_details || subscriptionSignal?.recurring_merchants || []
      
      if (merchantData.length > 0) {
        const subs = merchantData.map((m: any) => ({
          merchant: m.merchant || 'Unknown',
          amount: m.amount || 0,
          monthly_equivalent: m.monthly_equivalent || m.amount || 0,
          frequency: m.frequency || 'monthly'
        }))
        setSubscriptions(subs)
        
        const monthly = subscriptionSignal.monthly_recurring || 0
        setTotalMonthly(monthly)
        setTotalYearly(monthly * 12)
      }
      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load subscriptions")
      setLoading(false)
    }
  }

  async function calculateSavings() {
    try {
      const result = await calculateSubscriptionSavings(userId, selectedIndices)
      setCalculation(result)
    } catch (err) {
      console.error("Failed to calculate savings", err)
    }
  }

  function toggleSubscription(index: number) {
    setSelectedIndices(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    )
  }

  function getMerchantLogo(merchant: string): string {
    // Try to use better logo services
    const cleanMerchant = merchant.toLowerCase().trim()
    
    // Common subscription services with known logos
    const logoMap: Record<string, string> = {
      'netflix': 'https://logo.clearbit.com/netflix.com',
      'spotify': 'https://logo.clearbit.com/spotify.com',
      'hulu': 'https://logo.clearbit.com/hulu.com',
      'disney+': 'https://logo.clearbit.com/disneyplus.com',
      'disney plus': 'https://logo.clearbit.com/disneyplus.com',
      'apple': 'https://logo.clearbit.com/apple.com',
      'icloud': 'https://logo.clearbit.com/icloud.com',
      'amazon': 'https://logo.clearbit.com/amazon.com',
      'prime': 'https://logo.clearbit.com/amazon.com',
      'youtube': 'https://logo.clearbit.com/youtube.com',
      'gym': 'https://logo.clearbit.com/planetfitness.com',
      'planet fitness': 'https://logo.clearbit.com/planetfitness.com',
      'adobe': 'https://logo.clearbit.com/adobe.com',
      'microsoft': 'https://logo.clearbit.com/microsoft.com',
      'office': 'https://logo.clearbit.com/microsoft.com',
      'dropbox': 'https://logo.clearbit.com/dropbox.com',
      'nyt': 'https://logo.clearbit.com/nytimes.com',
      'new york times': 'https://logo.clearbit.com/nytimes.com',
      'peloton': 'https://logo.clearbit.com/onepeloton.com',
      'hellofresh': 'https://logo.clearbit.com/hellofresh.com',
    }
    
    // Check if we have a known logo
    for (const [key, logo] of Object.entries(logoMap)) {
      if (cleanMerchant.includes(key)) {
        return logo
      }
    }
    
    // Fallback to UI avatars
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(merchant)}&background=random&size=96&font-size=0.4&bold=true`
  }
  
  function getCancellationLink(merchant: string): string | null {
    const cleanMerchant = merchant.toLowerCase().trim()
    
    const cancellationLinks: Record<string, string> = {
      'netflix': 'https://help.netflix.com/en/node/407',
      'spotify': 'https://support.spotify.com/us/article/close-account/',
      'hulu': 'https://help.hulu.com/s/article/cancel-subscription',
      'disney+': 'https://help.disneyplus.com/csp?id=csp_article_content&sys_kb_id=f17a6c38db3048d03c0cf158bf9619e2',
      'disney plus': 'https://help.disneyplus.com/csp?id=csp_article_content&sys_kb_id=f17a6c38db3048d03c0cf158bf9619e2',
      'amazon': 'https://www.amazon.com/mc/yourmembershipsandsubscriptions',
      'prime': 'https://www.amazon.com/mc/yourmembershipsandsubscriptions',
      'youtube': 'https://www.youtube.com/paid_memberships',
      'adobe': 'https://helpx.adobe.com/manage-account/using/cancel-subscription.html',
    }
    
    for (const [key, link] of Object.entries(cancellationLinks)) {
      if (cleanMerchant.includes(key)) {
        return link
      }
    }
    
    return null
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">Loading your subscriptions...</div>
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

  if (subscriptions.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            No subscriptions detected at this time.
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-6 w-6" />
          Subscription Manager
        </CardTitle>
        <CardDescription>
          See how much you're spending on subscriptions and how much you could save
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary */}
        <div className="space-y-2">
          <div className="text-lg font-semibold">
            You're spending ${totalMonthly.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            })}/month on subscriptions
          </div>
          <div className="text-muted-foreground">
            That's ${totalYearly.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            })} per year total
          </div>
        </div>

        {/* Quick Select Buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedIndices(subscriptions.map((_, i) => i))}
            className="flex-1"
          >
            Select All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedIndices([])}
            className="flex-1"
          >
            Deselect All
          </Button>
        </div>

        {/* Instructions */}
        <div className="text-sm text-muted-foreground">
          Click logos to see how much you'd save if you cancel
        </div>

        {/* Subscription Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {subscriptions.map((sub, index) => {
            const isSelected = selectedIndices.includes(index)
            const cancellationLink = getCancellationLink(sub.merchant)
            return (
              <div key={index} className="flex flex-col gap-2">
                <button
                  onClick={() => toggleSubscription(index)}
                  className={cn(
                    "relative flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all transform",
                    isSelected 
                      ? "border-primary bg-primary/10 scale-95" 
                      : "border-border hover:border-primary/50 hover:scale-105"
                  )}
                >
                  {isSelected && (
                    <div className="absolute top-2 right-2 bg-primary text-primary-foreground rounded-full p-1 animate-in zoom-in duration-200">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                  )}
                  <img
                    src={getMerchantLogo(sub.merchant)}
                    alt={sub.merchant}
                    className="w-16 h-16 rounded-lg object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement
                      target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(sub.merchant.charAt(0))}&background=random&size=96&font-size=0.5&bold=true`
                    }}
                  />
                  <div className="text-center w-full">
                    <div className="font-medium text-sm truncate">{sub.merchant}</div>
                    <div className="text-xs text-muted-foreground">
                      ${sub.monthly_equivalent.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}/mo
                    </div>
                    <Badge variant="outline" className="mt-1 text-xs">
                      {sub.frequency === 'weekly' ? 'Weekly' : 'Monthly'}
                    </Badge>
                  </div>
                </button>
                {cancellationLink && (
                  <a
                    href={cancellationLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-center text-primary hover:underline"
                  >
                    Cancel Guide
                  </a>
                )}
              </div>
            )
          })}
        </div>

        {/* Savings Calculation */}
        {calculation && (
          <div className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-600 p-6 rounded-lg space-y-3 animate-in slide-in-from-bottom duration-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <div className="text-lg font-semibold">
                Potential Savings
              </div>
            </div>
            <div className="text-sm text-muted-foreground">
              By canceling {calculation.canceled_count} {calculation.canceled_count === 1 ? 'subscription' : 'subscriptions'}, you could save:
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white p-3 rounded-lg">
                <div className="text-xs text-muted-foreground">Monthly</div>
                <div className="font-semibold text-green-600 text-2xl">
                  ${calculation.monthly_savings.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })}
                </div>
              </div>
              <div className="bg-white p-3 rounded-lg">
                <div className="text-xs text-muted-foreground">Yearly</div>
                <div className="font-semibold text-green-600 text-2xl">
                  ${calculation.yearly_savings.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedIndices.length === 0 && (
          <div className="text-sm text-muted-foreground text-center">
            Select subscriptions above to see your potential savings
          </div>
        )}
      </CardContent>
    </Card>
  )
}

