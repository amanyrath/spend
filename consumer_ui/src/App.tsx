import { BrowserRouter, Routes, Route, Navigate, useLocation, useParams } from "react-router-dom"
import { Navigation } from "@/components/navigation"
import { OverviewPage } from "@/pages/overview"
import { EducationPage } from "@/pages/education"
import { InsightsPage } from "@/pages/insights"
import { TransactionsPage } from "@/pages/transactions"
import { OffersPage } from "@/pages/offers"
import { ChatWidget } from "@/components/chat-widget"
import { DEFAULT_USER_ID, getValidUserId } from "@/lib/utils"

function ChatWidgetWrapper() {
  const location = useLocation()
  
  // Extract userId from pathname
  const pathParts = location.pathname.split('/').filter(Boolean)
  const userId = pathParts[0] ? getValidUserId(pathParts[0]) : DEFAULT_USER_ID
  
  return <ChatWidget userId={userId} />
}

function DefaultRedirect() {
  const { userId } = useParams<{ userId: string }>()
  const targetUserId = getValidUserId(userId)
  return <Navigate to={`/${targetUserId}/overview`} replace />
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="bg-background">
          <Routes>
            <Route
              path="/"
              element={<Navigate to={`/${DEFAULT_USER_ID}/overview`} replace />}
            />
            {/* More specific routes first to avoid matching :userId to route names */}
            <Route path="/:userId/overview" element={<OverviewPage />} />
            <Route path="/:userId/transactions" element={<TransactionsPage />} />
            <Route path="/:userId/offers" element={<OffersPage />} />
            <Route path="/:userId/insights" element={<InsightsPage />} />
            <Route path="/:userId/education" element={<EducationPage />} />
            <Route path="/:userId" element={<DefaultRedirect />} />
          </Routes>
        </main>
        <ChatWidgetWrapper />
      </div>
    </BrowserRouter>
  )
}

export default App
