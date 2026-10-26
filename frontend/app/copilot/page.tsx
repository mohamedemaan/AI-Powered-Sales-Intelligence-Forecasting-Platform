'use client'

import GeminiPage from '../gemini/page'

/**
 * Re-exports GeminiPage to maintain route compatibility while upgrading
 * from the legacy mock copilot to live Google Gemini Pro.
 */
export default function CopilotMigrationPage() {
  return <GeminiPage />
}
