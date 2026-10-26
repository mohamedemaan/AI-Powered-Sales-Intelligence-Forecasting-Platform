import './globals.css'
import { ReactNode } from 'react'
import Providers from './providers'
import { AppShell } from '../components/layout/AppShell'

export const metadata = {
  title: 'SalesMind AI — AI-Powered Sales Intelligence & Forecasting Platform',
  description: 'Turn your sales data into intelligent predictions, actionable insights, and smarter business decisions.',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-background text-slate-200 min-h-screen">
        <Providers>
          <AppShell>
            {children}
          </AppShell>
        </Providers>
      </body>
    </html>
  )
}
