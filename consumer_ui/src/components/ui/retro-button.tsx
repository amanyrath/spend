import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const retroButtonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap font-mono text-xs font-semibold uppercase tracking-wider ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-trust-primary text-white hover:bg-trust-primary/90 border border-trust-primary",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 border border-destructive",
        outline:
          "border border-retro-border bg-white hover:bg-muted hover:text-foreground",
        secondary:
          "bg-trust-secondary text-white hover:bg-trust-secondary/80 border border-trust-secondary",
        ghost: "hover:bg-accent hover:text-accent-foreground border border-transparent",
        link: "text-trust-primary underline-offset-4 hover:underline border-0",
        gold: "bg-retro-gold text-retro-charcoal hover:bg-retro-gold/90 border border-retro-gold",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3 text-xs",
        lg: "h-11 px-8 text-sm",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface RetroButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof retroButtonVariants> {
  asChild?: boolean
}

const RetroButton = React.forwardRef<HTMLButtonElement, RetroButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(retroButtonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
RetroButton.displayName = "RetroButton"

export { RetroButton, retroButtonVariants }








