import * as React from "react"
import { ChatIcon } from "@/components/chat-icon"
import { ChatWindow } from "@/components/chat-window"
import { cn } from "@/lib/utils"

interface ChatWidgetProps {
  userId: string
  className?: string
}

export function ChatWidget({ userId, className }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = React.useState(false)

  return (
    <div className={cn("fixed bottom-6 right-6 z-50", className)}>
      {/* Chat Icon */}
      {!isOpen && (
        <ChatIcon onClick={() => setIsOpen(true)} />
      )}

      {/* Chat Window Popup */}
      {isOpen && (
        <div
          className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-2"
          style={{ animationDuration: '200ms' }}
        >
          <ChatWindow
            userId={userId}
            variant="popup"
            onClose={() => setIsOpen(false)}
          />
        </div>
      )}
    </div>
  )
}

