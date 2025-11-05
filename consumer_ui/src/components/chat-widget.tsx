import * as React from "react"
import { MessageCircle, X, Minus, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { sendChatMessage } from "@/lib/api"

interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
}

interface ChatWidgetProps {
  userId: string
  className?: string
}

const SUGGESTED_QUESTIONS = [
  "What's my credit utilization?",
  "How much do I spend on subscriptions?",
  "Why am I seeing this content?",
]

export function ChatWidget({ userId, className }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const [isMinimized, setIsMinimized] = React.useState(false)
  const [messages, setMessages] = React.useState<Message[]>([
    {
      id: '1',
      text: "Hello! I can help you understand your finances. What would you like to know?",
      sender: 'bot',
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = React.useState("")
  const [isTyping, setIsTyping] = React.useState(false)
  const messagesEndRef = React.useRef<HTMLDivElement>(null)
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when messages change
  React.useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isTyping])

  // Auto-resize textarea
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 100)}px`
    }
  }, [inputValue])

  // Auto-focus textarea when chat opens
  React.useEffect(() => {
    if (isOpen && !isMinimized && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [isOpen, isMinimized])

  const handleSend = () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const messageText = inputValue
    setInputValue("")
    setIsTyping(true)

    // Connect to chat API endpoint
    sendChatMessage(userId, messageText)
      .then((response) => {
        setIsTyping(false)
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            text: response.data.response,
            sender: 'bot',
            timestamp: new Date(),
          },
        ])
      })
      .catch((error) => {
        setIsTyping(false)
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            text: `Sorry, I encountered an error: ${error.message}`,
            sender: 'bot',
            timestamp: new Date(),
          },
        ])
      })
  }

  const handleSuggestedQuestion = (question: string) => {
    setInputValue(question)
    // Auto-send suggested question
    setTimeout(() => {
      setInputValue("")
      const userMessage: Message = {
        id: Date.now().toString(),
        text: question,
        sender: 'user',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMessage])
      setIsTyping(true)
      
      sendChatMessage(userId, question)
        .then((response) => {
          setIsTyping(false)
          setMessages((prev) => [
            ...prev,
            {
              id: (Date.now() + 1).toString(),
              text: response.data.response,
              sender: 'bot',
              timestamp: new Date(),
            },
          ])
        })
        .catch((error) => {
          setIsTyping(false)
          setMessages((prev) => [
            ...prev,
            {
              id: (Date.now() + 1).toString(),
              text: `Sorry, I encountered an error: ${error.message}`,
              sender: 'bot',
              timestamp: new Date(),
            },
          ])
        })
    }, 100)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
    if (e.key === 'Escape') {
      setIsOpen(false)
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

  // Highlight data citations in bot messages
  const renderMessageText = (text: string) => {
    // Simple pattern matching for data citations (will be enhanced in Story 5.3)
    const parts = text.split(/(\d+%|\$\d+|\d+ subscriptions)/g)
    return parts.map((part, index) => {
      if (part.match(/\d+%|\$\d+|\d+ subscriptions/)) {
        return (
          <span
            key={index}
            className="bg-[rgba(30,64,175,0.1)] text-[#1e40af] px-1.5 py-0.5 rounded font-semibold text-[0.8125rem] inline-block mx-0.5"
          >
            {part}
          </span>
        )
      }
      return <span key={index}>{part}</span>
    })
  }

  return (
    <div className={cn("fixed bottom-5 right-5 z-50", className)}>
      {/* Chat Button */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="rounded-full px-5 py-3 h-auto shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5"
          style={{
            background: '#1e40af',
            boxShadow: '0 4px 12px rgba(30, 64, 175, 0.3)',
          }}
          aria-label="Open chat"
        >
          <MessageCircle className="h-5 w-5 mr-2" />
          <span className="text-sm font-medium">Message</span>
        </Button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          className={cn(
            "bg-white rounded-t-2xl shadow-lg border border-[#e2e8f0] flex flex-col",
            "transition-transform duration-300 ease-out",
            isOpen ? "translate-y-0" : "translate-y-full",
            "w-[380px] max-h-[600px] h-[600px]",
            "md:w-[380px]",
            "max-md:w-full max-md:right-0 max-md:left-0 max-md:rounded-t-2xl"
          )}
          style={{
            boxShadow: '0 -4px 20px rgba(0,0,0,0.15)',
          }}
          role="region"
          aria-label="Chat window"
        >
          {/* Header */}
          <div className="px-5 py-4 border-b border-[#e2e8f0] bg-white rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-lg"
                style={{
                  background: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
                }}
              >
                AI
              </div>
              <div>
                <h3 className="text-[0.9375rem] font-semibold text-[#1e293b] leading-tight">
                  Financial Assistant
                </h3>
                <p className="text-[0.75rem] text-[#64748b]">
                  Usually replies instantly
                </p>
              </div>
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="w-8 h-8 rounded-full bg-[#f1f5f9] text-[#64748b] flex items-center justify-center hover:bg-[#e2e8f0] transition-colors"
                aria-label={isMinimized ? "Expand chat" : "Minimize chat"}
              >
                <Minus className="h-4 w-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="w-8 h-8 rounded-full bg-[#f1f5f9] text-[#64748b] flex items-center justify-center hover:bg-[#e2e8f0] transition-colors"
                aria-label="Close chat"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Messages Area */}
              <div
                className="flex-1 overflow-y-auto px-4 py-4 bg-[#f8fafc] flex flex-col gap-3"
                aria-live="polite"
                aria-label="Chat messages"
              >
                {messages.map((message, index) => {
                  const showTime =
                    index === 0 ||
                    messages[index - 1].timestamp.getTime() - message.timestamp.getTime() > 300000

                  return (
                    <React.Fragment key={message.id}>
                      {showTime && (
                        <div className="text-center text-[0.75rem] text-[#94a3b8] my-2">
                          {formatTime(message.timestamp)}
                        </div>
                      )}
                      <div
                        className={cn(
                          "max-w-[75%] px-4 py-3 rounded-2xl text-[0.875rem] leading-relaxed",
                          message.sender === 'user'
                            ? "bg-[#1e40af] text-white ml-auto rounded-br-sm"
                            : "bg-white text-[#1e293b] border border-[#e2e8f0] rounded-bl-sm shadow-sm"
                        )}
                      >
                        {message.sender === 'bot' ? renderMessageText(message.text) : message.text}
                      </div>
                    </React.Fragment>
                  )
                })}

                {/* Typing Indicator */}
                {isTyping && (
                  <div className="flex gap-1.5 px-4 py-3 bg-white border border-[#e2e8f0] rounded-2xl rounded-bl-sm max-w-[60px] self-start">
                    <div
                      className="w-2 h-2 rounded-full bg-[#94a3b8] animate-bounce"
                      style={{ animationDelay: '0s' }}
                    />
                    <div
                      className="w-2 h-2 rounded-full bg-[#94a3b8] animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    />
                    <div
                      className="w-2 h-2 rounded-full bg-[#94a3b8] animate-bounce"
                      style={{ animationDelay: '0.4s' }}
                    />
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Suggested Questions */}
              {messages.length === 1 && (
                <div className="px-4 py-3 bg-white border-t border-[#e2e8f0]">
                  <div className="flex flex-wrap gap-2">
                    {SUGGESTED_QUESTIONS.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestedQuestion(question)}
                        className="px-3.5 py-2 bg-[#f1f5f9] border border-[#e2e8f0] rounded-2xl text-[0.8125rem] text-[#1e293b] hover:bg-[#e2e8f0] hover:border-[#cbd5e1] transition-all hover:-translate-y-0.5"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Input Area */}
              <div className="px-4 py-3 bg-white border-t border-[#e2e8f0] flex items-end gap-2">
                <div className="flex-1 relative">
                  <textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type a message..."
                    disabled={isTyping}
                    className="w-full px-4 py-3 rounded-3xl border border-[#e2e8f0] text-[0.875rem] resize-none max-h-[100px] focus:outline-none focus:border-[#1e40af] disabled:opacity-50"
                    rows={1}
                    aria-label="Chat input"
                  />
                </div>
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isTyping}
                  className="w-10 h-10 rounded-full bg-[#1e40af] text-white flex items-center justify-center hover:bg-[#1e3a8a] transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
                  aria-label="Send message"
                >
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>

              {/* Disclaimer */}
              <div
                className="px-4 py-2.5 bg-[#fef3c7] border-t border-[#fcd34d] text-[0.75rem] text-[#92400e] leading-relaxed"
                role="complementary"
                aria-label="Disclaimer"
              >
                This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

