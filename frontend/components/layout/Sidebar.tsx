'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '../../hooks/useAuth'

const navItems = [
  { href: '/', label: 'Overview' },
  { href: '/data', label: 'Data Ingestion & Preview' },
  { href: '/analytics', label: 'Sales Analytics' },
  { href: '/forecast', label: 'Forecast Lab' },
  { href: '/anomalies', label: 'Anomalies' },
  { href: '/scenarios', label: 'Scenario Lab' },
  { href: '/inventory', label: 'Inventory Intelligence' },
  { href: '/model-health', label: 'Model Health' },
  { href: '/gemini', label: 'Gemini AI' },
  { href: '/reports', label: 'Reports & Exports' },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuth()

  return (
    <aside className="w-64 bg-surface border-r border-slate-700 flex flex-col p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-white">Sales Intel AI</h1>
        <span className="text-xs text-primary font-mono block">Enterprise Platform</span>
      </div>

      <nav className="flex flex-col gap-4 text-sm font-medium">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href === '/gemini' && pathname === '/copilot')
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`hover:text-primary transition-colors py-1 ${
                isActive ? 'text-primary font-semibold' : 'text-slate-300'
              }`}
            >
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="mt-auto pt-4 border-t border-slate-700/60">
        {user ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Link 
                href="/profile" 
                className="text-xs text-slate-300 truncate font-medium hover:text-primary transition" 
                title={user.email}
              >
                {user.email}
              </Link>
              <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded font-mono">
                {user.role}
              </span>
            </div>
            <div className="flex gap-2">
              <Link
                href="/profile"
                className="flex-1 text-center text-xs font-medium py-1 px-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
              >
                Profile & Workspace
              </Link>
              <button
                onClick={logout}
                className="text-center text-xs font-medium py-1 px-2 rounded-lg bg-slate-800 text-slate-400 hover:text-danger hover:bg-slate-750 transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        ) : (
          <Link
            href="/login"
            className="block text-center text-xs font-semibold py-2 px-3 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition"
          >
            Account / Sign In
          </Link>
        )}
      </div>
    </aside>
  )
}
