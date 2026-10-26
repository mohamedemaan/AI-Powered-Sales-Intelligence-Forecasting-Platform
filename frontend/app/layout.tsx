import './globals.css'
import { ReactNode } from 'react'
import Providers from './providers'
import { Sidebar } from '../components/layout/Sidebar'

export const metadata = {
  title: 'Sales Intel AI',
  description: 'AI-Powered Sales Intelligence Platform',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-background text-slate-200 min-h-screen">
        <Providers>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-8">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
