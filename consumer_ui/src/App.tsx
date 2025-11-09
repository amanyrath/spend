import { BrowserRouter, Routes, Route, Navigate, useLocation, useParams } from "react-router-dom"
import { Layout } from "@/components/layout"
import { HelpPage } from "@/pages/help"
import { EducationPage } from "@/pages/education"
import { InsightsPage } from "@/pages/insights"
import { TransactionsPage } from "@/pages/transactions"
import { OffersPage } from "@/pages/offers"
import { DashboardPage } from "@/pages/dashboard"
import { ProfilePage } from "@/pages/profile"
import { LoginPage } from "@/pages/login"
import { SettingsPage } from "@/pages/settings"
import { ChatWidget } from "@/components/chat-widget"
import { ChatProvider } from "@/contexts/chat-context"
import { AuthProvider } from "@/contexts/auth-context"
import { ProtectedRoute } from "@/components/protected-route"
import { DEFAULT_USER_ID, getValidUserId } from "@/lib/utils"

function ChatWidgetWrapper() {
  const location = useLocation()
  
  // Extract userId from pathname
  const pathParts = location.pathname.split('/').filter(Boolean)
  const userId = pathParts[0] ? getValidUserId(pathParts[0]) : DEFAULT_USER_ID
  
  return <ChatWidget userId={userId} />
}

function AppContent() {
  const location = useLocation()
  const pathParts = location.pathname.split('/').filter(Boolean)
  const userId = pathParts[0] ? getValidUserId(pathParts[0]) : DEFAULT_USER_ID
  
  return (
    <ChatProvider userId={userId}>
      <div className="min-h-screen bg-background">
        <Layout>
          <Routes>
            <Route
              path="/"
              element={<Navigate to={`/${DEFAULT_USER_ID}/dashboard`} replace />}
            />
            {/* More specific routes first to avoid matching :userId to route names */}
            <Route path="/:userId/dashboard" element={<DashboardPage />} />
            <Route path="/:userId/profile" element={<ProfilePage />} />
            <Route path="/:userId/help" element={<HelpPage />} />
            <Route path="/:userId/education" element={<EducationPage />} />
            <Route path="/:userId/transactions" element={<TransactionsPage />} />
            <Route path="/:userId/offers" element={<OffersPage />} />
            <Route path="/:userId/insights" element={<InsightsPage />} />
            <Route path="/:userId/settings" element={<SettingsPage />} />
            <Route path="/:userId" element={<DefaultRedirect />} />
          </Routes>
        </Layout>
        <ChatWidgetWrapper />
      </div>
    </ChatProvider>
  )
}

function DefaultRedirect() {
  const { userId } = useParams<{ userId: string }>()
  const targetUserId = getValidUserId(userId)
  return <Navigate to={`/${targetUserId}/dashboard`} replace />
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/:userId/*" element={
            <ProtectedRoute>
              <AppContent />
            </ProtectedRoute>
          } />
          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
