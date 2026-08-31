import { parseSseStream, type SseEvent } from './sse'
import type {
  CarePlan,
  CarePlanItem,
  ChatEvent,
  CheckIn,
  CheckInDraft,
  HerCareTransport,
  HomeData,
  ProductData,
  Profile,
  TimelineEvent,
} from './types'

type Fetcher = typeof fetch

export class HttpTransport implements HerCareTransport {
  constructor(private readonly baseUrl = '/api/v1', private readonly fetcher: Fetcher = fetch) {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await this.fetcher.call(globalThis, `${this.baseUrl}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
    if (!response.ok) throw new Error(`请求失败（${response.status}）`)
    return response.json() as Promise<T>
  }

  async getProfile() {
    const data = await this.request<{ name: string; postpartum_week: number; concerns?: string[] }>('/profile')
    return { name: data.name, postpartumWeek: data.postpartum_week, careTeam: 'HerCare 产后照护团队' }
  }
  async getHome() {
    const data = await this.request<{ profile: { postpartum_week: number }; quick_actions: string[] }>('/home')
    return { greeting: `产后第 ${data.profile.postpartum_week} 周，今天感觉怎么样？`, focus: data.quick_actions, nextAppointment: '本周 · 产后复查提醒' }
  }
  async getTimeline() {
    const data = await this.request<{ items: Array<{ id: string; occurred_at: string; title: string; detail: string; kind: string }> }>('/timeline')
    return data.items.map((item) => ({ id: item.id, date: item.occurred_at, title: item.title, description: item.detail, kind: item.kind === 'check_in' ? 'check-in' : 'plan' } as TimelineEvent))
  }
  async getCarePlan() {
    const data = await this.request<{ items: Array<{ id: string; title: string; description: string; cadence: string; completed: boolean }> }>('/care-plan')
    return { title: '第 8 周产后恢复计划', items: data.items.map((item) => ({ id: item.id, title: item.title, detail: item.description, due: item.cadence, complete: item.completed })) }
  }
  async getProduct() {
    const data = await this.request<{ items: Array<{ name: string; summary: string; disclaimer: string }> }>('/product')
    const item = data.items[0]
    return { name: item?.name ?? 'HerCare 7日恢复营养餐', subtitle: item?.summary ?? '', bullets: item ? [item.disclaimer] : [] }
  }

  createCheckIn(draft: CheckInDraft) {
    return this.request<CheckIn>('/check-ins', { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify(draft) })
  }

  updateCarePlanItem(itemId: string, complete: boolean) {
    return this.request<CarePlanItem>(`/care-plan/items/${encodeURIComponent(itemId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ completed: complete }),
    })
  }

  async *streamChat(message: string, signal: AbortSignal): AsyncGenerator<ChatEvent> {
    const response = await this.fetcher.call(globalThis, `${this.baseUrl}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ message, client_turn_id: crypto.randomUUID() }),
      signal,
    })
    if (!response.ok) throw new Error(`对话请求失败（${response.status}）`)
    if (!response.body) throw new Error('服务器未返回流式响应')

    const events: ChatEvent[] = []
    let finished = false
    let failure: unknown
    let wake: (() => void) | undefined
    const notify = () => {
      wake?.()
      wake = undefined
    }
    const parsing = parseSseStream(response.body, (event) => {
      const mapped = mapEvent(event)
      if (mapped) {
        events.push(mapped)
        notify()
      }
    }).then(
      () => { finished = true; notify() },
      (error) => { failure = error; finished = true; notify() },
    )

    while (!finished || events.length) {
      if (events.length) {
        yield events.shift() as ChatEvent
      } else {
        await new Promise<void>((resolve) => { wake = resolve })
      }
    }
    await parsing
    if (failure) throw failure
  }
}

function mapEvent(event: SseEvent): ChatEvent | undefined {
  const data = event.data as Record<string, unknown>
  if (event.event === 'message.delta' && typeof data?.text === 'string') return { type: 'token', text: data.text }
  if (event.event === 'message.start' && typeof data?.trace_id === 'string') return { type: 'trace', traceId: data.trace_id, label: typeof data.route === 'string' ? data.route : 'routing', status: 'started' }
  if (event.event === 'message.completed' && typeof data?.conversation_id === 'string') return { type: 'done', conversationId: data.conversation_id }
  if (event.event === 'safety.escalation') return { type: 'error', message: '请尽快联系医生或急诊评估。' }
  if (event.event === 'error' && typeof data?.message === 'string') return { type: 'error', message: data.message }
  return undefined
}
