import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { ConsentModal } from '@/components/consent-modal'
import { getConsentStatus, grantConsent } from '@/lib/api'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const [consentStatus, setConsentStatus] = useState<boolean | null>(null)
  const [showConsentModal, setShowConsentModal] = useState(false)
  const [checkingConsent, setCheckingConsent] = useState(true)

  useEffect(() => {
    if (user) {
      // Check consent status
      getConsentStatus(user.uid)
        .then((status) => {
          setConsentStatus(status.granted)
          if (!status.granted) {
            setShowConsentModal(true)
          }
          setCheckingConsent(false)
        })
        .catch(() => {
          setCheckingConsent(false)
        })
    }
  }, [user])

  const handleAcceptConsent = async () => {
    if (!user) return
    
    await grantConsent(user.uid)
    setConsentStatus(true)
    setShowConsentModal(false)
  }

  const handleDeclineConsent = () => {
    // User declined - show message
    setShowConsentModal(false)
  }

  if (loading || checkingConsent) {
    return <div className="flex items-center justify-center min-h-screen font-mono">Loading...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (consentStatus === false && !showConsentModal) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="text-center font-mono">
          <p>SpendSense requires consent to provide personalized education.</p>
          <p className="mt-2 text-sm text-muted-foreground">
            You can grant consent anytime in Settings.
          </p>
        </div>
      </div>
    )
  }

  return (
    <>
      {children}
      <ConsentModal
        open={showConsentModal}
        onAccept={handleAcceptConsent}
        onDecline={handleDeclineConsent}
      />
    </>
  )
}





