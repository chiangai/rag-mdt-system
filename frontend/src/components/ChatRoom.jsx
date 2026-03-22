import { useEffect, useRef } from 'react'

const AGENTS = {
  user: {
    name: '患者',
    avatar: 'https://api.dicebear.com/7.x/notionists/svg?seed=Felix&backgroundColor=e2e8f0',
    color: 'bg-gradient-to-b from-[#e1f5fe] to-[#cbd5e1]',
    border: 'border-[#94a3b8]',
    align: 'right',
  },
  router: {
    name: '导诊护士',
    avatar: 'https://api.dicebear.com/7.x/notionists/svg?seed=Nurse&backgroundColor=e0e7ff',
    color: 'bg-gradient-to-b from-white to-[#f8fafc]',
    border: 'border-[#cbd5e1]',
    align: 'left',
  },
  graph_query: {
    name: '医学知识库',
    avatar: 'https://api.dicebear.com/7.x/bottts/svg?seed=Knowledge&backgroundColor=cffafe',
    color: 'bg-gradient-to-b from-white to-[#f0fdfa]',
    border: 'border-[#a5f3fc]',
    align: 'left',
  },
  obstetrician: {
    name: '产科主任',
    avatar: 'https://api.dicebear.com/7.x/notionists/svg?seed=Doctor1&backgroundColor=fce7f3',
    color: 'bg-gradient-to-b from-white to-[#fdf2f8]',
    border: 'border-[#fbcfe8]',
    align: 'left',
  },
  endocrinologist: {
    name: '内分泌主任',
    avatar: 'https://api.dicebear.com/7.x/notionists/svg?seed=Doctor2&backgroundColor=fef3c7',
    color: 'bg-gradient-to-b from-white to-[#fffbeb]',
    border: 'border-[#fde68a]',
    align: 'left',
  },
  reviewer: {
    name: '质控/药师',
    avatar: 'https://api.dicebear.com/7.x/notionists/svg?seed=Pharmacist&backgroundColor=d1fae5',
    color: 'bg-gradient-to-b from-white to-[#ecfdf5]',
    border: 'border-[#a7f3d0]',
    align: 'left',
  },
  system: {
    name: '系统',
    avatar: 'https://api.dicebear.com/7.x/shapes/svg?seed=System&backgroundColor=f1f5f9',
    color: 'bg-gray-50',
    border: 'border-gray-200',
    align: 'center',
  }
}

function escapeHtml(str) {
  if (typeof str !== 'string') return ''
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function safeMarkdown(text) {
  const escaped = escapeHtml(text)
  return escaped.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
}

function generateDialogue(event) {
  const { node, data } = event

  if (node === 'router') {
    const depts = data?.required_departments || []
    const deptNames = depts.map(d => d === 'obstetrics' ? '产科' : d === 'endocrinology' ? '内分泌科' : d).join('和')
    return `我已经记录了您的主诉。根据您的情况，我这就为您呼叫**${deptNames}**的专家进行联合会诊。`
  }

  if (node === 'graph_query') {
    const keys = data?.graph_knowledge ? Object.keys(data.graph_knowledge) : []
    return `正在为您调取最新临床指南... 检索完毕，已将**${keys.length}**项相关疾病和药物禁忌数据同步给各位专家。`
  }

  if (node === 'obstetrician' || node === 'endocrinologist') {
    const opinions = data?.expert_opinions
    if (!opinions) return '正在评估...'
    const dept = Object.keys(opinions)[0]
    const op = opinions[dept]

    if (op?.error) return `抱歉，我在评估时遇到了问题：${op.error}`

    const risk = op?.maternal_risk?.level || '未知'
    const recs = op?.recommendations?.[0] || '建议进一步观察'
    return `从${op.department || '我的专业'}角度来看，目前的母体风险评估为**${risk}**。我的核心建议是：${recs}。详细方案我已经写在右侧的会诊记录中了。`
  }

  if (node === 'reviewer') {
    const alerts = data?.safety_alerts?.length || 0
    if (alerts > 0) {
      return `大家注意，我刚才交叉核对了各位的用药建议。发现了 **${alerts}** 项潜在的安全风险（如药物禁忌），已在报告中红色高亮，请务必关注。最终的 MDT 报告已经生成。`
    }
    return `我已完成所有建议的交叉核对。用药方案安全，无明显冲突。最终的 MDT 会诊报告已生成，请查阅。`
  }

  if (node === 'error') {
    return `会诊中断：${data?.error}`
  }

  return '...'
}

function ChatBubble({ event }) {
  const { node, timestamp } = event
  const agent = AGENTS[node] || AGENTS.system
  const isRight = agent.align === 'right'
  const isCenter = agent.align === 'center'

  const content = event.content || generateDialogue(event)

  if (isCenter) {
    return (
      <div className="flex justify-center my-4">
        <span className="text-xs text-gray-500 bg-black/5 px-4 py-1.5 rounded-full shadow-inner border border-black/5 backdrop-blur-sm">
          {content}
        </span>
      </div>
    )
  }

  return (
    <div className={`flex w-full ${isRight ? 'justify-end' : 'justify-start'} mb-5`}>
      <div className={`flex max-w-[85%] ${isRight ? 'flex-row-reverse' : 'flex-row'} items-end gap-3`}>

        {/* Avatar */}
        <div className="flex flex-col items-center flex-shrink-0 mb-1">
          <div className="w-9 h-9 rounded-full bg-white border border-gray-200/80 flex items-center justify-center overflow-hidden shadow-[0_2px_8px_rgba(0,0,0,0.08)] ring-2 ring-white">
            <img src={agent.avatar} alt={agent.name} className="w-full h-full object-cover" />
          </div>
        </div>

        {/* Message */}
        <div className={`flex flex-col ${isRight ? 'items-end' : 'items-start'}`}>
          <span className="text-[11px] font-medium text-gray-500 mb-1.5 px-1 drop-shadow-sm">
            {agent.name} <span className="opacity-60 font-normal ml-1">{timestamp.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit' })}</span>
          </span>
          <div
            className={`px-4 py-3 rounded-2xl text-[13px] leading-relaxed shadow-[0_2px_10px_rgba(0,0,0,0.04)] border ${agent.color} ${agent.border} text-gray-800 relative
              ${isRight ? 'rounded-br-sm' : 'rounded-bl-sm'}
            `}
            dangerouslySetInnerHTML={{
              __html: safeMarkdown(content)
            }}
          />
        </div>

      </div>
    </div>
  )
}

export default function ChatRoom({ events, streaming, complaint }) {
  const scrollRef = useRef(null)

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events, streaming])

  if (!complaint && !events.length) return null

  // 构造对话流
  const chatFlow = []

  if (complaint) {
    chatFlow.push({
      node: 'user',
      content: complaint,
      timestamp: events[0]?.timestamp || new Date()
    })
  }

  events.forEach(ev => {
    if (ev.node !== 'done') {
      chatFlow.push(ev)
    }
  })

  return (
    <div className="flex flex-col h-full bg-[#f0f0f3] relative">
      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 sm:p-6 scroll-smooth pb-8">
        {chatFlow.map((ev, i) => (
          <div key={i} className="animate-in slide-in-from-bottom-2 fade-in duration-300">
            <ChatBubble event={ev} />
          </div>
        ))}

        {/* Typing indicator */}
        {streaming && events.length > 0 && events[events.length - 1].node !== 'done' && (
          <div className="flex w-full justify-start mb-4 animate-in fade-in duration-300">
            <div className="flex flex-row items-end gap-3">
              <div className="w-9 h-9 rounded-full bg-white border border-gray-200/80 flex items-center justify-center overflow-hidden shadow-[0_2px_8px_rgba(0,0,0,0.08)] ring-2 ring-white mb-1">
                 <img src={AGENTS.system.avatar} alt="Typing" className="w-full h-full object-cover opacity-50" />
              </div>
              <div className="px-4 py-3.5 rounded-2xl rounded-bl-sm bg-gradient-to-b from-white to-[#f8fafc] border border-[#cbd5e1] shadow-[0_2px_10px_rgba(0,0,0,0.04)]">
                <div className="flex gap-1.5">
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
