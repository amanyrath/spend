import { RefreshCw } from 'lucide-react'
import { AnalyticsData } from '../App'
import { PersonaDistributionChart } from './PersonaDistributionChart'
import { PersonaTrendsChart } from './PersonaTrendsChart'
import { SuccessMetricsTable } from './SuccessMetricsTable'
import { ActiveUsersCard } from './ActiveUsersCard'
import { SafetyIndicatorsPanel } from './SafetyIndicatorsPanel'

interface AnalyticsDashboardProps {
  data: AnalyticsData | null
  loading: boolean
  error: string | null
  onRefresh: () => void
}

export function AnalyticsDashboard({ data, loading, error, onRefresh }: AnalyticsDashboardProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-4 border-neutral border-t-primary rounded-full animate-spin"></div>
          <div className="mt-4 text-sm text-neutral uppercase tracking-wider">Loading Analytics...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="max-w-md w-full bg-red-50 border border-red-200 p-6">
          <div className="text-red-900 font-bold uppercase tracking-wide text-sm mb-2">Error</div>
          <div className="text-red-800 text-xs mb-4">{error}</div>
          <button
            onClick={onRefresh}
            className="bg-primary text-white px-4 py-2 text-xs font-semibold uppercase tracking-wider hover:bg-blue-900 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-60 bg-white border-r-2 border-dashed border-gray-200 p-5">
        <div className="pb-5 mb-5 border-b border-dashed border-gray-200">
          <div className="text-lg font-bold tracking-wider text-primary mb-1">SPENDSENSE</div>
          <div className="text-xs text-neutral tracking-wider">ANALYTICS VIEW</div>
        </div>
        
        <nav className="space-y-1">
          <a href="/operator_ui/templates/user_list.html" className="block px-4 py-3 text-xs font-semibold text-neutral uppercase tracking-wider hover:bg-gray-50 hover:text-primary transition-colors border-l-3 border-transparent hover:border-gray-200">
            User List
          </a>
          <a href="/operator_ui/templates/analytics.html" className="block px-4 py-3 text-xs font-semibold bg-blue-50 text-primary uppercase tracking-wider border-l-3 border-primary">
            Analytics
          </a>
          <a href="/operator_ui/templates/decision_traces.html" className="block px-4 py-3 text-xs font-semibold text-neutral uppercase tracking-wider hover:bg-gray-50 hover:text-primary transition-colors border-l-3 border-transparent hover:border-gray-200">
            Decision Traces
          </a>
          <a href="/operator_ui/templates/settings.html" className="block px-4 py-3 text-xs font-semibold text-neutral uppercase tracking-wider hover:bg-gray-50 hover:text-primary transition-colors border-l-3 border-transparent hover:border-gray-200">
            Settings
          </a>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="border-b-2 border-dashed border-gray-200 px-6 py-4 bg-white flex justify-between items-center">
          <h1 className="text-base font-bold uppercase tracking-wider text-primary">Analytics Dashboard</h1>
          <button
            onClick={onRefresh}
            className="flex items-center gap-2 bg-primary text-white px-4 py-2 text-xs font-semibold uppercase tracking-wider hover:bg-blue-900 transition-colors"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
          {/* Summary Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            <div className="bg-white border border-gray-200 p-5">
              <div className="text-xs font-semibold text-neutral uppercase tracking-wider mb-2">Total Users</div>
              <div className="text-3xl font-bold text-gray-900">{data.summary.total_users}</div>
            </div>
            
            <ActiveUsersCard 
              active7d={data.summary.active_users_7d}
              active30d={data.summary.active_users_30d}
            />
            
            <div className="bg-white border border-gray-200 p-5">
              <div className="text-xs font-semibold text-neutral uppercase tracking-wider mb-2">Recommendations</div>
              <div className="text-3xl font-bold text-gray-900">{data.summary.total_recommendations}</div>
            </div>
          </div>

          {/* Safety Indicators */}
          <SafetyIndicatorsPanel 
            overrideRate={data.summary.override_rate}
            guardrailsPassRate={data.summary.guardrails_pass_rate}
            flaggedUsersCount={data.summary.flagged_users_count}
          />

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <PersonaDistributionChart distribution={data.personas.current_distribution} />
            <PersonaTrendsChart weeklyHistory={data.personas.weekly_history} />
          </div>

          {/* Success Metrics Table */}
          <SuccessMetricsTable metricsByPersona={data.success_metrics.by_persona} />
        </div>
      </main>
    </div>
  )
}






