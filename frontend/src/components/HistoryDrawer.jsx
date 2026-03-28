/**
 * HistoryDrawer — 从右侧滑出的历史会诊记录抽屉
 * 点击某条记录可拉取完整报告并显示摘要
 */
import { useState, useEffect, useCallback } from 'react'

const API_BASE = '/api/v1'

function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

function RiskBadge({ level }) {
  const colors = {
    '极高': 'bg-red-100 text-red-700',
    '高': 'bg-orange-100 text-orange-700',
    '中': 'bg-yellow-100 text-yellow-700',
    '低': 'bg-green-100 text-green-700',
  }
  return (
    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${colors[level] || 'bg-gray-100 text-gray-600'}`}>
      {level}
    </span>
  )
}

function RecordDetail({ record, onClose }) {
  const report = record?.report
  if (!report) return (
    <div className="p-6 text-sm text-gray-500 text-center mt-10">暂无报告数据</div>
  )

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-200 flex-shrink-0">
        <button onClick={onClose}
          className="w-7 h-7 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-500 transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <p className="text-xs text-gray-400 font-mono">#{record.consultation_id}</p>
          <p className="text-[11px] text-gray-400">{formatDate(record.created_at)}</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {/* Complaint */}
        <div className="bg-blue-50 rounded-xl p-3 border border-blue-100">
          <p className="text-[11px] font-bold text-blue-600 mb-1">患者主诉</p>
          <p className="text-sm text-gray-800 leading-relaxed">{record.complaint}</p>
        </div>

        {/* Risk assessment */}
        {report.risk_assessment && (
          <div>
            <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">风险评估</p>
            <div className="flex gap-3">
              {Object.entries(report.risk_assessment).map(([k, v]) => (
                <div key={k} className="flex items-center gap-1.5">
                  <span className="text-xs text-gray-500">{k === 'maternal' ? '母体' : k === 'fetal' ? '胎儿' : k}：</span>
                  <RiskBadge level={v} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        {report.consultation_summary && (
          <div>
            <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">会诊摘要</p>
            <p className="text-sm text-gray-700 leading-relaxed bg-white rounded-xl p-3 border border-gray-100">
              {report.consultation_summary}
            </p>
          </div>
        )}

        {/* Safety alerts */}
        {report.safety_alerts?.length > 0 && (
          <div>
            <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">安全警示</p>
            <div className="space-y-1.5">
              {report.safety_alerts.map((alert, i) => (
                <div key={i} className="bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                  <p className="text-xs font-semibold text-red-700">{alert.detail}</p>
                  {alert.suggestion && <p className="text-[11px] text-red-500 mt-0.5">{alert.suggestion}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {report.recommendations?.length > 0 && (
          <div>
            <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">诊疗建议</p>
            <div className="space-y-1.5">
              {report.recommendations.map((rec, i) => (
                <div key={i} className="flex gap-2 text-sm text-gray-700 bg-white rounded-lg px-3 py-2 border border-gray-100">
                  <span className="text-[10px] font-bold text-gray-400 mt-0.5 flex-shrink-0">{rec.department}</span>
                  <span className="flex-1 text-[12px]">{rec.content}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Follow-up */}
        {report.follow_up_plan && (
          <div>
            <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">随访计划</p>
            <p className="text-sm text-gray-700 bg-white rounded-xl p-3 border border-gray-100">{report.follow_up_plan}</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default function HistoryDrawer({ open, onClose }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const fetchList = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/consults?limit=50`)
      const data = await res.json()
      setItems(data.items || [])
    } catch {
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (open) {
      setSelected(null)
      fetchList()
    }
  }, [open, fetchList])

  const openDetail = async (item) => {
    setDetailLoading(true)
    try {
      const res = await fetch(`${API_BASE}/consult/${item.consultation_id}`)
      const data = await res.json()
      setSelected({ ...item, report: data.report, created_at: data.trace?.[0]?.timestamp || item.created_at })
    } catch {
      setSelected({ ...item, report: null })
    } finally {
      setDetailLoading(false)
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/20 backdrop-blur-[2px] z-40 transition-opacity duration-300 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div className={`fixed top-0 right-0 h-full w-[390px] bg-white z-50 shadow-2xl flex flex-col transition-transform duration-300 ease-out ${open ? 'translate-x-0' : 'translate-x-full'}`}>

        {selected ? (
          detailLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="w-8 h-8 rounded-full border-4 border-blue-200 border-t-blue-600 animate-spin" />
            </div>
          ) : (
            <RecordDetail record={selected} onClose={() => setSelected(null)} />
          )
        ) : (
          <>
            {/* List header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 flex-shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h2 className="text-sm font-bold text-gray-800">历史会诊记录</h2>
              </div>
              <button onClick={onClose}
                className="w-7 h-7 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-400 transition-colors">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* List body */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center h-40">
                  <div className="w-8 h-8 rounded-full border-4 border-blue-200 border-t-blue-600 animate-spin" />
                </div>
              ) : items.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-60 text-gray-400">
                  <svg className="w-12 h-12 mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-sm">暂无历史记录</p>
                </div>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {items.map((item) => (
                    <li key={item.consultation_id}>
                      <button
                        onClick={() => openDetail(item)}
                        className="w-full text-left px-5 py-3.5 hover:bg-gray-50 active:bg-gray-100 transition-colors group"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm text-gray-800 leading-snug line-clamp-2 group-hover:text-blue-700 transition-colors flex-1">
                            {item.complaint}
                          </p>
                          <svg className="w-4 h-4 text-gray-300 group-hover:text-blue-400 flex-shrink-0 mt-0.5 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className="text-[10px] font-mono text-gray-400">#{item.consultation_id}</span>
                          <span className="text-[10px] text-gray-400">{formatDate(item.created_at)}</span>
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
      </div>
    </>
  )
}
