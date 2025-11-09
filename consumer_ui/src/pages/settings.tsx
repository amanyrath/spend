import { useState } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { revokeConsent } from '@/lib/api'
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from '@/components/ui/retro-card'
import { RetroButton } from '@/components/ui/retro-button'

export function SettingsPage() {
  const { user, signOut } = useAuth()
  const [showRevokeConfirm, setShowRevokeConfirm] = useState(false)
  
  const handleRevokeConsent = async () => {
    if (!user) return
    
    await revokeConsent(user.uid)
    alert('Consent revoked. You will need to grant consent again to use SpendSense.')
    window.location.reload()
  }
  
  return (
    <div className="space-y-5">
      <RetroCard>
        <RetroCardHeader>
          <RetroCardTitle>PRIVACY & CONSENT</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <p className="text-sm mb-4 font-mono">
            You have granted consent for SpendSense to analyze your financial data.
          </p>
          {!showRevokeConfirm ? (
            <RetroButton
              variant="destructive"
              onClick={() => setShowRevokeConfirm(true)}
            >
              REVOKE CONSENT
            </RetroButton>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-destructive font-mono">
                Are you sure? You will lose access to personalized recommendations.
              </p>
              <div className="flex gap-3">
                <RetroButton
                  variant="destructive"
                  onClick={handleRevokeConsent}
                >
                  YES, REVOKE
                </RetroButton>
                <RetroButton
                  variant="outline"
                  onClick={() => setShowRevokeConfirm(false)}
                >
                  CANCEL
                </RetroButton>
              </div>
            </div>
          )}
        </RetroCardContent>
      </RetroCard>
      
      <RetroCard>
        <RetroCardHeader>
          <RetroCardTitle>ACCOUNT</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <p className="text-sm mb-4 font-mono">Email: {user?.email}</p>
          <RetroButton onClick={signOut}>SIGN OUT</RetroButton>
        </RetroCardContent>
      </RetroCard>
    </div>
  )
}





