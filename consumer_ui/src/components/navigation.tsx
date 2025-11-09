import { Link, useLocation, useParams } from "react-router-dom"
import { cn, getValidUserId } from "@/lib/utils"

const navigation = [
  { name: "Dashboard", path: "/dashboard" },  // Combined mission+progress
  { name: "Profile", path: "/profile" },      // Combined overview+you
  { name: "Education", path: "/education" },
  { name: "Insights", path: "/insights" },
  { name: "Offers", path: "/offers" },
  { name: "Transactions", path: "/transactions" },
  { name: "Settings", path: "/settings" },
  { name: "Help", path: "/help" },
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
  const validUserId = getValidUserId(actualUserId || undefined)
  
  const basePath = validUserId ? `/${validUserId}` : ""

  return (
    <nav className="flex gap-5 mb-[30px] py-[15px] border-b border-retro-border">
      {navigation.map((item) => {
        const href = `${basePath}${item.path}`
        const isActive = location.pathname === href || location.pathname.startsWith(href)
        return (
          <Link
            key={item.name}
            to={href}
            className={cn(
              "text-sm text-[#64748b] font-mono no-underline py-[5px] px-[10px] border border-transparent transition-all",
              isActive
                ? "text-[#1e40af] border-[#1e40af] bg-[#eff6ff]"
                : "hover:text-[#1e40af] hover:border-[#e5e7eb]"
            )}
          >
            {item.name.toUpperCase()}
          </Link>
        )
      })}
    </nav>
  )
}

