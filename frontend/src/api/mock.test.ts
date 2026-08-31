import { describe, expect, it } from 'vitest'
import { MockTransport } from './mock'

describe('MockTransport', () => {
  it('creates an urgent check-in for red-flag symptoms', async () => {
    const api = new MockTransport()

    const checkIn = await api.createCheckIn({
      week: 32,
      mood: '焦虑',
      symptoms: '持续腹痛并有阴道出血',
      note: '',
    })

    expect(checkIn.risk).toBe('urgent')
    expect(checkIn.id).toMatch(/^check-in-/)
  })
})
