import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from '@/components/ui/retro-card'
import { RetroButton } from '@/components/ui/retro-button'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await signIn(email, password)
      // Navigate after successful login (will be handled by App routing)
      navigate('/')
    } catch (err: any) {
      setError(err.message || 'Failed to sign in')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <RetroCard className="w-full max-w-md">
        <RetroCardHeader>
          <RetroCardTitle className="text-center text-2xl">SPENDSENSE LOGIN</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-mono mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-2 border border-retro-border font-mono"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-mono mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full p-2 border border-retro-border font-mono"
                required
              />
            </div>
            {error && (
              <div className="text-sm text-destructive font-mono">{error}</div>
            )}
            <RetroButton type="submit" disabled={loading} className="w-full">
              {loading ? 'SIGNING IN...' : 'SIGN IN'}
            </RetroButton>
          </form>
          <div className="mt-4 text-xs text-center font-mono text-muted-foreground">
            Demo: hannah@demo.com / demo123
          </div>
        </RetroCardContent>
      </RetroCard>
    </div>
  )
}





