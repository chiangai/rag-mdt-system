export type MobileRoute = 'ai' | 'me' | 'check-in' | 'timeline' | 'care-plan'

export const MOBILE_TABS = [
  { id: 'ai', label: 'HerCare', icon: '✦' },
  { id: 'me', label: '我的', icon: '◉' },
] as const

export function normalizeMobileRoute(route: string): 'ai' | 'me' {
  return route === 'me' || route === 'check-in' || route === 'timeline' || route === 'care-plan' ? 'me' : 'ai'
}

export function contentRoute(route: string): MobileRoute {
  return route === 'check-in' || route === 'timeline' || route === 'care-plan' || route === 'me' ? route : 'ai'
}
