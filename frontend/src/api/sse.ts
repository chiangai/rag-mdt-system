export type SseEvent = {
  event: string
  data: unknown
}

export async function parseSseStream(
  stream: ReadableStream<Uint8Array>,
  onEvent: (event: SseEvent) => void,
): Promise<void> {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const emit = (block: string) => {
    const fields = block.split(/\r?\n/)
    const event = fields.find((line) => line.startsWith('event:'))?.slice(6).trim() || 'message'
    const dataText = fields
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trim())
      .join('\n')

    if (!dataText) return
    try {
      onEvent({ event, data: JSON.parse(dataText) })
    } catch {
      onEvent({ event, data: dataText })
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })

    let boundary = buffer.search(/\r?\n\r?\n/)
    while (boundary !== -1) {
      const block = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary).replace(/^\r?\n\r?\n/, '')
      emit(block)
      boundary = buffer.search(/\r?\n\r?\n/)
    }

    if (done) break
  }

  if (buffer.trim()) emit(buffer)
}
