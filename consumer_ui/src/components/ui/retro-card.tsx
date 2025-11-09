import * as React from "react"
import { cn } from "@/lib/utils"

export interface RetroCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "dashed" | "gold-accent"
}

const RetroCard = React.forwardRef<HTMLDivElement, RetroCardProps>(
  ({ className, variant = "default", ...props }, ref) => {
    const borderClass = variant === "dashed" 
      ? "border-dashed border-retro-border" 
      : variant === "gold-accent"
      ? "border-l-4 border-l-retro-gold border-retro-border"
      : "border border-retro-border"
    
    return (
      <div
        ref={ref}
        className={cn(
          "bg-white text-retro-charcoal shadow-sm",
          borderClass,
          className
        )}
        {...props}
      />
    )
  }
)
RetroCard.displayName = "RetroCard"

const RetroCardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 px-6 pt-6 pb-4 border-b border-retro-border", className)}
    {...props}
  />
))
RetroCardHeader.displayName = "RetroCardHeader"

const RetroCardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-base font-bold leading-none tracking-wide font-mono text-[#222222] uppercase",
      className
    )}
    {...props}
  />
))
RetroCardTitle.displayName = "RetroCardTitle"

const RetroCardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-xs text-retro-charcoal-light font-mono uppercase tracking-wider", className)}
    {...props}
  />
))
RetroCardDescription.displayName = "RetroCardDescription"

const RetroCardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("px-6 pt-8 pb-6", className)} {...props} />
))
RetroCardContent.displayName = "RetroCardContent"

const RetroCardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0 border-t border-retro-border", className)}
    {...props}
  />
))
RetroCardFooter.displayName = "RetroCardFooter"

export { RetroCard, RetroCardHeader, RetroCardFooter, RetroCardTitle, RetroCardDescription, RetroCardContent }


