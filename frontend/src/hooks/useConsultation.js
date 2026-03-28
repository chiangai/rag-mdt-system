import { useState, useCallback, useRef } from 'react'

const API_BASE = '/api/v1'

const AGENT_LABELS = {
  router: '导诊/规划智能体',
  graph_query: '图谱查询智能体',
  obstetrician: '产科专家智能体',
  endocrinologist: '内分泌专家智能体',
  cardiologist: '心内科专家智能体',
  nephrologist: '肾内科专家智能体',
  reviewer: '医疗审查/安全智能体',
  done: '会诊完成',
  error: '系统错误',
}

export function useConsultation() {
  const [status, setStatus] = useState('idle') // idle | loading | streaming | done | error
  const [events, setEvents] = useState([])
  const [report, setReport] = useState(null)
  const [graphKnowledge, setGraphKnowledge] = useState(null)
  const [error, setError] = useState(null)
  const [complaint, setComplaint] = useState('')
  const abortRef = useRef(null)

  const reset = useCallback(() => {
    if (abortRef.current) abortRef.current.abort()
    setStatus('idle')
    setEvents([])
    setReport(null)
    setGraphKnowledge(null)
    setError(null)
    setComplaint('')
  }, [])

  const submitStream = useCallback(async (text) => {
    reset()
    setComplaint(text)
    setStatus('streaming')

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const res = await fetch(`${API_BASE}/consult/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ complaint: text }),
        signal: controller.signal,
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload = JSON.parse(line.slice(6))
            const { node, data } = payload

            const event = {
              node,
              label: AGENT_LABELS[node] || node,
              data,
              timestamp: new Date(),
            }

            setEvents((prev) => [...prev, event])

            // Extract graph knowledge when graph_query_agent fires
            if (node === 'graph_query' && data?.graph_knowledge) {
              setGraphKnowledge(data.graph_knowledge)
            }

            if (node === 'reviewer' && data?.final_report) {
              setReport(data.final_report)
            }
            if (node === 'done') {
              setStatus('done')
            }
            if (node === 'error') {
              setStatus('error')
              setError(data?.error || '未知错误')
            }
          } catch {
            // skip malformed SSE frames
          }
        }
      }

      setStatus((prev) => (prev === 'streaming' ? 'done' : prev))
    } catch (err) {
      if (err.name === 'AbortError') return
      setStatus('error')
      setError(err.message)
    }
  }, [reset])

  const submitSync = useCallback(async (text) => {
    reset()
    setComplaint(text)
    setStatus('loading')

    try {
      const res = await fetch(`${API_BASE}/consult`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ complaint: text }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      if (data.report) setReport(data.report)
      if (data.errors?.length) setError(data.errors.join('; '))
      setStatus('done')
    } catch (err) {
      setStatus('error')
      setError(err.message)
    }
  }, [reset])

  return { status, events, report, graphKnowledge, error, complaint, submitStream, submitSync, reset }
}
