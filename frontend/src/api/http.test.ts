import { describe, expect, it, vi } from 'vitest'
import { HttpTransport } from './http'

describe('HttpTransport', () => {
  it('posts a chat message and maps streamed token events', async () => {
    const encoder = new TextEncoder()
    const fetcher = vi.fn().mockResolvedValue(new Response(new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: message.delta\ndata: {"text":"已收到"}\n\n'))
        controller.close()
      },
    }), { status: 200 }))
    const api = new HttpTransport('/api/v1', fetcher)
    const aborter = new AbortController()
    const events = [] as string[]

    for await (const event of api.streamChat('你好', aborter.signal)) {
      if (event.type === 'token') events.push(event.text)
    }

    expect(fetcher).toHaveBeenCalledWith('/api/v1/chat/stream', expect.objectContaining({ method: 'POST' }))
    expect(events).toEqual(['已收到'])
  })

  it('yields a token before the response stream closes', async () => {
    const encoder = new TextEncoder()
    let closeStream: () => void = () => {}
    const fetcher = vi.fn().mockResolvedValue(new Response(new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: message.delta\ndata: {"text":"增量"}\n\n'))
        closeStream = () => controller.close()
      },
    }), { status: 200 }))
    const api = new HttpTransport('/api/v1', fetcher)
    const iterator = api.streamChat('你好', new AbortController().signal)
    const next = iterator.next()

    expect(await Promise.race([next, new Promise((resolve) => setTimeout(() => resolve('timeout'), 30))])).toEqual({
      done: false,
      value: { type: 'token', text: '增量' },
    })
    closeStream()
  })
})
