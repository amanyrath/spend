import * as React from "react"
import { ChatContext } from "./chat-context"

export function useChat() {
  const context = React.useContext(ChatContext)
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider')
  }
  return context
}







