const PERSONA_LABELS: Record<string, string> = {
  high_utilization: 'High Utilization',
  variable_income: 'Variable Income',
  subscription_heavy: 'Subscription Heavy',
  savings_builder: 'Savings Builder',
  general_wellness: 'General Wellness'
}

interface SuccessMetricsTableProps {
  metricsByPersona: Record<string, {
    persona: string
    user_count: number
    avg_recommendations: number
    chat_messages: number
    module_completions: number
    override_rate: number
  }>
}

export function SuccessMetricsTable({ metricsByPersona }: SuccessMetricsTableProps) {
  const personas = ['high_utilization', 'variable_income', 'subscription_heavy', 'savings_builder', 'general_wellness']

  return (
    <div className="bg-white border border-gray-200 p-6">
      <div className="mb-5 pb-3 border-b border-dashed border-gray-200">
        <h3 className="text-sm font-bold uppercase tracking-wide text-gray-900">
          Success Metrics by Persona
        </h3>
        <p className="text-xs text-neutral mt-1">
          Engagement and performance indicators
        </p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b-2 border-gray-200">
              <th className="text-left py-3 px-3 font-semibold text-neutral uppercase tracking-wider">Persona</th>
              <th className="text-left py-3 px-3 font-semibold text-neutral uppercase tracking-wider">Users</th>
              <th className="text-left py-3 px-3 font-semibold text-neutral uppercase tracking-wider">Avg Recs</th>
              <th className="text-left py-3 px-3 font-semibold text-neutral uppercase tracking-wider">Chat Msgs</th>
              <th className="text-left py-3 px-3 font-semibold text-neutral uppercase tracking-wider">Modules</th>
              <th className="text-left py-3 px-3 font-semibold text-neutral uppercase tracking-wider">Override Rate</th>
            </tr>
          </thead>
          <tbody>
            {personas.map((persona) => {
              const metrics = metricsByPersona[persona] || {
                user_count: 0,
                avg_recommendations: 0,
                chat_messages: 0,
                module_completions: 0,
                override_rate: 0
              }
              
              return (
                <tr key={persona} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="py-3 px-3 font-semibold">{PERSONA_LABELS[persona]}</td>
                  <td className="py-3 px-3">{metrics.user_count}</td>
                  <td className="py-3 px-3">{metrics.avg_recommendations.toFixed(1)}</td>
                  <td className="py-3 px-3">{metrics.chat_messages}</td>
                  <td className="py-3 px-3">{metrics.module_completions}</td>
                  <td className="py-3 px-3">{(metrics.override_rate * 100).toFixed(1)}%</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}






