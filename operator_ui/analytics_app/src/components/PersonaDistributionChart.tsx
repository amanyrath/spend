import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

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

interface PersonaDistributionChartProps {
  distribution: Record<string, number>
}

export function PersonaDistributionChart({ distribution }: PersonaDistributionChartProps) {
  const data = Object.entries(distribution).map(([key, value]) => ({
    name: PERSONA_LABELS[key] || key,
    value: value,
    color: PERSONA_COLORS[key] || '#999'
  }))

  return (
    <div className="bg-white border border-gray-200 p-6">
      <div className="mb-5 pb-3 border-b border-dashed border-gray-200">
        <h3 className="text-sm font-bold uppercase tracking-wide text-gray-900">
          Current Persona Distribution
        </h3>
        <p className="text-xs text-neutral mt-1">
          Snapshot of user personas (30-day window)
        </p>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
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
              fontSize: '10px',
              paddingTop: '16px'
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}






