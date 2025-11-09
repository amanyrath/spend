import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { ChatWindow } from "@/components/chat-window"
import { getValidUserId } from "@/lib/utils"

export function HelpPage() {
  const { userId } = useParams<{ userId: string }>()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!userId) {
      setLoading(false)
      return
    }

    const validUserId = getValidUserId(userId)
    setLoading(false)
  }, [userId])

  if (loading) {
    return (
      <div>
        <div className="text-center font-mono">Loading help...</div>
      </div>
    )
  }

  const validUserId = userId ? getValidUserId(userId) : 'user_001'

  return (
    <div>
      {/* Help Introduction */}
      <RetroCard className="mb-5">
        <RetroCardHeader>
          <RetroCardTitle className="text-base">ABOUT YOUR MISSION</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <div className="space-y-4">
            <p className="text-sm font-mono text-retro-charcoal leading-relaxed">
              Hi! I can help you answer questions about your mission and financial journey.
            </p>
            
            <div className="space-y-2">
              <div className="text-xs font-mono text-retro-charcoal-light">
                Quick questions you might have:
              </div>
              <ul className="space-y-1 text-sm font-mono text-retro-charcoal">
                <li>• "Why is 30% utilization the goal?"</li>
                <li>• "When will my credit score improve?"</li>
                <li>• "What if I can't save $500 right now?"</li>
              </ul>
            </div>
          </div>
        </RetroCardContent>
      </RetroCard>

      {/* Chat Interface */}
      <RetroCard>
        <RetroCardHeader>
          <RetroCardTitle className="text-base">ASK A QUESTION</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <ChatWindow userId={validUserId} variant="inline" />
        </RetroCardContent>
      </RetroCard>
    </div>
  )
}


