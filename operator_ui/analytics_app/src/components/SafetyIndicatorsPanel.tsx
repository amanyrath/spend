import { Shield, AlertTriangle, CheckCircle } from 'lucide-react'

interface SafetyIndicatorsPanelProps {
  overrideRate: number
  guardrailsPassRate: number
  flaggedUsersCount: number
}

export function SafetyIndicatorsPanel({ 
  overrideRate, 
  guardrailsPassRate, 
  flaggedUsersCount 
}: SafetyIndicatorsPanelProps) {
  const overrideStatus = overrideRate > 0.05 ? 'warning' : 'success'
  const guardrailsStatus = guardrailsPassRate < 0.95 ? 'warning' : 'success'
  const flaggedStatus = flaggedUsersCount > 0 ? 'warning' : 'success'

  return (
    <div className="bg-white border border-gray-200 p-6 mb-6">
      <div className="mb-5 pb-3 border-b border-dashed border-gray-200">
        <h3 className="text-sm font-bold uppercase tracking-wide text-gray-900 flex items-center gap-2">
          <Shield size={16} className="text-primary" />
          Safety Indicators
        </h3>
        <p className="text-xs text-neutral mt-1">
          Recommendation quality and safety metrics
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Override Rate */}
        <div className="flex items-start gap-3">
          {overrideStatus === 'success' ? (
            <CheckCircle size={20} className="text-success mt-0.5" />
          ) : (
            <AlertTriangle size={20} className="text-warning mt-0.5" />
          )}
          <div>
            <div className="text-xs font-semibold text-neutral uppercase tracking-wider">Override Rate</div>
            <div className={`text-2xl font-bold ${overrideStatus === 'success' ? 'text-success' : 'text-warning'}`}>
              {(overrideRate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-neutral mt-1">
              Target: &lt; 5%
            </div>
          </div>
        </div>

        {/* Guardrails Pass Rate */}
        <div className="flex items-start gap-3">
          {guardrailsStatus === 'success' ? (
            <CheckCircle size={20} className="text-success mt-0.5" />
          ) : (
            <AlertTriangle size={20} className="text-warning mt-0.5" />
          )}
          <div>
            <div className="text-xs font-semibold text-neutral uppercase tracking-wider">Guardrails Pass</div>
            <div className={`text-2xl font-bold ${guardrailsStatus === 'success' ? 'text-success' : 'text-warning'}`}>
              {(guardrailsPassRate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-neutral mt-1">
              Target: &gt; 95%
            </div>
          </div>
        </div>

        {/* Flagged Users */}
        <div className="flex items-start gap-3">
          {flaggedStatus === 'success' ? (
            <CheckCircle size={20} className="text-success mt-0.5" />
          ) : (
            <AlertTriangle size={20} className="text-warning mt-0.5" />
          )}
          <div>
            <div className="text-xs font-semibold text-neutral uppercase tracking-wider">Flagged Users</div>
            <div className={`text-2xl font-bold ${flaggedStatus === 'success' ? 'text-gray-900' : 'text-warning'}`}>
              {flaggedUsersCount}
            </div>
            <div className="text-xs text-neutral mt-1">
              Requiring review
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}






