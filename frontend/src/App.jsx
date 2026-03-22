import { useConsultation } from './hooks/useConsultation'
import ConsultInput from './components/ConsultInput'
import ChatRoom from './components/ChatRoom'
import ExpertCards from './components/ExpertCards'
import MDTReport from './components/MDTReport'

export default function App() {
  const { status, events, report, error, submitStream, reset, complaint } = useConsultation()

  const isActive = status === 'streaming' || status === 'loading'

  return (
    <div className="min-h-screen bg-[#e8ecef] flex items-center justify-center p-4 sm:p-8 font-sans">
      {/* macOS Style Window Wrapper */}
      <div className="w-full max-w-7xl bg-[#f5f5f7] rounded-[20px] shadow-2xl overflow-hidden border border-white/60 ring-1 ring-black/5 flex flex-col h-[90vh]">

        {/* Window Title Bar */}
        <div className="h-12 bg-gradient-to-b from-[#fdfdfd] to-[#e8e8eb] border-b border-[#d1d1d6] flex items-center px-4 relative flex-shrink-0">
          {/* Mac window controls */}
          <div className="flex gap-2 absolute left-4">
            <div className="w-3 h-3 rounded-full bg-[#ff5f56] border border-[#e0443e] shadow-inner"></div>
            <div className="w-3 h-3 rounded-full bg-[#ffbd2e] border border-[#dea123] shadow-inner"></div>
            <div className="w-3 h-3 rounded-full bg-[#27c93f] border border-[#1aab29] shadow-inner"></div>
          </div>

          {/* Title */}
          <div className="w-full text-center flex items-center justify-center gap-2">
            <svg className="w-4 h-4 text-blue-600 drop-shadow-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            <h1 className="text-[13px] font-medium text-[#4d4d4d] tracking-wide" style={{ textShadow: '0 1px 0 rgba(255,255,255,0.8)' }}>
              妇产科 AI 虚拟 MDT 会诊系统
            </h1>
          </div>

          {/* Reset Button */}
          {status !== 'idle' && (
            <button
              onClick={reset}
              className="absolute right-4 text-[11px] font-medium text-gray-600 bg-white/80 hover:bg-white
                         px-3 py-1 rounded-md border border-gray-300 shadow-sm transition-all active:scale-95"
            >
              新建会诊
            </button>
          )}
        </div>

        {/* Main Content Area */}
        <main className="flex-1 overflow-hidden flex flex-col lg:flex-row">

          {/* Left Panel — Input + Chatroom */}
          <div className="w-full lg:w-[450px] flex flex-col border-r border-[#d1d1d6] bg-[#f0f0f3] z-10 shadow-[2px_0_10px_rgba(0,0,0,0.02)]">
            {status === 'idle' ? (
              <div className="p-6 flex-1 overflow-y-auto">
                <div className="bg-white rounded-2xl p-6 shadow-[0_4px_20px_rgba(0,0,0,0.05)] border border-white/80">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-400 to-blue-600 shadow-lg shadow-blue-500/30 flex items-center justify-center border border-blue-300/50">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-gray-800">发起新会诊</h2>
                      <p className="text-xs text-gray-500">输入患者主诉，AI 专家组将自动介入</p>
                    </div>
                  </div>
                  <ConsultInput onSubmit={submitStream} disabled={isActive} />
                </div>
              </div>
            ) : (
              <ChatRoom events={events} streaming={status === 'streaming'} complaint={complaint} />
            )}
          </div>

          {/* Right Panel — Expert Cards + Report */}
          <div className="flex-1 bg-[#f9f9fb] overflow-y-auto relative">
            <div className="p-6 lg:p-8 max-w-4xl mx-auto space-y-6 pb-20">

              {/* Loading state */}
              {isActive && events.length === 0 && (
                <div className="mt-20 flex flex-col items-center justify-center">
                  <div className="relative w-20 h-20 mb-6">
                    <div className="absolute inset-0 rounded-full border-4 border-blue-100"></div>
                    <div className="absolute inset-0 rounded-full border-4 border-blue-600 border-t-transparent animate-spin"></div>
                    <div className="absolute inset-0 flex items-center justify-center text-2xl">🏥</div>
                  </div>
                  <h3 className="text-lg font-medium text-gray-700">正在组建 MDT 专家团队...</h3>
                  <p className="text-sm text-gray-500 mt-2">系统正在解析主诉并连接知识图谱</p>
                </div>
              )}

              {/* Expert opinions */}
              {events.length > 0 && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <ExpertCards events={events} />
                </div>
              )}

              {/* Final report */}
              {report && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200 fill-mode-both">
                  <MDTReport report={report} />
                </div>
              )}

              {/* Error display */}
              {status === 'error' && error && (
                <div className="bg-gradient-to-br from-red-50 to-rose-50 border border-red-200 rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 shadow-inner">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h3 className="text-base font-bold text-red-800">会诊异常中断</h3>
                  </div>
                  <p className="text-sm text-red-600 ml-11">{error}</p>
                </div>
              )}

              {/* Empty state */}
              {status === 'idle' && (
                <div className="h-full min-h-[500px] flex flex-col items-center justify-center text-center px-6">
                  <div className="w-32 h-32 mb-6 relative">
                    <div className="absolute inset-0 bg-blue-100 rounded-full blur-2xl opacity-60"></div>
                    <img src="https://api.dicebear.com/7.x/shapes/svg?seed=medical&backgroundColor=ffffff" alt="Medical" className="w-full h-full drop-shadow-xl relative z-10 rounded-2xl" />
                  </div>
                  <h2 className="text-xl font-bold text-gray-800 mb-3">等待发起会诊</h2>
                  <p className="text-sm text-gray-500 max-w-md leading-relaxed">
                    在左侧输入患者主诉，系统将自动进行分诊，调用 Neo4j 知识图谱，并由多个 AI 专家智能体并行进行专业评估。
                  </p>
                </div>
              )}
            </div>
          </div>

        </main>
      </div>
    </div>
  )
}
