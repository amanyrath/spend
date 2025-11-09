import { ReactNode } from "react"
import { Navigation } from "@/components/navigation"

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto max-w-[1200px]">
        {/* Header */}
        <div className="border-b-2 border-dashed border-retro-border pb-5 mb-[30px]">
          <div className="text-2xl font-bold font-mono tracking-[2px] mb-1 text-[#1e40af]">
            SPENDSENSE
          </div>
          <div className="text-xs text-[#64748b] font-mono tracking-wider">
            One mission at a time. Clear progress. Real results.
          </div>
        </div>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main className="pb-8">
          {children}
        </main>

        {/* Footer */}
        <div className="mt-[60px] pt-[30px] border-t-2 border-dashed border-retro-border text-center text-[11px] text-[#94a3b8]">
          SpendSense | Technically Trustworthy Financial Guidance
        </div>
      </div>
    </div>
  )
}

