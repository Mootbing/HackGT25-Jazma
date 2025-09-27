import { Button } from "@/components/ui/button"

export function Header() {
  return (
    <header className="border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-foreground rounded-sm flex items-center justify-center">
              <div className="w-3 h-3 bg-background rounded-sm"></div>
            </div>
            <span className="font-semibold text-lg">jasma</span>
          </div>
        </div>
      </div>
    </header>
  )
}
