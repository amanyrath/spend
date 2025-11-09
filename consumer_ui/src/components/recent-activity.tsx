import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import type { Transaction } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"

export interface RecentActivityProps {
  transactions: Transaction[]
}

interface ActivityItem {
  icon: string
  text: string
  timeAgo: string
}

/**
 * Formats a date as relative time (e.g., "2 days ago")
 */
function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    if (diffHours === 0) {
      const diffMins = Math.floor(diffMs / (1000 * 60))
      return diffMins === 0 ? "Just now" : `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    }
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  } else if (diffDays === 1) {
    return "1 day ago"
  } else if (diffDays < 7) {
    return `${diffDays} days ago`
  } else if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7)
    return `${weeks} week${weeks > 1 ? 's' : ''} ago`
  } else {
    const months = Math.floor(diffDays / 30)
    return `${months} month${months > 1 ? 's' : ''} ago`
  }
}

/**
 * Extracts activity items from transaction history
 */
function extractActivityItems(transactions: Transaction[]): ActivityItem[] {
  const items: ActivityItem[] = []
  
  // Filter for payment transactions (negative amounts typically indicate payments/debits)
  const paymentTransactions = transactions
    .filter(tx => tx.amount < 0)
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5)
  
  paymentTransactions.forEach((tx, index) => {
    // Check if this looks like a credit card payment
    const isPayment = tx.amount < 0 && Math.abs(tx.amount) > 50
    
    if (isPayment) {
      items.push({
        icon: "✓",
        text: `Last payment: ${formatCurrency(Math.abs(tx.amount))}`,
        timeAgo: formatTimeAgo(tx.date)
      })
    }
  })
  
  // If we don't have enough items, add some generic ones
  if (items.length === 0) {
    items.push({
      icon: "✓",
      text: "On track this month",
      timeAgo: "2 weeks ago"
    })
  }
  
  // Ensure we have at least 3 items
  while (items.length < 3 && items.length < transactions.length) {
    const tx = transactions[items.length]
    if (tx) {
      items.push({
        icon: "✓",
        text: `Balance reduced by ${formatCurrency(Math.abs(tx.amount))}`,
        timeAgo: formatTimeAgo(tx.date)
      })
    } else {
      break
    }
  }
  
  return items.slice(0, 3)
}

export function RecentActivity({ transactions }: RecentActivityProps) {
  const activityItems = extractActivityItems(transactions)
  
  return (
    <RetroCard>
      <RetroCardHeader>
        <RetroCardTitle className="text-base">RECENT ACTIVITY</RetroCardTitle>
      </RetroCardHeader>
      <RetroCardContent>
        <div className="space-y-0">
          {activityItems.map((item, index) => (
            <div key={index}>
              {index > 0 && (
                <div className="border-t border-dashed border-[#E9ECEF] my-[10px]" />
              )}
              <div className="flex items-center gap-[10px] text-xs font-mono pb-0">
                <span className="text-[#28A745] font-bold text-sm">{item.icon}</span>
                <span className="text-[#343A40] flex-1">{item.text}</span>
                <span className="text-[#6C757D] text-xs ml-auto">
                  {item.timeAgo}
                </span>
              </div>
            </div>
          ))}
        </div>
      </RetroCardContent>
    </RetroCard>
  )
}

