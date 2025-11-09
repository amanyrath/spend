import * as React from "react"
import { sendChatMessage } from "@/lib/api"

export interface ChatMessage {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
}

interface ChatContextType {
  messages: ChatMessage[]
  addMessage: (message: ChatMessage) => void
  sendMessage: (text: string, userId: string) => Promise<void>
  clearMessages: () => void
  isLoading: boolean
}

export const ChatContext = React.createContext<ChatContextType | undefined>(undefined)

const STORAGE_KEY_PREFIX = 'spendsense_chat_'

export function ChatProvider({ children, userId }: { children: React.ReactNode; userId: string }) {
  const [messages, setMessages] = React.useState<ChatMessage[]>([
    {
      id: '1',
      text: "Hello! I can help you understand your finances. What would you like to know?",
      sender: 'bot',
      timestamp: new Date(),
    },
  ])
  const [isLoading, setIsLoading] = React.useState(false)

  const storageKey = `${STORAGE_KEY_PREFIX}${userId}`

  // Load messages from localStorage on mount and when userId changes
  React.useEffect(() => {
    try {
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        const parsed = JSON.parse(stored)
        setMessages(parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        })))
      } else {
        // Reset to initial message if no stored history
        setMessages([
          {
            id: '1',
            text: "Hello! I can help you understand your finances. What would you like to know?",
            sender: 'bot',
            timestamp: new Date(),
          },
        ])
      }
    } catch (error) {
      console.error('Failed to load chat history:', error)
    }
  }, [userId, storageKey])

  // Save messages to localStorage whenever they change
  React.useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(messages))
    } catch (error) {
      console.error('Failed to save chat history:', error)
    }
  }, [messages, storageKey])

  const addMessage = React.useCallback((message: ChatMessage) => {
    setMessages((prev) => [...prev, message])
  }, [])

  const sendMessage = React.useCallback(async (text: string, userId: string) => {
    if (!text.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
    }

    addMessage(userMessage)
    setIsLoading(true)

    try {
      const response = await sendChatMessage(userId, text.trim())
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: response.data.response,
        sender: 'bot',
        timestamp: new Date(),
      }
      addMessage(botMessage)
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, I encountered an error: ${error.message}`,
        sender: 'bot',
        timestamp: new Date(),
      }
      addMessage(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }, [addMessage])

  const clearMessages = React.useCallback(() => {
    const initialMessage: ChatMessage = {
      id: '1',
      text: "Hello! I can help you understand your finances. What would you like to know?",
      sender: 'bot',
      timestamp: new Date(),
    }
    setMessages([initialMessage])
  }, [])

  const value = React.useMemo(
    () => ({
      messages,
      addMessage,
      sendMessage,
      clearMessages,
      isLoading,
    }),
    [messages, addMessage, sendMessage, clearMessages, isLoading]
  )

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}
