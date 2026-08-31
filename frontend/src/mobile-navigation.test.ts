import { describe, expect, it } from 'vitest'
import { MOBILE_TABS, normalizeMobileRoute } from './mobile-navigation'

describe('mobile navigation', () => {
  it('keeps AI and My as the only persistent tabs', () => {
    expect(MOBILE_TABS.map((tab) => tab.id)).toEqual(['ai', 'me'])
  })

  it('groups check-in, timeline and care plan under My', () => {
    expect(normalizeMobileRoute('check-in')).toBe('me')
    expect(normalizeMobileRoute('timeline')).toBe('me')
    expect(normalizeMobileRoute('care-plan')).toBe('me')
  })
})
