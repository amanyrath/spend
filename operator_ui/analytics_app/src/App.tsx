import { useState, useEffect } from 'react'
import { AnalyticsDashboard } from './components/AnalyticsDashboard'

// API Configuration
const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://spendsense-api.vercel.app'

export interface AnalyticsData {
  summary: {
    total_users: number
    active_users_7d: number
    active_users_30d: number
    total_recommendations: number
    override_rate: number
    guardrails_pass_rate: number
    flagged_users_count: number
  }
  personas: {
    current_distribution: Record<string, number>
    weekly_history: Array<{
      week_start: string
      high_utilization: number
      variable_income: number
      subscription_heavy: number
      savings_builder: number
      general_wellness: number
    }>
  }
  success_metrics: {
    by_persona: Record<string, {
      persona: string
      user_count: number
      avg_recommendations: number
      chat_messages: number
      module_completions: number
      override_rate: number
    }>
  }
}

function App() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAnalytics = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/analytics/overview`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const analyticsData = await response.json()
      setData(analyticsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
      console.error('Error loading analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAnalytics()
  }, [])

  return (
    <div className="min-h-screen bg-white">
      <AnalyticsDashboard 
        data={data}
        loading={loading}
        error={error}
        onRefresh={loadAnalytics}
      />
    </div>
  )
}

export default App






