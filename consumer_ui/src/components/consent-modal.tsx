import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { RetroButton } from '@/components/ui/retro-button'

interface ConsentModalProps {
  open: boolean
  onAccept: () => Promise<void>
  onDecline: () => void
}

export function ConsentModal({ open, onAccept, onDecline }: ConsentModalProps) {
  const [accepted, setAccepted] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleAccept = async () => {
    setLoading(true)
    try {
      await onAccept()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-mono">WELCOME TO SPENDSENSE</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 font-mono text-sm">
          <p>We'll analyze your transaction data to provide personalized financial education.</p>
          
          <div>
            <div className="font-semibold mb-2">What we access:</div>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Your transaction history</li>
              <li>Account balances and types</li>
              <li>Payment patterns and subscriptions</li>
            </ul>
          </div>

          <div>
            <div className="font-semibold mb-2">What we don't do:</div>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Share your data with third parties (except partner offers you click)</li>
              <li>Provide financial advice (only education)</li>
              <li>Access your login credentials</li>
            </ul>
          </div>

          <p className="text-xs text-muted-foreground">
            You can revoke consent anytime in Settings.
          </p>

          <div className="flex items-center gap-2 pt-4">
            <input
              type="checkbox"
              id="consent-check"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="consent-check" className="text-xs">
              I consent to SpendSense analyzing my financial data
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <RetroButton
              onClick={handleAccept}
              disabled={!accepted || loading}
              className="flex-1"
            >
              {loading ? 'PROCESSING...' : 'ACCEPT'}
            </RetroButton>
            <RetroButton
              onClick={onDecline}
              variant="outline"
              className="flex-1"
            >
              DECLINE
            </RetroButton>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}





