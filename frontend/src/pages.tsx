import { FormEvent, type ReactNode, useEffect, useRef, useState } from 'react'
import { api } from './api'
import type { CarePlan, ChatEvent, CheckIn, HomeData, Profile, TimelineEvent } from './api/types'

const toMessage = (error: unknown) => error instanceof Error ? error.message : '暂时无法加载，请稍后重试。'

function useResource<T>(loader: () => Promise<T>) {
  const [data, setData] = useState<T>()
  const [error, setError] = useState<string>()
  const [loading, setLoading] = useState(true)
  const loaderRef = useRef(loader)
  useEffect(() => {
    let active = true
    loaderRef.current().then(
      (value) => { if (active) setData(value) },
      (reason) => { if (active) setError(toMessage(reason)) },
    ).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])
  return { data, error, loading, setData }
}

function PageHeading({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return <div className="page-heading"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{children}</div>
}

function LoadState({ loading, error }: { loading: boolean; error?: string }) {
  if (loading) return <p className="status" role="status">正在加载…</p>
  if (error) return <p className="status error" role="alert">{error}</p>
  return null
}

export function HomePage({ onAsk }: { onAsk: () => void }) {
  const profile = useResource<Profile>(() => api.getProfile())
  const home = useResource<HomeData>(() => api.getHome())
  return <section className="page-stack">
    <PageHeading eyebrow="你的连续照护空间" title={profile.data ? `${profile.data.name}，${home.data?.greeting ?? ''}` : '欢迎来到 HerCare'}>
      <p>{profile.data ? `孕 ${profile.data.pregnancyWeek} 周 · ${profile.data.careTeam}` : '把今天的感受、疑问和照护计划放在同一个地方。'}</p>
    </PageHeading>
    <LoadState loading={profile.loading || home.loading} error={profile.error ?? home.error} />
    {home.data && <>
      <div className="hero-card">
        <div><p className="eyebrow">下一次安排</p><h2>{home.data.nextAppointment}</h2><p>准备好问题，和医生一起做决定。</p></div>
        <a className="button secondary" href="#/care-plan">查看照护计划</a>
      </div>
      <div className="card-grid three">
        {home.data.focus.map((item, index) => <article className="card" key={item}><span className="step-number">0{index + 1}</span><h2>{item}</h2><p>{index === 0 ? '用一分钟完成签到，让变化有迹可循。' : index === 1 ? '把需要咨询的内容提前写下。' : '获得清晰、谨慎的健康信息。'}</p></article>)}
      </div>
      <div className="action-row"><a className="button" href="#/check-in">开始今日签到</a><button className="button text-button" type="button" onClick={onAsk}>问问 HerCare</button></div>
    </>}
  </section>
}

export function CheckInPage() {
  const [week, setWeek] = useState(32)
  const [mood, setMood] = useState('平稳')
  const [symptoms, setSymptoms] = useState('')
  const [note, setNote] = useState('')
  const [result, setResult] = useState<CheckIn>()
  const [error, setError] = useState<string>()
  const [saving, setSaving] = useState(false)

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSaving(true); setError(undefined); setResult(undefined)
    try { setResult(await api.createCheckIn({ week, mood, symptoms, note })) } catch (reason) { setError(toMessage(reason)) } finally { setSaving(false) }
  }
  return <section className="page-stack narrow">
    <PageHeading eyebrow="每日签到" title="给自己一分钟，记录今天的变化"><p>这些信息用于帮助你回顾和准备与医生的沟通。</p></PageHeading>
    <aside className="safety-note" aria-label="紧急情况提示"><strong>如果出现大量出血、持续剧烈腹痛、呼吸困难、晕厥或胎动明显减少，</strong>请立即联系急救服务或前往急诊；不要等待线上回复。</aside>
    <form className="form-card" onSubmit={submit}>
      <label>孕周<input type="number" min="1" max="45" value={week} onChange={(event) => setWeek(Number(event.target.value))} required /></label>
      <fieldset><legend>此刻的心情</legend><div className="choice-row">{['平稳', '疲惫', '焦虑', '开心'].map((item) => <label className="choice" key={item}><input type="radio" name="mood" value={item} checked={mood === item} onChange={() => setMood(item)} />{item}</label>)}</div></fieldset>
      <label>身体感受或症状<textarea value={symptoms} onChange={(event) => setSymptoms(event.target.value)} placeholder="例如：腰酸、睡眠不稳、头痛等" rows={4} /></label>
      <label>想补充的内容（可选）<textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="今天有什么想记下来的？" rows={3} /></label>
      <button className="button" disabled={saving}>{saving ? '正在保存…' : '保存今日签到'}</button>
    </form>
    {error && <p className="status error" role="alert">{error}</p>}
    {result?.risk === 'urgent' && <section className="red-flag" role="alert"><p className="eyebrow">需要立即线下评估</p><h2>你提到的症状可能需要尽快获得医疗帮助</h2><p>请现在联系产科急诊、当地急救服务或你的医疗团队。HerCare 无法评估紧急状况。</p></section>}
    {result && result.risk !== 'urgent' && <p className="status success" role="status">已保存。你可以在时间线里回顾这次记录。</p>}
  </section>
}

export function TimelinePage() {
  const resource = useResource<TimelineEvent[]>(() => api.getTimeline())
  return <section className="page-stack"><PageHeading eyebrow="照护轨迹" title="时间线"><p>把日常记录、计划和产检安排串起来。</p></PageHeading><LoadState {...resource} />
    {resource.data && <ol className="timeline">{resource.data.map((event) => <li key={event.id}><time>{event.date}</time><article className="timeline-card"><span className={`badge ${event.risk ?? event.kind}`}>{event.risk === 'urgent' ? '需关注' : event.kind === 'visit' ? '产检' : event.kind === 'plan' ? '计划' : '签到'}</span><h2>{event.title}</h2><p>{event.description}</p></article></li>)}</ol>}
  </section>
}

export function CarePlanPage() {
  const resource = useResource<CarePlan>(() => api.getCarePlan())
  const [savingId, setSavingId] = useState<string>()
  const toggle = async (itemId: string, complete: boolean) => {
    setSavingId(itemId)
    try {
      const saved = await api.updateCarePlanItem(itemId, complete)
      resource.setData((current) => current ? { ...current, items: current.items.map((item) => item.id === itemId ? saved : item) } : current)
    } finally { setSavingId(undefined) }
  }
  return <section className="page-stack"><PageHeading eyebrow="小步前进" title={resource.data?.title ?? '照护计划'}><p>只关注今天能做的一件事。</p></PageHeading><LoadState {...resource} />
    {resource.data && <div className="plan-list">{resource.data.items.map((item) => <article className={item.complete ? 'plan-item complete' : 'plan-item'} key={item.id}><label><input type="checkbox" checked={item.complete} disabled={savingId === item.id} onChange={(event) => void toggle(item.id, event.target.checked)} /><span><strong>{item.title}</strong><small>{item.detail}</small></span></label><time>{item.due}</time></article>)}</div>}
  </section>
}

export function ProductPage() {
  const resource = useResource(() => api.getProduct())
  return <section className="page-stack"><PageHeading eyebrow="关于产品" title={resource.data?.name ?? 'HerCare'}><p>{resource.data?.subtitle}</p></PageHeading><LoadState {...resource} />
    {resource.data && <div className="card-grid three">{resource.data.bullets.map((bullet) => <article className="card" key={bullet}><span className="large-icon" aria-hidden="true">✦</span><p>{bullet}</p></article>)}</div>}
    <section className="disclaimer"><h2>清晰的边界</h2><p>HerCare 提供健康信息整理与就医沟通支持，不提供诊断、处方或紧急服务。任何不适或担忧，都应优先咨询持证医疗专业人员。</p></section>
  </section>
}

type Message = { id: string; role: 'assistant' | 'user'; content: string }
type Trace = Extract<ChatEvent, { type: 'trace' }>

export function AskHerCare({ debug }: { debug: boolean }) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([{ id: 'welcome', role: 'assistant', content: '你好，我可以帮你整理症状、准备就诊问题，并提供谨慎的健康信息。' }])
  const [traces, setTraces] = useState<Trace[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>()
  const controller = useRef<AbortController | undefined>(undefined)
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const message = input.trim()
    if (!message || loading) return
    const aborter = new AbortController()
    controller.current = aborter
    const assistantId = `assistant-${Date.now()}`
    setInput(''); setError(undefined); setLoading(true)
    setMessages((current) => [...current, { id: `user-${Date.now()}`, role: 'user', content: message }, { id: assistantId, role: 'assistant', content: '' }])
    try {
      for await (const event of api.streamChat(message, aborter.signal)) {
        if (event.type === 'token') setMessages((current) => current.map((item) => item.id === assistantId ? { ...item, content: item.content + event.text } : item))
        if (event.type === 'trace') setTraces((current) => [...current, event])
        if (event.type === 'error') setError(event.message)
      }
    } catch (reason) { if (!(reason instanceof DOMException && reason.name === 'AbortError')) setError(toMessage(reason)) } finally { setLoading(false); controller.current = undefined }
  }
  return <section className="page-stack chat-page"><PageHeading eyebrow="对话支持" title="问问 HerCare"><p>描述你的感受，或把就诊前想问的问题写下来。</p></PageHeading>
    <aside className="safety-note"><strong>紧急情况不使用聊天等待回复。</strong> 大量出血、剧烈腹痛、呼吸困难、晕厥或胎动明显减少，请立即寻求线下急救帮助。</aside>
    <div className="chat-layout"><div className="chat-card" aria-live="polite">{messages.map((message) => <div className={`message ${message.role}`} key={message.id}><span>{message.role === 'user' ? '你' : 'HerCare'}</span><p>{message.content || (loading ? '正在思考…' : '')}</p></div>)}</div>
      {debug && <aside className="trace-panel" aria-label="安全调试追踪"><p className="eyebrow">调试追踪</p><h2>请求阶段</h2>{traces.length ? <ul>{traces.map((trace, index) => <li key={`${trace.traceId}-${index}`}><span>{trace.status === 'completed' ? '完成' : '进行中'}</span>{trace.label}</li>)}</ul> : <p>尚无追踪记录。</p>}<small>仅显示请求阶段，不展示模型推理内容。</small></aside>}
    </div>
    <form className="chat-form" onSubmit={submit}><label className="sr-only" htmlFor="chat-input">输入你的问题</label><textarea id="chat-input" value={input} onChange={(event) => setInput(event.target.value)} placeholder="例如：我想知道产检时该问哪些问题？" rows={3} /><div><button className="button" disabled={loading || !input.trim()}>{loading ? '正在回复…' : '发送问题'}</button>{loading && <button className="button secondary" type="button" onClick={() => controller.current?.abort()}>停止生成</button>}</div></form>
    {error && <p className="status error" role="alert">{error}</p>}
  </section>
}
