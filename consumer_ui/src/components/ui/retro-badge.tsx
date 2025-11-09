import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const retroBadgeVariants = cva(
  "inline-flex items-center font-mono text-xs font-semibold uppercase tracking-wider border transition-colors focus:outline-none",
  {
    variants: {
      variant: {
        default:
          "border-trust-primary bg-transparent text-trust-primary",
        secondary:
          "border-trust-secondary bg-transparent text-trust-secondary",
        destructive:
          "border-trust-error bg-transparent text-trust-error",
        success:
          "border-trust-success bg-transparent text-trust-success",
        warning:
          "border-trust-warning bg-transparent text-trust-warning",
        outline: "border-retro-border text-retro-charcoal-light",
        gold: "border-retro-gold bg-transparent text-retro-gold",
      },
      size: {
        default: "px-2.5 py-0.5",
        sm: "px-2 py-0.5 text-xs",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface RetroBadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof retroBadgeVariants> {
  icon?: React.ReactNode
}

function RetroBadge({ className, variant, size, icon, children, ...props }: RetroBadgeProps) {
  return (
    <div className={cn(retroBadgeVariants({ variant, size }), className)} {...props}>
      {icon && <span className="mr-1">{icon}</span>}
      {children}
    </div>
  )
}

export { RetroBadge, retroBadgeVariants }








