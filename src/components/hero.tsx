import { Button } from "@/components/ui/button"
import { fkGrotesk } from "@/app/fonts"
import { ArrowRight, Play } from "lucide-react"
import { WordRotate } from "@/components/ui/word-rotate"
import SmoothScrollLink from "@/components/ui/smooth-scroll-link"

export function Hero() {
  return (
    <section className="relative py-24 md:py-32 overflow-hidden">
      <div className="container mx-auto px-4 text-center relative z-10">
        <div className="inline-flex items-center gap-1 px-3 py-1 rounded-full border border-border bg-muted/50 text-sm text-muted-foreground mb-4">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          MCP Protocol v1.0 Now Available
        </div>

        <h1 className={`${fkGrotesk.className} text-4xl md:text-6xl lg:text-7xl font-bold text-balance mb-6 leading-tight`} style={{ fontFamily: 'var(--font-grotesk)' }}>
          <span className="text-muted-foreground font-normal leading-tight">
            Let Agents Share {" "}
            <span className="block mx-auto w-[13ch] text-center relative top-[1px]">
              <WordRotate
                words={["Knowledge", "Documentation", "Context"]}
                className="leading-[inherit] align-baseline shiny-text"
              />
            </span>
          </span>
        </h1>

        <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto mb-12 text-balance leading-relaxed">
            Connect coding agents to a shared bugfix knowledge base with a standardized protocol. Build faster, smarter developer tools that can instantly retrieve past fixes and apply them in real time.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <Button size="lg" className="gap-2">
            Get Started
            <ArrowRight className="w-4 h-4" />
          </Button>
          <Button asChild variant="outline" size="lg" className="gap-2 bg-transparent">
            <SmoothScrollLink href="#demo" aria-label="Watch Demo">
              <Play className="w-4 h-4" />
              Watch Demo
            </SmoothScrollLink>
          </Button>
        </div>

        {/* Safari Mockup with Mastercard-style Overlapping Circles */}
        <div className="max-w-full mx-auto mt-24 relative px-8">
          {/* Large Overlapping Circles Surrounding Mockup */}
          <div className="absolute inset-0 flex items-center justify-center">
            {/* Golden Blob */}
            <div className="absolute blob-move blob-delay-2s -translate-x-64">
              <div className="w-[800px] h-[800px] bg-gradient-to-br from-yellow-400 to-amber-600 opacity-40 blur-2xl blob-shape"></div>
            </div>

            {/* Silver Blob */}
            <div className="absolute blob-move blob-move-slow translate-x-64">
              <div className="w-[800px] h-[800px] bg-gradient-to-br from-gray-300 to-gray-500 opacity-40 blur-2xl blob-shape"></div>
            </div>

            {/* Overlapping Center Blob */}
            <div className="absolute blob-move blob-move-fast">
              <div className="w-[800px] h-[800px] bg-gradient-to-br from-yellow-200 to-gray-400 opacity-30 blur-3xl blob-shape"></div>
            </div>
          </div>
          
          {/* Simple Rectangle Outline for Video Overlay */}
          <div className="relative z-10" id="demo">
            <div 
              className="w-full mx-auto bg-black border-2 border-white/20 rounded-2xl"
              style={{
                aspectRatio: "1203/753",
                maxWidth: "1203px"
              }}
            >
              {/* This rectangle is ready for video overlay */}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
