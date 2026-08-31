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

const redFlagPattern = /出血|腹痛|胸痛|呼吸困难|晕厥|头痛|视物模糊|胎动.*少/

const profile: Profile = { name: '小禾', postpartumWeek: 8, careTeam: 'HerCare 产后照护团队' }
const home: HomeData = {
  greeting: '产后第 8 周，今天感觉怎么样？',
  focus: ['记录身体变化', '完成今日恢复计划', '有疑问随时提问'],
  nextAppointment: '本周 · 产后复查提醒',
}
const timeline: TimelineEvent[] = [
  { id: 'visit-1', date: '2026-08-28', title: '常规产检', description: '血压与胎心监测结果已记录。', kind: 'visit' },
  { id: 'check-in-1', date: '2026-08-26', title: '每日签到', description: '睡眠一般，轻微腰酸。', kind: 'check-in', risk: 'routine' },
  { id: 'plan-1', date: '2026-08-24', title: '护理计划更新', description: '已加入胎动计数提醒。', kind: 'plan' },
]
const plan: CarePlan = {
  title: '第 32 周照护计划',
  items: [
    { id: 'plan-1', title: '记录胎动', detail: '每天选择固定时间记录 1 小时胎动。', due: '今天', complete: false },
    { id: 'plan-2', title: '准备产检问题', detail: '把不适和疑问写下来，复诊时带给医生。', due: '周五前', complete: false },
    { id: 'plan-3', title: '规律补水与休息', detail: '按医嘱保持均衡饮食与充足睡眠。', due: '本周', complete: true },
  ],
}
const product: ProductData = {
  name: 'HerCare',
  subtitle: '面向孕产期的连续照护助手',
  bullets: ['将每日感受整理为可回顾的记录', '帮助你准备与医生的对话', '在出现紧急信号时提示尽快寻求线下医疗帮助'],
}

const pause = (milliseconds: number, signal: AbortSignal) => new Promise<void>((resolve, reject) => {
  const timer = window.setTimeout(resolve, milliseconds)
  signal.addEventListener('abort', () => {
    window.clearTimeout(timer)
    reject(new DOMException('Request aborted', 'AbortError'))
  }, { once: true })
})

export class MockTransport implements HerCareTransport {
  async getProfile() { return profile }
  async getHome() { return home }
  async getTimeline() { return [...timeline] }
  async getCarePlan() { return { ...plan, items: [...plan.items] } }
  async getProduct() { return product }

  async createCheckIn(draft: CheckInDraft): Promise<CheckIn> {
    const risk = redFlagPattern.test(draft.symptoms) ? 'urgent' : draft.symptoms.trim() ? 'watch' : 'routine'
    const record: CheckIn = {
      ...draft,
      id: `check-in-${Date.now()}`,
      createdAt: new Date().toISOString(),
      risk,
    }
    timeline.unshift({
      id: record.id,
      date: record.createdAt.slice(0, 10),
      title: '每日签到',
      description: draft.symptoms || '已完成今日签到。',
      kind: 'check-in',
      risk,
    })
    return record
  }

  async updateCarePlanItem(itemId: string, complete: boolean): Promise<CarePlanItem> {
    const item = plan.items.find((entry) => entry.id === itemId)
    if (!item) throw new Error('护理计划项目不存在')
    item.complete = complete
    return { ...item }
  }

  async *streamChat(message: string, signal: AbortSignal): AsyncGenerator<ChatEvent> {
    const traceId = `trace-${Date.now()}`
    yield { type: 'trace', traceId, label: '正在整理你的问题', status: 'started' }
    await pause(250, signal)
    const response = `我已收到“${message}”。我可以帮你整理问题和下一步，但不能替代线下医生诊断。`
    for (const text of response.match(/.{1,12}/gu) ?? []) {
      await pause(90, signal)
      yield { type: 'token', text }
    }
    yield { type: 'trace', traceId, label: '已生成安全提示', status: 'completed' }
    yield { type: 'done', conversationId: `conversation-${Date.now()}` }
  }
}
