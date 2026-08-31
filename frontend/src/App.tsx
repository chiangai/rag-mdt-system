import { useEffect, useState } from 'react'
import { transportMode } from './api'
import { AiHomePage, CarePlanPage, CheckInPage, MyPage, TimelinePage } from './pages'
import { MOBILE_TABS, contentRoute, normalizeMobileRoute, type MobileRoute } from './mobile-navigation'

function routeFromHash(): MobileRoute {
  return contentRoute(window.location.hash.replace(/^#\/?/, ''))
}

export function App() {
  const [route, setRoute] = useState<MobileRoute>(routeFromHash)
  const debug = new URLSearchParams(window.location.search).get('debug') === '1'

  useEffect(() => {
    const onHashChange = () => setRoute(routeFromHash())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const go = (next: MobileRoute) => { window.location.hash = `#/${next}` }
  const content = {
    ai: <AiHomePage debug={debug} onCheckIn={() => go('check-in')} />,
    me: <MyPage onNavigate={go} />,
    'check-in': <CheckInPage onBack={() => go('ai')} />,
    timeline: <TimelinePage onBack={() => go('me')} />,
    'care-plan': <CarePlanPage onBack={() => go('me')} />,
  }[route]

  const activeTab = normalizeMobileRoute(route)
  return <div className="phone-frame">
    <a className="skip-link" href="#main-content">跳到主要内容</a>
    <header className="mobile-header">
      <a className="brand" href="#/ai" aria-label="HerCare AI 首页"><span>✦</span>HerCare</a>
      <span className="week-pill">产后第 8 周</span>
    </header>
    <main id="main-content" className="mobile-main">{content}</main>
    <nav className="bottom-tabs" aria-label="主导航">
      {MOBILE_TABS.map((tab) => <button key={tab.id} type="button" className={activeTab === tab.id ? 'tab active' : 'tab'} onClick={() => go(tab.id)} aria-current={activeTab === tab.id ? 'page' : undefined}>
        <span aria-hidden="true">{tab.icon}</span>{tab.label}
      </button>)}
    </nav>
    <p className="app-boundary">HerCare 提供健康信息整理，不替代诊断或紧急医疗服务。{transportMode === 'mock' ? ' 演示数据。' : ''}</p>
  </div>
}
