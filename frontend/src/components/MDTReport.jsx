function SeverityBadge({ severity }) {
  const colors = {
    '严重': 'bg-gradient-to-b from-red-500 to-red-600 text-white border-red-700 shadow-sm',
    '中等': 'bg-gradient-to-b from-yellow-400 to-yellow-500 text-yellow-900 border-yellow-600 shadow-sm',
    '轻微': 'bg-gradient-to-b from-blue-400 to-blue-500 text-white border-blue-600 shadow-sm',
  }
  return (
    <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold border ${colors[severity] || 'bg-gray-100 text-gray-600 border-gray-300'}`}>
      {severity}
    </span>
  )
}

function PriorityDot({ priority }) {
  const colors = {
    '高': 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]',
    '中': 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.6)]',
    '低': 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]'
  }
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${colors[priority] || 'bg-gray-300'}`} />
}

export default function MDTReport({ report }) {
  if (!report) return null

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-1.5 h-4 bg-emerald-500 rounded-full"></div>
        <h3 className="text-base font-bold text-gray-800">MDT 最终会诊报告</h3>
      </div>

      {/* Summary */}
      <div className="rounded-xl bg-white border border-gray-200 p-5 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-500"></div>
        <p className="text-sm text-gray-800 leading-relaxed font-medium">{report.consultation_summary}</p>

        {report.risk_assessment && (
          <div className="flex gap-6 text-xs mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2">
              <span className="text-gray-500">母体风险评估:</span>
              <span className="font-bold text-gray-800 bg-gray-100 px-2 py-0.5 rounded">{report.risk_assessment.maternal}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">胎儿风险评估:</span>
              <span className="font-bold text-gray-800 bg-gray-100 px-2 py-0.5 rounded">{report.risk_assessment.fetal}</span>
            </div>
          </div>
        )}
      </div>

      {/* Safety alerts */}
      {report.safety_alerts?.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-red-600 uppercase tracking-wider flex items-center gap-1.5">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            安全警告 ({report.safety_alerts.length})
          </h4>
          {report.safety_alerts.map((alert, i) => (
            <div key={i} className="rounded-xl border border-red-200 bg-gradient-to-br from-white to-red-50 p-4 shadow-sm relative overflow-hidden">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-red-500"></div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-red-900">{alert.alert_type}</span>
                <SeverityBadge severity={alert.severity} />
              </div>
              <p className="text-sm text-red-800 leading-relaxed">{alert.detail}</p>
              {alert.suggestion && (
                <div className="mt-3 bg-white/60 rounded-lg p-2.5 border border-red-100">
                  <p className="text-xs text-red-700 font-medium flex items-start gap-1.5">
                    <span className="mt-0.5">💡</span>
                    <span>处理建议: {alert.suggestion}</span>
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Recommendations by department */}
      {report.recommendations?.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>
            综合科室建议
          </h4>
          <div className="grid gap-3">
            {report.recommendations.map((rec, i) => (
              <div key={i} className="flex items-start gap-3 rounded-xl bg-white border border-gray-200 p-4 shadow-sm hover:border-blue-300 transition-colors">
                <div className="mt-1"><PriorityDot priority={rec.priority} /></div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-bold text-gray-800">{rec.department}</span>
                    <span className="text-[10px] text-gray-400 font-medium bg-gray-100 px-2 py-0.5 rounded-full">优先级: {rec.priority}</span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed">{rec.content}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Follow-up plan */}
      {report.follow_up_plan && (
        <div className="rounded-xl bg-gradient-to-br from-[#f0f9ff] to-[#e0f2fe] border border-[#bae6fd] p-5 shadow-sm relative overflow-hidden">
          <div className="absolute right-0 bottom-0 opacity-10 transform translate-x-4 translate-y-4">
            <svg className="w-24 h-24 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          </div>
          <h4 className="text-sm font-bold text-blue-900 mb-2 relative z-10">随访计划</h4>
          <p className="text-sm text-blue-800 leading-relaxed relative z-10">{report.follow_up_plan}</p>
        </div>
      )}

      {/* Disclaimer */}
      {report.disclaimer && (
        <div className="flex items-center justify-center gap-2 pt-4 border-t border-gray-200">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <p className="text-[11px] text-gray-400 font-medium tracking-wide">
            {report.disclaimer}
          </p>
        </div>
      )}
    </div>
  )
}
