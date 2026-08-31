import { FormEvent, useEffect, useRef, useState } from 'react'
import { api } from './api'
import type { CarePlan, ChatEvent, CheckIn, HomeData, Profile, TimelineEvent } from './api/types'
import type { MobileRoute } from './mobile-navigation'

const toMessage = (error: unknown) => error instanceof Error ? error.message : '暂时无法加载，请稍后重试。'

function useResource<T>(loader: () => Promise<T>) {
  const [data, setData] = useState<T>()
  const [error, setError] = useState<string>()
  useEffect(() => { loader().then(setData).catch((reason) => setError(toMessage(reason))) }, [])
  return { data, error, setData }
}

function Back({ onBack, title }: { onBack: () => void; title: string }) {
  return <div className="subpage-head"><button type="button" onClick={onBack} aria-label="返回">‹</button><h1>{title}</h1></div>
}

type Message = { id: string; role: 'assistant' | 'user'; content: string }
type Trace = Extract<ChatEvent, { type: 'trace' }>

export function AiHomePage({ debug, onCheckIn }: { debug: boolean; onCheckIn: () => void }) {
  const profile = useResource<Profile>(() => api.getProfile())
  const home = useResource<HomeData>(() => api.getHome())
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([{ id: 'welcome', role: 'assistant', content: '早上好，小禾。今天身体和心情感觉怎么样？' }])
  const [traces, setTraces] = useState<Trace[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>()
  const controller = useRef<AbortController>()
  const prompts = ['昨晚睡不好', '我很疲惫', '恢复得正常吗', '帮我整理就诊问题']

  const send = async (event?: FormEvent<HTMLFormElement>, preset?: string) => {
    event?.preventDefault()
    const message = (preset ?? input).trim()
    if (!message || loading) return
    const aborter = new AbortController(); controller.current = aborter
    const assistantId = `assistant-${Date.now()}`
    setInput(''); setLoading(true); setError(undefined)
    setMessages((items) => [...items, { id: `user-${Date.now()}`, role: 'user', content: message }, { id: assistantId, role: 'assistant', content: '' }])
    try {
      for await (const event of api.streamChat(message, aborter.signal)) {
        if (event.type === 'token') setMessages((items) => items.map((item) => item.id === assistantId ? { ...item, content: item.content + event.text } : item))
        if (event.type === 'trace') setTraces((items) => [...items, event])
        if (event.type === 'error') setError(event.message)
      }
    } catch (reason) { if (!(reason instanceof DOMException && reason.name === 'AbortError')) setError(toMessage(reason)) } finally { setLoading(false); controller.current = undefined }
  }

  return <section className="ai-home">
    <p className="soft-label">你的产后照护助手</p>
    <h1>{profile.data ? `${profile.data.name}，今天想聊什么？` : '今天想聊什么？'}</h1>
    <p className="subcopy">我会结合你的记录，帮你整理变化、准备问题和下一步行动。</p>
    <div className="prompt-row">{prompts.map((prompt) => <button type="button" key={prompt} onClick={() => void send(undefined, prompt)}>{prompt}</button>)}</div>
    <button className="checkin-card" type="button" onClick={onCheckIn}>
      <span>今日状态</span><strong>{home.data?.focus[0] ?? '用一分钟记录今天的恢复'}</strong><small>记录一下 →</small>
    </button>
    <div className="conversation" aria-live="polite">{messages.map((message) => <article className={`bubble ${message.role}`} key={message.id}><span>{message.role === 'user' ? '你' : 'HerCare'}</span><p>{message.content || (loading ? '正在整理…' : '')}</p></article>)}</div>
    {debug && <div className="trace-mini"><strong>Developer Trace</strong>{traces.map((trace, index) => <span key={`${trace.traceId}-${index}`}>{trace.label}</span>)}</div>}
    {error && <p className="inline-error" role="alert">{error}</p>}
    <form className="composer" onSubmit={send}><label className="sr-only" htmlFor="ai-input">输入你的感受或问题</label><textarea id="ai-input" rows={1} value={input} onChange={(event) => setInput(event.target.value)} placeholder="告诉 HerCare 你现在的感受…" /><button type="button" className="voice-button" aria-label="语音输入（演示）">⌁</button><button type="submit" aria-label="发送" disabled={!input.trim() || loading}>↑</button>{loading && <button type="button" className="stop" onClick={() => controller.current?.abort()}>停止</button>}</form>
    <p className="safety-inline">大量出血、剧烈头痛或视物异常等紧急情况，请立即线下就医。</p>
  </section>
}

export function MyPage({ onNavigate }: { onNavigate: (route: MobileRoute) => void }) {
  const profile = useResource<Profile>(() => api.getProfile())
  const plan = useResource<CarePlan>(() => api.getCarePlan())
  return <section className="my-page">
    <p className="soft-label">我的恢复</p><h1>{profile.data?.name ?? '小禾'}</h1>
    <p className="subcopy">产后第 {profile.data?.postpartumWeek ?? 8} 周 · {profile.data?.careTeam ?? 'HerCare 产后照护团队'}</p>
    <button className="my-summary" type="button" onClick={() => onNavigate('care-plan')}><span>今天的照护计划</span><strong>{plan.data?.items.filter((item) => !item.complete).length ?? 1} 件小事等你完成</strong><small>查看计划 →</small></button>
    <div className="my-list">
      <button type="button" onClick={() => onNavigate('check-in')}><span>✓</span><div><strong>记录今日状态</strong><small>身体、情绪和睡眠</small></div><b>›</b></button>
      <button type="button" onClick={() => onNavigate('timeline')}><span>◷</span><div><strong>恢复记录</strong><small>查看时间线和趋势</small></div><b>›</b></button>
    </div>
  </section>
}

export function CheckInPage({ onBack }: { onBack: () => void }) {
  const [mood, setMood] = useState('平稳'); const [symptoms, setSymptoms] = useState(''); const [result, setResult] = useState<CheckIn>(); const [saving, setSaving] = useState(false)
  const submit = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); setSaving(true); try { setResult(await api.createCheckIn({ week: 8, mood, symptoms, note: '' })) } finally { setSaving(false) } }
  return <section className="subpage"><Back onBack={onBack} title="记录今日状态" /><p>不用填表。告诉我现在的感受，AI 会在对话里继续了解。</p><form className="simple-form" onSubmit={submit}><div className="mood-row">{['平稳', '疲惫', '焦虑', '开心'].map((item) => <button className={mood === item ? 'selected' : ''} type="button" key={item} onClick={() => setMood(item)}>{item}</button>)}</div><textarea rows={5} value={symptoms} onChange={(event) => setSymptoms(event.target.value)} placeholder="例如：昨晚只睡了 5 小时，今天腰有点酸…" /><button className="primary" disabled={saving}>{saving ? '保存中…' : '保存并问问 HerCare'}</button></form>{result?.risk === 'urgent' && <p className="urgent" role="alert">你描述的情况需要立即线下评估，请联系急诊或产科。</p>}{result && result.risk !== 'urgent' && <p className="saved">已记录。回到 AI 页面继续聊聊吧。</p>}</section>
}

export function TimelinePage({ onBack }: { onBack: () => void }) {
  const resource = useResource<TimelineEvent[]>(() => api.getTimeline())
  return <section className="subpage"><Back onBack={onBack} title="恢复记录" />{resource.data?.map((item) => <article className="record" key={item.id}><time>{item.date}</time><strong>{item.title}</strong><p>{item.description}</p></article>)}</section>
}

export function CarePlanPage({ onBack }: { onBack: () => void }) {
  const resource = useResource<CarePlan>(() => api.getCarePlan())
  const toggle = async (id: string, complete: boolean) => { const saved = await api.updateCarePlanItem(id, complete); resource.setData((current) => current ? { ...current, items: current.items.map((item) => item.id === id ? saved : item) } : current) }
  return <section className="subpage"><Back onBack={onBack} title="今日照护计划" /><p>只做今天最重要的一两件事。</p><div className="plan-stack">{resource.data?.items.map((item) => <label key={item.id}><input type="checkbox" checked={item.complete} onChange={(event) => void toggle(item.id, event.target.checked)} /><span><strong>{item.title}</strong><small>{item.detail}</small></span></label>)}</div></section>
}
