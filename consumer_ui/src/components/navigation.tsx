import { Link, useLocation, useParams } from "react-router-dom"
import { cn, getValidUserId } from "@/lib/utils"
import { Home, BookOpen, TrendingUp, Receipt, Gift } from "lucide-react"

const navigation = [
  { name: "Overview", path: "/overview", icon: Home },
  { name: "Education", path: "/education", icon: BookOpen },
  { name: "Insights", path: "/insights", icon: TrendingUp },
  { name: "Transactions", path: "/transactions", icon: Receipt },
  { name: "Offers", path: "/offers", icon: Gift },
]

export function Navigation() {
  const location = useLocation()
  const { userId } = useParams<{ userId: string }>()
  
  // Extract userId from pathname if params don't have it
  // This handles cases where routes might not match correctly
  const actualUserId = userId || (location.pathname.startsWith('/') 
    ? location.pathname.split('/')[1] 
    : null)
  
  // Validate that userId is actually a user ID (not a route name)
  const validUserId = getValidUserId(actualUserId)
  
  const basePath = validUserId ? `/${validUserId}` : ""

  return (
    <nav className="border-b bg-white shadow-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-primary">SpendSense</h1>
          </div>
          <div className="flex items-center gap-1">
            {navigation.map((item) => {
              const href = `${basePath}${item.path}`
              const isActive = location.pathname === href
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={href}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors rounded-md",
                    "hover:text-primary hover:bg-muted/50",
                    isActive
                      ? "text-primary bg-primary/5 border-b-2 border-primary"
                      : "text-muted-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{item.name}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}

