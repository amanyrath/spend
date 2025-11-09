import { Users, TrendingUp } from 'lucide-react'

interface ActiveUsersCardProps {
  active7d: number
  active30d: number
}

export function ActiveUsersCard({ active7d, active30d }: ActiveUsersCardProps) {
  return (
    <div className="bg-white border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-2">
        <Users size={14} className="text-success" />
        <div className="text-xs font-semibold text-neutral uppercase tracking-wider">Active Users (7d)</div>
      </div>
      <div className="text-3xl font-bold text-success">{active7d}</div>
      <div className="flex items-center gap-1 text-xs text-neutral mt-1">
        <TrendingUp size={12} />
        {active30d} in 30 days
      </div>
    </div>
  )
}






