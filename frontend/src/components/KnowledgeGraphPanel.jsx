/**
 * KnowledgeGraphPanel — 展示图谱查询智能体从 Neo4j 检索到的知识
 * graph_knowledge 结构：
 *   { vector_search_results: [{entity, type, result}], custom_queries: [...], <template>: [...] }
 */

function TagBadge({ label, color = 'blue' }) {
  const colors = {
    blue:   'bg-blue-50 text-blue-700 border-blue-200',
    green:  'bg-green-50 text-green-700 border-green-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    amber:  'bg-amber-50 text-amber-700 border-amber-200',
  }
  return (
    <span className={`inline-block text-[11px] font-medium px-2 py-0.5 rounded-full border ${colors[color]}`}>
      {label}
    </span>
  )
}

/**
 * 将后端返回的 result 字符串（Python repr 格式）解析为可读条目。
 * 例如: "[{'name': '妊娠期糖尿病', 'score': 0.92, 'category': '疾病'}, ...]"
 */
function parseResultString(raw) {
  try {
    // 尝试 JSON 解析（result 有时是 JSON 格式）
    return JSON.parse(raw)
  } catch {
    // 回退：使用正则提取每对 key/value
    const items = []
    const objPattern = /\{([^}]+)\}/g
    let match
    while ((match = objPattern.exec(raw)) !== null) {
      const obj = {}
      const kvPattern = /'(\w+)':\s*('([^']*)'|([\d.]+)|(True|False|None))/g
      let kv
      while ((kv = kvPattern.exec(match[1])) !== null) {
        const key = kv[1]
        const val = kv[3] !== undefined ? kv[3]
                  : kv[4] !== undefined ? Number(kv[4])
                  : kv[5]
        obj[key] = val
      }
      if (Object.keys(obj).length) items.push(obj)
    }
    return items.length ? items : null
  }
}

function VectorResultItem({ item }) {
  const results = parseResultString(item.result)
  return (
    <div className="mb-3">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-xs font-semibold text-gray-600">检索词：</span>
        <span className="text-xs font-bold text-blue-700">{item.entity}</span>
        <TagBadge label="向量检索" color="blue" />
      </div>
      {results ? (
        <div className="space-y-1">
          {results.map((r, i) => (
            <div key={i} className="flex items-center justify-between bg-white rounded-lg px-3 py-1.5 border border-gray-100 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-medium text-gray-800">{r.name}</span>
                {r.category && <TagBadge label={r.category} color="purple" />}
              </div>
              {r.score !== undefined && (
                <span className="text-[11px] text-gray-400 font-mono">
                  相似度 {(r.score * 100).toFixed(1)}%
                </span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2 font-mono break-all">{item.result}</p>
      )}
    </div>
  )
}

function TemplateResultItem({ entry, templateName }) {
  const results = parseResultString(entry.result)
  const params = entry.params || {}
  return (
    <div className="mb-3">
      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
        <TagBadge label={`模板：${templateName}`} color="green" />
        {Object.values(params).flat().map((p, i) => (
          <span key={i} className="text-xs font-bold text-gray-700">{p}</span>
        ))}
      </div>
      {results ? (
        <div className="space-y-1">
          {results.slice(0, 8).map((r, i) => (
            <div key={i} className="flex items-start gap-2 bg-white rounded-lg px-3 py-1.5 border border-gray-100 text-[12px] text-gray-700">
              {typeof r === 'object'
                ? Object.entries(r).map(([k, v]) => (
                    <span key={k}><span className="text-gray-400">{k}:</span> {String(v).slice(0, 40)}</span>
                  ))
                : String(r)}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2 font-mono break-all">
          {entry.result?.slice(0, 300)}
        </p>
      )}
    </div>
  )
}

export default function KnowledgeGraphPanel({ graphKnowledge }) {
  if (!graphKnowledge || Object.keys(graphKnowledge).length === 0) return null

  const vectorResults = graphKnowledge.vector_search_results || []
  const customQueries = graphKnowledge.custom_queries || []
  const templateKeys = Object.keys(graphKnowledge).filter(
    k => k !== 'vector_search_results' && k !== 'custom_queries'
  )
  const totalItems = vectorResults.length + customQueries.length + templateKeys.length

  return (
    <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/60 to-blue-50/40 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-indigo-100 bg-white/60">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-sm">
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <h3 className="text-sm font-bold text-gray-800">知识图谱检索结果</h3>
          <p className="text-[11px] text-gray-500">共命中 {totalItems} 个查询，来自 Neo4j 医学知识图谱</p>
        </div>
      </div>

      <div className="px-5 py-4 space-y-5">
        {/* Vector search results */}
        {vectorResults.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
              <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider">向量语义检索</h4>
            </div>
            {vectorResults.map((item, i) => (
              <VectorResultItem key={i} item={item} />
            ))}
          </section>
        )}

        {/* Template query results */}
        {templateKeys.map(key => (
          <section key={key}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
              <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider">精准图谱查询</h4>
            </div>
            {(graphKnowledge[key] || []).map((entry, i) => (
              <TemplateResultItem key={i} entry={entry} templateName={key} />
            ))}
          </section>
        ))}

        {/* Custom Cypher results */}
        {customQueries.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500"></div>
              <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider">自定义 Cypher 查询</h4>
            </div>
            {customQueries.map((item, i) => (
              <div key={i} className="mb-2 text-xs text-gray-600 bg-white rounded-lg px-3 py-2 border border-gray-100">
                <p className="font-mono text-gray-400 mb-1">{item.query?.slice(0, 80)}</p>
                <p className="break-all">{item.result?.slice(0, 200)}</p>
              </div>
            ))}
          </section>
        )}
      </div>
    </div>
  )
}
