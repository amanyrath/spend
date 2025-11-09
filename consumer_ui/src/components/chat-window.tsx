import * as React from "react"
import { X, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { RetroButton } from "@/components/ui/retro-button"
import { useChat } from "@/contexts/use-chat"
import ReactMarkdown from 'react-markdown'

const SUGGESTED_QUESTIONS = [
  "What's my credit utilization?",
  "How much do I spend on subscriptions?",
  "Why am I seeing this content?",
]

interface ChatWindowProps {
  userId: string
  onClose?: () => void
  variant?: 'popup' | 'inline'
  className?: string
}

export function ChatWindow({ userId, onClose, variant = 'popup', className }: ChatWindowProps) {
  const { messages, sendMessage, isLoading } = useChat()
  const [inputValue, setInputValue] = React.useState("")
  const messagesEndRef = React.useRef<HTMLDivElement>(null)
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when messages change
  React.useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isLoading])

  // Auto-resize textarea
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 100)}px`
    }
  }, [inputValue])

  // Auto-focus textarea when chat opens (for popup variant)
  React.useEffect(() => {
    if (variant === 'popup' && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [variant])

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const messageText = inputValue.trim()
    setInputValue("")
    await sendMessage(messageText, userId)
  }

  const handleSuggestedQuestion = async (question: string) => {
    setInputValue("")
    await sendMessage(question, userId)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
    if (e.key === 'Escape' && onClose) {
      onClose()
    }
  }

  // Format timestamp
  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    return date.toLocaleDateString()
  }

  // Render message text with markdown and citation highlighting
  const renderMessageText = (text: string) => {
    return (
      <ReactMarkdown
        components={{
          text: ({ node, children, ...props }) => {
            const textContent = String(children)
            const citationPattern = /(\d+\.?\d*%|\$\d+[\d,]*\.?\d*|\d+ subscriptions)/g
            const citationMatch = textContent.match(citationPattern)
            if (citationMatch) {
              const parts = textContent.split(citationPattern)
              return (
                <>
                  {parts.map((part, index) => {
                    if (part && part.match(citationPattern)) {
                      return (
                        <span
                          key={index}
                          className="bg-[#eff6ff] text-[#1e40af] px-1.5 py-0.5 rounded font-semibold text-xs inline-block mx-0.5 border border-[#1e40af]/20"
                        >
                          {part}
                        </span>
                      )
                    }
                    return part ? <span key={index}>{part}</span> : null
                  })}
                </>
              )
            }
            return <>{children}</>
          },
          ul: ({ node, ...props }) => <ul className="list-disc list-inside space-y-1 my-2 pl-0 font-mono" {...props} />,
          li: ({ node, ...props }) => <li className="ml-4 font-mono" {...props} />,
          strong: ({ node, ...props }) => <strong className="font-semibold text-[#1a1a1a]" {...props} />,
          p: ({ node, ...props }) => <p className="mb-2 last:mb-0 font-mono" {...props} />,
        }}
      >
        {text}
      </ReactMarkdown>
    )
  }

  const isPopup = variant === 'popup'

  return (
    <div
      className={cn(
        "bg-white border border-[#E5E7EB] flex flex-col",
        isPopup ? "w-[380px] max-h-[600px] h-[600px] rounded-t-lg shadow-lg" : "w-full",
        className
      )}
    >
      {/* Header */}
      {isPopup && (
        <div className="px-6 py-6 border-b border-[#E5E7EB] bg-white flex items-center justify-between">
          <div className="flex items-center gap-[10px]">
            <div className="w-8 h-8 border-2 border-[#1a1a1a] flex items-center justify-center font-mono text-sm font-bold text-[#1a1a1a]">
              AI
            </div>
            <div>
              <h3 className="text-sm font-mono font-semibold text-[#1a1a1a] uppercase tracking-wider">
                Financial Assistant
              </h3>
              <p className="text-xs font-mono text-[#666666] mt-1">
                Usually replies instantly
              </p>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="w-8 h-8 border border-[#E5E7EB] bg-white text-[#1a1a1a] flex items-center justify-center hover:bg-[#f5f5f5] transition-colors font-mono"
              aria-label="Close chat"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      )}

      {/* Messages Area */}
      <div
        className={cn(
          "flex-1 overflow-y-auto px-6 py-6 bg-white flex flex-col gap-4",
          isPopup ? "" : "min-h-[400px] max-h-[600px]"
        )}
      >
        {messages.map((message, index) => {
          const showTime =
            index === 0 ||
            messages[index - 1].timestamp.getTime() - message.timestamp.getTime() > 300000

          return (
            <React.Fragment key={message.id}>
              {showTime && (
                <div className="text-center text-xs font-mono text-[#888888] my-2">
                  {formatTime(message.timestamp)}
                </div>
              )}
              <div
                className={cn(
                  "max-w-[85%] px-4 py-3 border font-mono text-sm leading-relaxed",
                  message.sender === 'user'
                    ? "bg-white border-[#1a1a1a] text-[#1e40af] ml-auto"
                    : "bg-white border-[#E5E7EB] text-[#1a1a1a]"
                )}
              >
                {message.sender === 'bot' ? renderMessageText(message.text) : message.text}
              </div>
            </React.Fragment>
          )
        })}

        {/* Typing Indicator */}
        {isLoading && (
          <div className="flex gap-1.5 px-4 py-2 bg-white border border-[#E5E7EB] max-w-[60px] self-start">
            <div className="w-1.5 h-1.5 bg-[#1a1a1a] animate-bounce" style={{ animationDelay: '0s' }} />
            <div className="w-1.5 h-1.5 bg-[#1a1a1a] animate-bounce" style={{ animationDelay: '0.2s' }} />
            <div className="w-1.5 h-1.5 bg-[#1a1a1a] animate-bounce" style={{ animationDelay: '0.4s' }} />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="px-6 py-4 bg-white border-t border-[#E5E7EB]">
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(question)}
                className="px-3 py-1.5 bg-[#f5f5f5] border border-[#E5E7EB] text-xs font-mono text-[#1a1a1a] hover:bg-[#e5e5e5] hover:border-[#1a1a1a] transition-all uppercase tracking-wider"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="px-6 py-4 bg-white border-t border-[#E5E7EB] flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={isLoading}
            className="w-full px-4 py-2 border border-[#E5E7EB] text-sm font-mono resize-none max-h-[100px] focus:outline-none focus:border-[#1a1a1a] disabled:opacity-50 bg-white text-[#1a1a1a]"
            rows={1}
            aria-label="Chat input"
          />
        </div>
        <RetroButton
          onClick={handleSend}
          disabled={!inputValue.trim() || isLoading}
          size="sm"
          className="flex-shrink-0"
          aria-label="Send message"
        >
          <ArrowRight className="h-4 w-4" />
        </RetroButton>
      </div>

      {/* Disclaimer */}
      <div
        className="px-6 py-3 bg-yellow-50 border-t border-yellow-200 text-xs font-mono text-[#666666] leading-relaxed"
        role="complementary"
        aria-label="Disclaimer"
      >
        This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.
      </div>
    </div>
  )
}

