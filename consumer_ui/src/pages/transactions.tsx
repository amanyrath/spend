import { useParams } from "react-router-dom"
import { TransactionsTab } from "@/components/TransactionsTab"
import { getValidUserId } from "@/lib/utils"

export function TransactionsPage() {
  const { userId } = useParams<{ userId: string }>()
  const validUserId = getValidUserId(userId)

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-foreground">Transactions</h1>
        <p className="text-muted-foreground text-base">
          Your recent transaction history
        </p>
      </div>
      <TransactionsTab userId={validUserId} />
    </div>
  )
}

