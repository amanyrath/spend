import React, { useEffect, useState, useMemo } from "react"
import { fetchTransactions, type Transaction } from "@/lib/api"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Loader2,
  AlertCircle,
  Utensils,
  ShoppingBag,
  Car,
  Film,
  Receipt,
  Home,
  Heart,
  GraduationCap,
  Briefcase,
  DollarSign,
  ChevronDown,
  ChevronUp,
  MapPin,
  CreditCard,
  Globe,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface TransactionsTabProps {
  userId: string
}

type DateRange = "30" | "90" | "all"
type SortColumn = "date" | "amount"
type SortDirection = "asc" | "desc"

// Category icon mapping
const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  food_and_drink: Utensils,
  "food & drink": Utensils,
  general_merchandise: ShoppingBag,
  "general merchandise": ShoppingBag,
  gas_stations: Car,
  "gas stations": Car,
  groceries: ShoppingBag,
  transportation: Car,
  travel: Car,
  entertainment: Film,
  general: DollarSign,
  general_services: Receipt,
  lodging: Home,
  restaurants: Utensils,
  shopping: ShoppingBag,
  healthcare: Heart,
  education: GraduationCap,
  professional_services: Briefcase,
  bills: Receipt,
  gas: Car,
  subscriptions: Film,
  transfer: DollarSign,
}

// Helper function to get primary category (handles both string and array formats)
function getPrimaryCategory(category: string | string[]): string {
  if (Array.isArray(category)) {
    return category[0] || 'Uncategorized'
  }
  return category || 'Uncategorized'
}

// Helper function to get category icon
function getCategoryIcon(category: string | string[]) {
  const normalizedCategory = getPrimaryCategory(category).toLowerCase().replace(/\s+/g, "_")
  return categoryIcons[normalizedCategory] || DollarSign
}

// Format date as "Nov 3, 2025"
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date)
}

// Format amount as currency
function formatAmount(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(amount))
}

// Clean merchant name (remove trailing " 0" if present)
function cleanMerchantName(merchantName: string): string {
  return merchantName.replace(/\s+0$/, '')
}

// Get payment channel badge
function getPaymentChannelBadge(paymentChannel?: string): { label: string; className: string } | null {
  if (!paymentChannel) return null
  
  const badges: Record<string, { label: string; className: string }> = {
    'online': { label: 'Online', className: 'bg-blue-100 text-blue-800' },
    'in store': { label: 'In Store', className: 'bg-green-100 text-green-800' },
    'other': { label: 'Other', className: 'bg-gray-100 text-gray-800' },
  }
  
  return badges[paymentChannel.toLowerCase()] || { label: paymentChannel, className: 'bg-gray-100 text-gray-800' }
}

// Format location string
function formatLocation(txn: Transaction): string | null {
  const parts: string[] = []
  if (txn.location_city) parts.push(txn.location_city)
  if (txn.location_region) parts.push(txn.location_region)
  if (parts.length === 0) return null
  return parts.join(', ')
}

// Get date range start date
function getDateRangeStart(dateRange: DateRange): string | undefined {
  if (dateRange === "all") return undefined
  const days = parseInt(dateRange)
  const date = new Date()
  date.setDate(date.getDate() - days)
  return date.toISOString().split("T")[0]
}

export function TransactionsTab({ userId }: TransactionsTabProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Filter states
  const [dateRange, setDateRange] = useState<DateRange>("30")
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")
  
  // Sort states
  const [sortColumn, setSortColumn] = useState<SortColumn>("date")
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc")
  
  // Pagination states
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)
  
  // Expanded transaction details
  const [expandedTransactions, setExpandedTransactions] = useState<Set<string>>(new Set())

  // Fetch transactions
  useEffect(() => {
    setLoading(true)
    setError(null)
    
    const startDate = getDateRangeStart(dateRange)
    fetchTransactions(userId, startDate)
      .then((txns) => {
        setTransactions(txns)
        setLoading(false)
        setCurrentPage(1) // Reset to first page on filter change
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [userId, dateRange])

  // Get unique categories from transactions
  const categories = useMemo(() => {
    const uniqueCategories = Array.from(
      new Set(transactions.map((t) => getPrimaryCategory(t.category)))
    ).sort()
    return uniqueCategories
  }, [transactions])

  // Filter transactions
  const filteredTransactions = useMemo(() => {
    return transactions.filter((txn) => {
      // Category filter
      if (selectedCategory !== "all" && getPrimaryCategory(txn.category) !== selectedCategory) {
        return false
      }
      
      // Search filter
      if (searchQuery.trim() && !cleanMerchantName(txn.merchant_name).toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      
      return true
    })
  }, [transactions, selectedCategory, searchQuery])

  // Sort transactions
  const sortedTransactions = useMemo(() => {
    const sorted = [...filteredTransactions].sort((a, b) => {
      let comparison = 0
      
      if (sortColumn === "date") {
        comparison = new Date(a.date).getTime() - new Date(b.date).getTime()
      } else if (sortColumn === "amount") {
        comparison = Math.abs(a.amount) - Math.abs(b.amount)
      }
      
      return sortDirection === "asc" ? comparison : -comparison
    })
    
    return sorted
  }, [filteredTransactions, sortColumn, sortDirection])

  // Pagination calculations
  const totalPages = Math.ceil(sortedTransactions.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedTransactions = sortedTransactions.slice(startIndex, endIndex)
  const startItem = sortedTransactions.length === 0 ? 0 : startIndex + 1
  const endItem = Math.min(endIndex, sortedTransactions.length)

  // Handle sort toggle
  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortColumn(column)
      setSortDirection("desc")
    }
    setCurrentPage(1)
  }

  // Sort icon component
  const SortIcon = ({ column }: { column: SortColumn }) => {
    if (sortColumn !== column) {
      return <ArrowUpDown className="ml-2 h-4 w-4 text-muted-foreground" />
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="ml-2 h-4 w-4" />
    ) : (
      <ArrowDown className="ml-2 h-4 w-4" />
    )
  }

  // Pagination page numbers
  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const maxVisible = 5
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) {
          pages.push(i)
        }
        pages.push("ellipsis")
        pages.push(totalPages)
      } else if (currentPage >= totalPages - 2) {
        pages.push(1)
        pages.push("ellipsis")
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pages.push(i)
        }
      } else {
        pages.push(1)
        pages.push("ellipsis")
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i)
        }
        pages.push("ellipsis")
        pages.push(totalPages)
      }
    }
    
    return pages
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <div className="text-center">
              <p className="text-destructive font-medium">Error loading transactions</p>
              <p className="text-sm text-muted-foreground mt-1">{error}</p>
            </div>
            <Button
              onClick={() => {
                setError(null)
                setLoading(true)
                const startDate = getDateRangeStart(dateRange)
                fetchTransactions(userId, startDate)
                  .then((txns) => {
                    setTransactions(txns)
                    setLoading(false)
                  })
                  .catch((err) => {
                    setError(err.message)
                    setLoading(false)
                  })
              }}
              variant="outline"
            >
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card className="shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            {/* Date Range Buttons */}
            <div className="flex flex-wrap gap-2">
              <Button
                variant={dateRange === "30" ? "default" : "outline"}
                size="sm"
                onClick={() => setDateRange("30")}
                className="font-medium"
              >
                30 days
              </Button>
              <Button
                variant={dateRange === "90" ? "default" : "outline"}
                size="sm"
                onClick={() => setDateRange("90")}
                className="font-medium"
              >
                90 days
              </Button>
              <Button
                variant={dateRange === "all" ? "default" : "outline"}
                size="sm"
                onClick={() => setDateRange("all")}
                className="font-medium"
              >
                All
              </Button>
            </div>

            {/* Category Dropdown */}
            <div className="flex-1 min-w-[200px]">
              <Select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value)
                  setCurrentPage(1)
                }}
                className="w-full"
              >
                <option value="all">All Categories</option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </Select>
            </div>

            {/* Search Input */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by merchant..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value)
                    setCurrentPage(1)
                  }}
                  className="pl-10 w-full"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold">Transactions</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {filteredTransactions.length === 0 ? (
            <div className="text-center py-16 px-6">
              <p className="text-muted-foreground text-base">
                No transactions found for this filter
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-b">
                      <TableHead className="font-semibold text-sm h-12">
                        <button
                          onClick={() => handleSort("date")}
                          className="flex items-center gap-2 hover:text-primary transition-colors font-semibold"
                        >
                          Date
                          <SortIcon column="date" />
                        </button>
                      </TableHead>
                      <TableHead className="font-semibold text-sm">Merchant Name</TableHead>
                      <TableHead className="font-semibold text-sm">Category</TableHead>
                      <TableHead className="font-semibold text-sm text-right">
                        <button
                          onClick={() => handleSort("amount")}
                          className="flex items-center gap-2 hover:text-primary transition-colors font-semibold ml-auto"
                        >
                          Amount
                          <SortIcon column="amount" />
                        </button>
                      </TableHead>
                      <TableHead className="font-semibold text-sm text-right">Account</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedTransactions.map((txn) => {
                      const CategoryIcon = getCategoryIcon(txn.category)
                      const isDebit = txn.amount < 0
                      const isExpanded = expandedTransactions.has(txn.transaction_id)
                      const paymentChannelBadge = getPaymentChannelBadge(txn.payment_channel)
                      const locationStr = formatLocation(txn)
                      const showAuthorizedDate = txn.authorized_date && txn.authorized_date !== txn.date
                      
                      return (
                        <React.Fragment key={txn.transaction_id}>
                          <TableRow
                            className="hover:bg-muted/50 transition-colors border-b cursor-pointer"
                            onClick={() => {
                              const newExpanded = new Set(expandedTransactions)
                              if (isExpanded) {
                                newExpanded.delete(txn.transaction_id)
                              } else {
                                newExpanded.add(txn.transaction_id)
                              }
                              setExpandedTransactions(newExpanded)
                            }}
                          >
                            <TableCell className="font-medium py-5 text-sm">
                              <div className="flex flex-col gap-1">
                                {formatDate(txn.date)}
                                {showAuthorizedDate && (
                                  <span className="text-xs text-muted-foreground">
                                    Auth: {formatDate(txn.authorized_date!)}
                                  </span>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="py-5">
                              <div className="flex flex-col gap-2">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="font-medium">{cleanMerchantName(txn.merchant_name)}</span>
                                  {txn.pending && (
                                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full font-medium">
                                      Pending
                                    </span>
                                  )}
                                  {paymentChannelBadge && (
                                    <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", paymentChannelBadge.className)}>
                                      {paymentChannelBadge.label}
                                    </span>
                                  )}
                                </div>
                                {locationStr && (
                                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                    <MapPin className="h-3 w-3" />
                                    <span>{locationStr}</span>
                                  </div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="py-5">
                              <div className="flex items-center gap-2.5">
                                <div className="p-1.5 bg-primary/10 rounded-md">
                                  <CategoryIcon className="h-4 w-4 text-primary" />
                                </div>
                                <span className="text-sm font-medium">{getPrimaryCategory(txn.category)}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right py-5">
                              <span className={cn(
                                "font-semibold text-base",
                                isDebit ? "text-red-600" : "text-green-600"
                              )}>
                                {isDebit ? "-" : "+"}
                                {formatAmount(txn.amount)}
                              </span>
                            </TableCell>
                            <TableCell className="text-muted-foreground text-right py-5 font-mono text-sm">
                              <div className="flex items-center justify-end gap-2">
                                {txn.account_mask ? `****${String(txn.account_mask)}` : "N/A"}
                                {(locationStr || txn.location_address || txn.payment_channel) && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      const newExpanded = new Set(expandedTransactions)
                                      if (isExpanded) {
                                        newExpanded.delete(txn.transaction_id)
                                      } else {
                                        newExpanded.add(txn.transaction_id)
                                      }
                                      setExpandedTransactions(newExpanded)
                                    }}
                                    className="ml-2 text-muted-foreground hover:text-foreground"
                                  >
                                    {isExpanded ? (
                                      <ChevronUp className="h-4 w-4" />
                                    ) : (
                                      <ChevronDown className="h-4 w-4" />
                                    )}
                                  </button>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                          {isExpanded && (txn.location_address || txn.location_city || txn.payment_channel || txn.iso_currency_code) && (
                            <TableRow key={`${txn.transaction_id}-details`} className="bg-muted/30">
                              <TableCell colSpan={5} className="py-4 px-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                  {txn.location_address && (
                                    <div className="flex items-start gap-2">
                                      <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                                      <div>
                                        <div className="font-medium text-muted-foreground mb-1">Address</div>
                                        <div className="text-foreground">
                                          {txn.location_address}
                                          {txn.location_postal_code && `, ${txn.location_postal_code}`}
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                  {(txn.location_city || txn.location_region) && (
                                    <div className="flex items-start gap-2">
                                      <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                                      <div>
                                        <div className="font-medium text-muted-foreground mb-1">Location</div>
                                        <div className="text-foreground">
                                          {[txn.location_city, txn.location_region].filter(Boolean).join(', ')}
                                          {txn.location_country && txn.location_country !== 'US' && `, ${txn.location_country}`}
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                  {(txn.location_lat && txn.location_lon) && (
                                    <div className="flex items-start gap-2">
                                      <Globe className="h-4 w-4 text-muted-foreground mt-0.5" />
                                      <div>
                                        <div className="font-medium text-muted-foreground mb-1">Coordinates</div>
                                        <div className="text-foreground font-mono text-xs">
                                          {txn.location_lat.toFixed(6)}, {txn.location_lon.toFixed(6)}
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                  {txn.payment_channel && (
                                    <div className="flex items-start gap-2">
                                      <CreditCard className="h-4 w-4 text-muted-foreground mt-0.5" />
                                      <div>
                                        <div className="font-medium text-muted-foreground mb-1">Payment Channel</div>
                                        <div className="text-foreground capitalize">{txn.payment_channel}</div>
                                      </div>
                                    </div>
                                  )}
                                  {txn.iso_currency_code && txn.iso_currency_code !== 'USD' && (
                                    <div className="flex items-start gap-2">
                                      <DollarSign className="h-4 w-4 text-muted-foreground mt-0.5" />
                                      <div>
                                        <div className="font-medium text-muted-foreground mb-1">Currency</div>
                                        <div className="text-foreground">{txn.iso_currency_code}</div>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </TableCell>
                            </TableRow>
                          )}
                        </React.Fragment>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 pt-6 border-t px-6 pb-6 bg-muted/30">
                <div className="text-sm text-muted-foreground font-medium">
                  Showing {startItem}-{endItem} of {sortedTransactions.length} transactions
                </div>
                
                <div className="flex items-center gap-4">
                  {/* Items per page */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground font-medium">Show:</span>
                    <Select
                      value={itemsPerPage.toString()}
                      onChange={(e) => {
                        setItemsPerPage(parseInt(e.target.value))
                        setCurrentPage(1)
                      }}
                      className="w-20"
                    >
                      <option value="10">10</option>
                      <option value="25">25</option>
                      <option value="50">50</option>
                      <option value="100">100</option>
                    </Select>
                  </div>

                  {/* Page navigation */}
                  <div className="flex items-center gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="font-medium"
                    >
                      Previous
                    </Button>
                    
                    {getPageNumbers().map((page, idx) => {
                      if (page === "ellipsis") {
                        return (
                          <span key={`ellipsis-${idx}`} className="px-2 text-muted-foreground">
                            ...
                          </span>
                        )
                      }
                      return (
                        <Button
                          key={page}
                          variant={currentPage === page ? "default" : "outline"}
                          size="sm"
                          onClick={() => setCurrentPage(page as number)}
                          className="min-w-[40px] font-medium"
                        >
                          {page}
                        </Button>
                      )
                    })}
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="font-medium"
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

