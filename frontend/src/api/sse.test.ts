import { describe, expect, it } from 'vitest'
import { parseSseStream } from './sse'

describe('parseSseStream', () => {
  it('reassembles fragmented SSE data events in order', async () => {
    const encoder = new TextEncoder()
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode('event: token\ndata: {"text":"您"}'))
        controller.enqueue(encoder.encode('\n\nevent: token\ndata: {"text":"好"}\n\n'))
        controller.close()
      },
    })

    const events = [] as Array<{ event: string; data: unknown }>
    await parseSseStream(stream, (event) => events.push(event))

    expect(events).toEqual([
      { event: 'token', data: { text: '您' } },
      { event: 'token', data: { text: '好' } },
    ])
  })
})
