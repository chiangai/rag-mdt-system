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
    const response = await this.fetcher(`${this.baseUrl}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
    if (!response.ok) throw new Error(`请求失败（${response.status}）`)
    return response.json() as Promise<T>
  }

  getProfile() { return this.request<Profile>('/profile') }
  getHome() { return this.request<HomeData>('/home') }
  getTimeline() { return this.request<TimelineEvent[]>('/timeline') }
  getCarePlan() { return this.request<CarePlan>('/care-plan') }
  getProduct() { return this.request<ProductData>('/product') }

  createCheckIn(draft: CheckInDraft) {
    return this.request<CheckIn>('/check-ins', { method: 'POST', body: JSON.stringify(draft) })
  }

  updateCarePlanItem(itemId: string, complete: boolean) {
    return this.request<CarePlanItem>(`/care-plan/items/${encodeURIComponent(itemId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ complete }),
    })
  }

  async *streamChat(message: string, signal: AbortSignal): AsyncGenerator<ChatEvent> {
    const response = await this.fetcher(`${this.baseUrl}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ message }),
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
  if (event.event === 'token' && typeof data?.text === 'string') return { type: 'token', text: data.text }
  if (event.event === 'trace' && typeof data?.traceId === 'string' && typeof data?.label === 'string') {
    return { type: 'trace', traceId: data.traceId, label: data.label, status: data.status === 'completed' ? 'completed' : 'started' }
  }
  if (event.event === 'done' && typeof data?.conversationId === 'string') return { type: 'done', conversationId: data.conversationId }
  if (event.event === 'error' && typeof data?.message === 'string') return { type: 'error', message: data.message }
  return undefined
}
