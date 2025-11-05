import * as React from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { RationaleBox } from "@/components/rationale-box"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { 
  CreditCard, 
  PiggyBank, 
  TrendingUp, 
  DollarSign,
  BookOpen,
  FileText
} from "lucide-react"

interface EducationCardProps {
  title: string
  description: string
  rationale: string
  contentId: string
  category?: string
  fullContent?: string
  tags?: string[]
  className?: string
}

const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  credit: CreditCard,
  savings: PiggyBank,
  budgeting: TrendingUp,
  debt: DollarSign,
  spending: TrendingUp,
  investing: PiggyBank,
  planning: BookOpen,
  general: BookOpen,
}

const categoryColors: Record<string, string> = {
  credit: "bg-blue-100 text-blue-800",
  savings: "bg-green-100 text-green-800",
  budgeting: "bg-purple-100 text-purple-800",
  debt: "bg-red-100 text-red-800",
  spending: "bg-purple-100 text-purple-800",
  investing: "bg-green-100 text-green-800",
  planning: "bg-blue-100 text-blue-800",
  general: "bg-gray-100 text-gray-800",
}

export function EducationCard({
  title,
  description,
  rationale,
  contentId: _contentId,
  category = "general",
  fullContent,
  tags,
  className,
}: EducationCardProps) {
  const [expanded, setExpanded] = React.useState(false)
  const Icon = categoryIcons[category] || FileText
  const categoryColor = categoryColors[category] || categoryColors.general

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Icon className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <CardTitle className="text-xl mb-2">{title}</CardTitle>
              <CardDescription className="text-base">{description}</CardDescription>
              {tags && tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {tags.map((tag, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      #{tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
          <Badge className={categoryColor}>{category}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <RationaleBox rationale={rationale} />
        {expanded && fullContent && (
          <div className="pt-4 border-t">
            <div className="prose prose-sm max-w-none text-foreground">
              <div className="whitespace-pre-wrap text-sm leading-relaxed">{fullContent}</div>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button
          onClick={() => setExpanded(!expanded)}
          variant={expanded ? "outline" : "default"}
          className="w-full"
        >
          {expanded ? "Show Less" : "Learn More"}
        </Button>
      </CardFooter>
    </Card>
  )
}

