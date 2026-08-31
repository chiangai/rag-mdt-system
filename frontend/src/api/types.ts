export type RiskLevel = 'routine' | 'watch' | 'urgent'

export type Profile = {
  name: string
  postpartumWeek: number
  careTeam: string
}

export type HomeData = {
  greeting: string
  focus: string[]
  nextAppointment: string
}

export type CheckInDraft = {
  week: number
  mood: string
  symptoms: string
  note: string
}

export type CheckIn = CheckInDraft & {
  id: string
  createdAt: string
  risk: RiskLevel
}

export type TimelineEvent = {
  id: string
  date: string
  title: string
  description: string
  kind: 'visit' | 'check-in' | 'plan'
  risk?: RiskLevel
}

export type CarePlanItem = {
  id: string
  title: string
  detail: string
  due: string
  complete: boolean
}

export type CarePlan = {
  title: string
  items: CarePlanItem[]
}

export type ProductData = {
  name: string
  subtitle: string
  bullets: string[]
}

export type ChatEvent =
  | { type: 'token'; text: string }
  | { type: 'trace'; traceId: string; label: string; status: 'started' | 'completed' }
  | { type: 'done'; conversationId: string }
  | { type: 'error'; message: string }

export interface HerCareTransport {
  getProfile(): Promise<Profile>
  getHome(): Promise<HomeData>
  createCheckIn(draft: CheckInDraft): Promise<CheckIn>
  getTimeline(): Promise<TimelineEvent[]>
  getCarePlan(): Promise<CarePlan>
  updateCarePlanItem(itemId: string, complete: boolean): Promise<CarePlanItem>
  getProduct(): Promise<ProductData>
  streamChat(message: string, signal: AbortSignal): AsyncGenerator<ChatEvent>
}
