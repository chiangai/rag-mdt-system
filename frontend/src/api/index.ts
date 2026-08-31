import { HttpTransport } from './http'
import { MockTransport } from './mock'

const useMock = import.meta.env.VITE_TRANSPORT !== 'http'

export const api = useMock ? new MockTransport() : new HttpTransport()
export const transportMode = useMock ? 'mock' : 'http'
