import { useEffect, useState } from 'react'
import { transportMode } from './api'
import { AskHerCare, CarePlanPage, CheckInPage, HomePage, ProductPage, TimelinePage } from './pages'

type Route = 'home' | 'check-in' | 'timeline' | 'care-plan' | 'product' | 'ask'

const navItems: Array<{ route: Route; label: string; icon: string }> = [
  { route: 'home', label: '首页', icon: '⌂' },
  { route: 'check-in', label: '签到', icon: '✓' },
  { route: 'timeline', label: '时间线', icon: '◷' },
  { route: 'care-plan', label: '照护计划', icon: '☷' },
  { route: 'product', label: '关于 HerCare', icon: '♡' },
  { route: 'ask', label: '问问 HerCare', icon: '✦' },
]

function routeFromHash(): Route {
  const value = window.location.hash.replace(/^#\/?/, '')
  return navItems.some((item) => item.route === value) ? value as Route : 'home'
}

export function App() {
  const [route, setRoute] = useState<Route>(routeFromHash)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const debug = new URLSearchParams(window.location.search).get('debug') === '1'

  useEffect(() => {
    const onHashChange = () => {
      setRoute(routeFromHash())
      setIsMenuOpen(false)
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const content = {
    home: <HomePage onAsk={() => { window.location.hash = '#/ask' }} />,
    'check-in': <CheckInPage />,
    timeline: <TimelinePage />,
    'care-plan': <CarePlanPage />,
    product: <ProductPage />,
    ask: <AskHerCare debug={debug} />,
  }[route]

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">跳到主要内容</a>
      <header className="topbar">
        <a className="brand" href="#/home" aria-label="HerCare 首页"><span>✦</span> HerCare</a>
        <button className="menu-button" type="button" aria-expanded={isMenuOpen} aria-controls="primary-navigation" onClick={() => setIsMenuOpen((open) => !open)}>
          菜单
        </button>
        <nav id="primary-navigation" className={isMenuOpen ? 'nav open' : 'nav'} aria-label="主导航">
          {navItems.map((item) => (
            <a key={item.route} className={route === item.route ? 'nav-link active' : 'nav-link'} href={`#/${item.route}`} aria-current={route === item.route ? 'page' : undefined}>
              <span aria-hidden="true">{item.icon}</span>{item.label}
            </a>
          ))}
        </nav>
      </header>
      <main id="main-content" className="main-content">{content}</main>
      <footer>HerCare 仅用于健康信息整理与沟通准备，不替代诊断或紧急医疗服务。{transportMode === 'mock' ? ' 当前为演示数据。' : ''}</footer>
    </div>
  )
}
