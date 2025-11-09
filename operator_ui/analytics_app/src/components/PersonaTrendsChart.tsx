import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const PERSONA_COLORS: Record<string, string> = {
  high_utilization: '#ef4444',
  variable_income: '#f59e0b',
  subscription_heavy: '#3b82f6',
  savings_builder: '#10b981',
  general_wellness: '#64748b'
}

const PERSONA_LABELS: Record<string, string> = {
  high_utilization: 'High Utilization',
  variable_income: 'Variable Income',
  subscription_heavy: 'Subscription Heavy',
  savings_builder: 'Savings Builder',
  general_wellness: 'General Wellness'
}

interface PersonaTrendsChartProps {
  weeklyHistory: Array<{
    week_start: string
    high_utilization: number
    variable_income: number
    subscription_heavy: number
    savings_builder: number
    general_wellness: number
  }>
}

export function PersonaTrendsChart({ weeklyHistory }: PersonaTrendsChartProps) {
  return (
    <div className="bg-white border border-gray-200 p-6">
      <div className="mb-5 pb-3 border-b border-dashed border-gray-200">
        <h3 className="text-sm font-bold uppercase tracking-wide text-gray-900">
          Persona Trends (12 Weeks)
        </h3>
        <p className="text-xs text-neutral mt-1">
          Weekly persona distribution over time
        </p>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={weeklyHistory}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="week_start" 
            tick={{ fontFamily: 'JetBrains Mono', fontSize: 9 }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis 
            tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '11px'
            }}
          />
          <Legend 
            wrapperStyle={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '9px',
              paddingTop: '8px'
            }}
          />
          <Line 
            type="monotone" 
            dataKey="high_utilization" 
            stroke={PERSONA_COLORS.high_utilization}
            strokeWidth={2}
            name={PERSONA_LABELS.high_utilization}
            dot={{ r: 3 }}
          />
          <Line 
            type="monotone" 
            dataKey="variable_income" 
            stroke={PERSONA_COLORS.variable_income}
            strokeWidth={2}
            name={PERSONA_LABELS.variable_income}
            dot={{ r: 3 }}
          />
          <Line 
            type="monotone" 
            dataKey="subscription_heavy" 
            stroke={PERSONA_COLORS.subscription_heavy}
            strokeWidth={2}
            name={PERSONA_LABELS.subscription_heavy}
            dot={{ r: 3 }}
          />
          <Line 
            type="monotone" 
            dataKey="savings_builder" 
            stroke={PERSONA_COLORS.savings_builder}
            strokeWidth={2}
            name={PERSONA_LABELS.savings_builder}
            dot={{ r: 3 }}
          />
          <Line 
            type="monotone" 
            dataKey="general_wellness" 
            stroke={PERSONA_COLORS.general_wellness}
            strokeWidth={2}
            name={PERSONA_LABELS.general_wellness}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}






