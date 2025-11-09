import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { RetroBadge } from "@/components/ui/retro-badge"
import { AccountCard } from "@/components/account-card"
import { AccountDetailPanel } from "@/components/account-detail-panel"
import { getValidUserId, formatCurrency, formatPercentage } from "@/lib/utils"
import { fetchOverview, fetchAccountDetails, type OverviewData, type Account } from "@/lib/api"
import { Wallet, TrendingUp, CreditCard } from "lucide-react"

// Health status badge component
function HealthBadge({ status }: { status: "good" | "fair" | "needs_attention" }) {
  const variants = {
    good: "success" as const,
    fair: "warning" as const,
    needs_attention: "destructive" as const,
  }

  const labels = {
    good: "Good",
    fair: "Fair",
    needs_attention: "Needs Attention",
  }

  return (
    <RetroBadge variant={variants[status]}>
      {labels[status]}
    </RetroBadge>
  )
}

export function ProfilePage() {
  const { userId } = useParams<{ userId: string }>()
  const [loading, setLoading] = useState(true)
  const [overviewData, setOverviewData] = useState<OverviewData | null>(null)
  const [accountsData, setAccountsData] = useState<any>(null)
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null)
  const [panelOpen, setPanelOpen] = useState(false)

  useEffect(() => {
    if (!userId) {
      setLoading(false)
      return
    }

    const validUserId = getValidUserId(userId)
    setLoading(true)
    
    Promise.all([
      fetchOverview(validUserId),
      fetchAccountDetails(validUserId)
    ])
      .then(([overview, accounts]) => {
        setOverviewData(overview)
        setAccountsData(accounts)
        setLoading(false)
      })
      .catch((err) => {
        console.error("Error fetching profile data:", err)
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

  if (!overviewData || !accountsData) {
    return (
      <div>
        <div className="text-center font-mono">No profile data available.</div>
      </div>
    )
  }

  // Organize accounts by type
  const checkingAccounts = accountsData?.accounts.filter(
    (acc: Account) => acc.type === 'depository' && acc.subtype === 'checking'
  ) || []
  
  const savingsAccounts = accountsData?.accounts.filter(
    (acc: Account) => acc.type === 'depository' && acc.subtype === 'savings'
  ) || []
  
  const creditAccounts = accountsData?.accounts.filter(
    (acc: Account) => acc.type === 'credit'
  ) || []
  
  const loanAccounts = accountsData?.accounts.filter(
    (acc: Account) => acc.type === 'loan'
  ) || []

  return (
    <div>
      {/* Financial Health Overview */}
      <RetroCard className="mb-5">
        <RetroCardHeader>
          <RetroCardTitle className="text-base">FINANCIAL HEALTH</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div>
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-2">
                Overall Health
              </div>
              <HealthBadge status={overviewData.data.health.overall} />
              <p className="text-xs font-mono mt-2 text-retro-charcoal-light">
                {overviewData.data.summary.net_worth >= 0 ? "Positive net worth" : "Building wealth"}
              </p>
            </div>
            
            <div>
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-2">
                Credit Utilization
              </div>
              <div className="text-2xl font-mono font-bold text-retro-charcoal tabular-nums">
                {formatPercentage(overviewData.data.health.credit_utilization)}
              </div>
              <p className="text-xs font-mono mt-2 text-retro-charcoal-light">
                {overviewData.data.health.credit_utilization < 30 ? "Excellent" :
                 overviewData.data.health.credit_utilization < 50 ? "Good" : "Needs attention"}
              </p>
            </div>
            
            <div>
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-2">
                Emergency Fund
              </div>
              <div className="text-2xl font-mono font-bold text-retro-charcoal tabular-nums">
                {overviewData.data.health.emergency_fund_months ? `${overviewData.data.health.emergency_fund_months.toFixed(1)}mo` : "N/A"}
              </div>
              <p className="text-xs font-mono mt-2 text-retro-charcoal-light">
                {overviewData.data.health.emergency_fund_months && overviewData.data.health.emergency_fund_months >= 6 ? "Excellent" :
                 overviewData.data.health.emergency_fund_months && overviewData.data.health.emergency_fund_months >= 3 ? "Good" : "Building"}
              </p>
            </div>
          </div>
        </RetroCardContent>
      </RetroCard>

      {/* Account Balances Summary */}
      <div className="grid gap-5 md:grid-cols-3 mb-5">
        <RetroCard>
          <RetroCardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Wallet className="w-5 h-5 text-trust-primary" />
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider">
                Checking
              </div>
            </div>
            <div className="text-2xl font-mono font-bold text-retro-charcoal tabular-nums">
              {formatCurrency(overviewData.data.accounts.checking.reduce((sum, acc) => sum + acc.balance, 0))}
            </div>
          </RetroCardContent>
        </RetroCard>

        <RetroCard>
          <RetroCardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-5 h-5 text-trust-success" />
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider">
                Savings
              </div>
            </div>
            <div className="text-2xl font-mono font-bold text-retro-charcoal tabular-nums">
              {formatCurrency(overviewData.data.summary.total_savings)}
            </div>
          </RetroCardContent>
        </RetroCard>

        <RetroCard>
          <RetroCardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <CreditCard className="w-5 h-5 text-trust-error" />
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider">
                Credit
              </div>
            </div>
            <div className="text-2xl font-mono font-bold text-retro-charcoal tabular-nums">
              {formatCurrency(overviewData.data.summary.total_credit_debt)}
            </div>
            <div className="text-xs font-mono text-retro-charcoal-light">
              of {formatCurrency(overviewData.data.summary.total_credit_limit)}
            </div>
          </RetroCardContent>
        </RetroCard>
      </div>

      {/* Checking Accounts */}
      {checkingAccounts.length > 0 && (
        <RetroCard className="mb-5">
          <RetroCardHeader>
            <RetroCardTitle className="text-base flex items-center gap-2">
              <Wallet className="w-4 h-4" />
              CHECKING ACCOUNTS
            </RetroCardTitle>
          </RetroCardHeader>
          <RetroCardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {checkingAccounts.map((account: Account) => (
                <AccountCard
                  key={account.account_id}
                  account={account}
                  onClick={() => handleAccountClick(account)}
                />
              ))}
            </div>
          </RetroCardContent>
        </RetroCard>
      )}

      {/* Savings Accounts */}
      {savingsAccounts.length > 0 && (
        <RetroCard className="mb-5">
          <RetroCardHeader>
            <RetroCardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              SAVINGS ACCOUNTS
            </RetroCardTitle>
          </RetroCardHeader>
          <RetroCardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {savingsAccounts.map((account: Account) => (
                <AccountCard
                  key={account.account_id}
                  account={account}
                  onClick={() => handleAccountClick(account)}
                />
              ))}
            </div>
          </RetroCardContent>
        </RetroCard>
      )}

      {/* Credit Cards */}
      {creditAccounts.length > 0 && (
        <RetroCard className="mb-5">
          <RetroCardHeader>
            <RetroCardTitle className="text-base flex items-center gap-2">
              <CreditCard className="w-4 h-4" />
              CREDIT CARDS
            </RetroCardTitle>
          </RetroCardHeader>
          <RetroCardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {creditAccounts.map((account: Account) => (
                <AccountCard
                  key={account.account_id}
                  account={account}
                  onClick={() => handleAccountClick(account)}
                />
              ))}
            </div>
          </RetroCardContent>
        </RetroCard>
      )}

      {/* Loans */}
      {loanAccounts.length > 0 && (
        <RetroCard className="mb-5">
          <RetroCardHeader>
            <RetroCardTitle className="text-base">LOANS</RetroCardTitle>
          </RetroCardHeader>
          <RetroCardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {loanAccounts.map((account: Account) => (
                <AccountCard
                  key={account.account_id}
                  account={account}
                  onClick={() => handleAccountClick(account)}
                />
              ))}
            </div>
          </RetroCardContent>
        </RetroCard>
      )}

      {/* Account Detail Panel */}
      {selectedAccount && (
        <AccountDetailPanel
          account={selectedAccount}
          userId={userId || ''}
          open={panelOpen}
          onOpenChange={setPanelOpen}
        />
      )}
    </div>
  )
}


