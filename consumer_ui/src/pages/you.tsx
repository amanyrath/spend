import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { getValidUserId } from "@/lib/utils"
import type { Account, AccountsResponse } from "@/lib/api"
import { fetchAccountDetails } from "@/lib/api"
import { AccountCard } from "@/components/account-card"
import { AccountDetailPanel } from "@/components/account-detail-panel"
import { CreditCard, Wallet, TrendingUp, Home, GraduationCap, Car } from "lucide-react"

export function YouPage() {
  const { userId } = useParams<{ userId: string }>()
  const [loading, setLoading] = useState(false)
  const [accountsData, setAccountsData] = useState<AccountsResponse | null>(null)
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null)
  const [panelOpen, setPanelOpen] = useState(false)

  useEffect(() => {
    if (!userId) {
      setLoading(false)
      return
    }

    const validUserId = getValidUserId(userId)
    setLoading(true)
    
    fetchAccountDetails(validUserId)
      .then((data) => {
        setAccountsData(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error("Error fetching account details:", err)
        setLoading(false)
      })
  }, [userId])

  const handleAccountClick = (account: Account) => {
    setSelectedAccount(account)
    setPanelOpen(true)
  }

  if (loading) {
    return (
      <div>
        <div className="text-center font-mono">Loading profile...</div>
      </div>
    )
  }

  // Organize accounts by type
  const checkingAccounts = accountsData?.accounts.filter(
    acc => acc.type === 'depository' && acc.subtype === 'checking'
  ) || []
  
  const savingsAccounts = accountsData?.accounts.filter(
    acc => acc.type === 'depository' && acc.subtype === 'savings'
  ) || []
  
  const creditAccounts = accountsData?.accounts.filter(
    acc => acc.type === 'credit'
  ) || []
  
  const loanAccounts = accountsData?.accounts.filter(
    acc => acc.type === 'loan'
  ) || []

  return (
    <div>
      {/* Profile Info */}
      <RetroCard className="mb-5">
        <RetroCardHeader>
          <RetroCardTitle className="text-base">ACCOUNT INFORMATION</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <div className="space-y-4">
            <div>
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-1">
                Member Since
              </div>
              <div className="text-sm font-mono text-retro-charcoal">January 2024</div>
            </div>
            <div>
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-1">
                Financial Profile
              </div>
              <div className="text-sm font-mono text-retro-charcoal">High Credit Use</div>
            </div>
          </div>
        </RetroCardContent>
      </RetroCard>

      {/* Checking Accounts */}
      {checkingAccounts.length > 0 && (
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <Wallet className="h-5 w-5 text-retro-charcoal-light" />
            <h2 className="text-lg font-mono font-semibold text-retro-charcoal">
              CHECKING ACCOUNTS
            </h2>
          </div>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {checkingAccounts.map((account) => (
              <AccountCard 
                key={account.account_id} 
                account={account}
                onClick={() => handleAccountClick(account)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Savings Accounts */}
      {savingsAccounts.length > 0 && (
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-5 w-5 text-retro-charcoal-light" />
            <h2 className="text-lg font-mono font-semibold text-retro-charcoal">
              SAVINGS ACCOUNTS
            </h2>
          </div>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {savingsAccounts.map((account) => (
              <AccountCard 
                key={account.account_id} 
                account={account}
                onClick={() => handleAccountClick(account)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Credit Cards */}
      {creditAccounts.length > 0 && (
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <CreditCard className="h-5 w-5 text-retro-charcoal-light" />
            <h2 className="text-lg font-mono font-semibold text-retro-charcoal">
              CREDIT CARDS
            </h2>
          </div>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {creditAccounts.map((account) => (
              <AccountCard 
                key={account.account_id} 
                account={account}
                onClick={() => handleAccountClick(account)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Loans */}
      {loanAccounts.length > 0 && (
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <Home className="h-5 w-5 text-retro-charcoal-light" />
            <h2 className="text-lg font-mono font-semibold text-retro-charcoal">
              LOANS
            </h2>
          </div>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {loanAccounts.map((account) => (
              <AccountCard 
                key={account.account_id} 
                account={account}
                onClick={() => handleAccountClick(account)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Preferences */}
      <RetroCard>
        <RetroCardHeader>
          <RetroCardTitle className="text-base">PREFERENCES</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <div className="space-y-3 text-sm font-mono">
            <div className="flex justify-between">
              <span className="text-retro-charcoal-light">Notifications:</span>
              <span className="text-retro-charcoal">On</span>
            </div>
            <div className="flex justify-between">
              <span className="text-retro-charcoal-light">Data Sharing:</span>
              <span className="text-retro-charcoal">Educational Only</span>
            </div>
            <div className="flex justify-between">
              <span className="text-retro-charcoal-light">Mission Pace:</span>
              <span className="text-retro-charcoal">Standard</span>
            </div>
          </div>
        </RetroCardContent>
      </RetroCard>

      {/* Account Detail Panel */}
      <AccountDetailPanel
        account={selectedAccount}
        userId={getValidUserId(userId)}
        open={panelOpen}
        onOpenChange={setPanelOpen}
      />
    </div>
  )
}


