import { useState, useEffect } from "react"
import { fetchUser } from "@/lib/api"
import { BalanceTransferModule } from "./BalanceTransferModule"
import { SubscriptionModule } from "./SubscriptionModule"
import { SavingsGoalModule } from "./SavingsGoalModule"
import { BudgetBreakdownModule } from "./BudgetBreakdownModule"

interface PersonaModuleRouterProps {
  userId: string
}

type Persona = 
  | "high_utilization"
  | "variable_income"
  | "subscription_heavy"
  | "savings_builder"
  | "general_wellness"

export function PersonaModuleRouter({ userId }: PersonaModuleRouterProps) {
  const [persona, setPersona] = useState<Persona | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [debugInfo, setDebugInfo] = useState<string>("")

  useEffect(() => {
    loadPersona()
  }, [userId])

  async function loadPersona() {
    try {
      setLoading(true)
      setError(null)
      const user = await fetchUser(userId)
      
      // Debug: log user data
      console.log('User data for persona detection:', user)
      
      // Get persona from user data
      // The API returns persona in personas.30d or personas.180d
      const personas = user.personas
      let detectedPersona: Persona | null = null

      if (personas) {
        // Try 30d first, then 180d
        const persona30d = personas['30d']
        const persona180d = personas['180d']
        
        setDebugInfo(`Found personas: 30d=${persona30d ? 'yes' : 'no'}, 180d=${persona180d ? 'yes' : 'no'}`)
        
        const personaData = persona30d || persona180d
        
        if (personaData) {
          // Check for primary_persona first
          if (personaData.primary_persona) {
            detectedPersona = personaData.primary_persona as Persona
            setDebugInfo(`Using primary_persona: ${personaData.primary_persona}`)
          } else if (personaData.persona) {
            detectedPersona = personaData.persona as Persona
            setDebugInfo(`Using persona: ${personaData.persona}`)
          } else if (personaData.match_percentages) {
            // Find persona with highest match percentage
            const matches = personaData.match_percentages as Record<string, number>
            const sorted = Object.entries(matches).sort((a, b) => b[1] - a[1])
            if (sorted.length > 0 && sorted[0][1] > 0) {
              detectedPersona = sorted[0][0] as Persona
              setDebugInfo(`Using highest match: ${sorted[0][0]} (${sorted[0][1]}%)`)
            } else {
              setDebugInfo('No match percentages found')
            }
          }
        } else {
          setDebugInfo('No persona data found')
        }
      } else {
        setDebugInfo('No personas object found in user data')
      }

      // Fallback to general_wellness if no persona detected
      const finalPersona = detectedPersona || "general_wellness"
      setPersona(finalPersona)
      setDebugInfo(prev => `${prev} | Final persona: ${finalPersona}`)
      setLoading(false)
    } catch (err) {
      console.error('Error loading persona:', err)
      setError(err instanceof Error ? err.message : "Failed to load persona")
      setDebugInfo(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
      // Set a default persona even on error so modules can still show
      setPersona("general_wellness")
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div>Loading personalized module...</div>
        {debugInfo && <div className="text-xs text-muted-foreground mt-2">{debugInfo}</div>}
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-destructive py-8">
        <div>Error: {error}</div>
        {debugInfo && <div className="text-xs text-muted-foreground mt-2">{debugInfo}</div>}
        <div className="text-sm text-muted-foreground mt-4">
          Showing default module for general wellness.
        </div>
      </div>
    )
  }

  // Route to appropriate module based on persona
  // For general_wellness, show SavingsGoalModule as a default
  switch (persona) {
    case "high_utilization":
      return <BalanceTransferModule userId={userId} />
    
    case "subscription_heavy":
      return <SubscriptionModule userId={userId} />
    
    case "savings_builder":
      return <SavingsGoalModule userId={userId} />
    
    case "variable_income":
      return <BudgetBreakdownModule userId={userId} />
    
    case "general_wellness":
    default:
      // Show SavingsGoalModule as default instead of returning null
      return <SavingsGoalModule userId={userId} />
  }
}

