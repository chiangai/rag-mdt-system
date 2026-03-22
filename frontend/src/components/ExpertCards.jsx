const DEPT_META = {
  obstetrics:     { label: '产科', color: 'border-pink-400 bg-gradient-to-br from-white to-pink-50', badge: 'bg-pink-100 text-pink-700 border border-pink-200' },
  endocrinology:  { label: '内分泌科', color: 'border-amber-400 bg-gradient-to-br from-white to-amber-50', badge: 'bg-amber-100 text-amber-700 border border-amber-200' },
  cardiology:     { label: '心内科', color: 'border-red-400 bg-gradient-to-br from-white to-red-50', badge: 'bg-red-100 text-red-700 border border-red-200' },
  nephrology:     { label: '肾内科', color: 'border-purple-400 bg-gradient-to-br from-white to-purple-50', badge: 'bg-purple-100 text-purple-700 border border-purple-200' },
}

function RiskBadge({ level }) {
  const colors = {
    '低': 'bg-green-100 text-green-700 border-green-200',
    '中': 'bg-yellow-100 text-yellow-700 border-yellow-200',
    '高': 'bg-orange-100 text-orange-700 border-orange-200',
    '极高': 'bg-red-100 text-red-700 border-red-200',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium border shadow-sm ${colors[level] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
      {level}
    </span>
  )
}

function ExpertCard({ deptKey, opinion }) {
  const meta = DEPT_META[deptKey] || { label: deptKey, color: 'border-gray-300 bg-gradient-to-br from-white to-gray-50', badge: 'bg-gray-100 text-gray-600 border-gray-200' }

  if (opinion?.error) {
    return (
      <div className="rounded-xl border-l-4 border border-red-200 border-l-red-400 bg-gradient-to-br from-white to-red-50 p-5 shadow-sm">
        <h4 className="font-semibold text-sm text-red-700">{meta.label}</h4>
        <p className="text-xs text-red-600 mt-1">智能体执行失败: {opinion.error}</p>
      </div>
    )
  }

  return (
    <div className={`rounded-xl border-l-4 border border-[#e2e8f0] ${meta.color} p-5 space-y-4 shadow-sm hover:shadow-md transition-shadow`}>
      <div className="flex items-center justify-between border-b border-black/5 pb-3">
        <h4 className="font-bold text-sm text-gray-800 flex items-center gap-2">
          {opinion?.department || meta.label}
        </h4>
        <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-medium ${meta.badge} shadow-sm`}>
          {meta.label}
        </span>
      </div>

      {/* Risk assessment */}
      <div className="flex gap-5 text-xs bg-white/50 p-2.5 rounded-lg border border-black/5">
        {opinion?.maternal_risk && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 font-medium">母体风险:</span>
            <RiskBadge level={opinion.maternal_risk.level} />
          </div>
        )}
        {opinion?.fetal_risk && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 font-medium">胎儿风险:</span>
            <RiskBadge level={opinion.fetal_risk.level} />
          </div>
        )}
      </div>

      {/* Recommendations */}
      {opinion?.recommendations?.length > 0 && (
        <div>
          <p className="text-xs font-bold text-gray-700 mb-2 flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            诊疗建议
          </p>
          <ul className="text-xs text-gray-700 space-y-1.5 pl-1">
            {opinion.recommendations.map((r, i) => (
              <li key={i} className="flex gap-2 leading-relaxed">
                <span className="text-blue-400 flex-shrink-0 mt-0.5">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Medications */}
      {opinion?.medications?.length > 0 && (
        <div className="flex flex-wrap gap-2 items-center pt-1">
          <span className="text-xs font-bold text-gray-700 flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
            用药:
          </span>
          {opinion.medications.map((m, i) => (
            <span key={i} className="text-[11px] px-2.5 py-1 bg-white border border-gray-200 rounded-md shadow-sm text-gray-700 font-medium">
              {m}
            </span>
          ))}
        </div>
      )}

      {/* Monitoring */}
      {opinion?.monitoring_plan?.length > 0 && (
        <div className="pt-1">
          <p className="text-xs font-bold text-gray-700 mb-2 flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
            监测计划
          </p>
          <ul className="text-xs text-gray-700 space-y-1.5 pl-1">
            {opinion.monitoring_plan.map((m, i) => (
              <li key={i} className="flex gap-2 leading-relaxed">
                <span className="text-purple-400 flex-shrink-0 mt-0.5">•</span>
                <span>{m}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default function ExpertCards({ events }) {
  const opinions = {}

  for (const ev of events) {
    if (ev.data?.expert_opinions) {
      Object.assign(opinions, ev.data.expert_opinions)
    }
  }

  if (Object.keys(opinions).length === 0) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-1.5 h-4 bg-blue-500 rounded-full"></div>
        <h3 className="text-base font-bold text-gray-800">各科室专家意见</h3>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        {Object.entries(opinions).map(([dept, opinion]) => (
          <ExpertCard key={dept} deptKey={dept} opinion={opinion} />
        ))}
      </div>
    </div>
  )
}
