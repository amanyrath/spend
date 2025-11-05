import * as React from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Copy, Check } from "lucide-react"
import { cn } from "@/lib/utils"

interface DecisionTraceViewerProps {
  decisionTrace: Record<string, any>
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DecisionTraceViewer({
  decisionTrace,
  open,
  onOpenChange,
}: DecisionTraceViewerProps) {
  const [copied, setCopied] = React.useState(false)
  const jsonString = JSON.stringify(decisionTrace, null, 2)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Silently fail - clipboard API may not be available in some contexts
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Decision Trace</DialogTitle>
          <DialogDescription>
            Complete JSON trace of the recommendation logic
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-auto">
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="absolute top-2 right-2 z-10"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </>
              )}
            </Button>
            <pre
              className={cn(
                "bg-muted p-4 rounded-lg overflow-x-auto text-sm",
                "font-mono",
                "border"
              )}
              style={{ fontFamily: "JetBrains Mono, monospace" }}
            >
              <code>{jsonString}</code>
            </pre>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

