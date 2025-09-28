'use client'

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { fkGrotesk } from "@/app/fonts"
import { Check, Copy, ExternalLink } from "lucide-react"

export function InstallCursor() {
  const configJson = `{
  "mcpServers": {
    "jazma": {
      "url": "https://jasma.workers.dev/mcp"
    }
  }
}`

  const curlList = `curl -X POST https://jasma.workers.dev/mcp \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'`

  const [copiedConfig, setCopiedConfig] = useState(false)
  const [copiedCurl, setCopiedCurl] = useState(false)

  const copy = async (text: string, which: "config" | "curl") => {
    try {
      await navigator.clipboard.writeText(text)
      if (which === "config") {
        setCopiedConfig(true)
        setTimeout(() => setCopiedConfig(false), 1800)
      } else {
        setCopiedCurl(true)
        setTimeout(() => setCopiedCurl(false), 1800)
      }
    } catch {}
  }

  return (
    <section id="install" className="py-16 md:py-24">
      <div className="container mx-auto px-4">
        <div className="text-center mb-10">
          <h2 className={`${fkGrotesk.className} text-3xl md:text-4xl font-bold text-balance mb-3`} style={{ fontFamily: 'var(--font-grotesk)' }}>
            Install in Cursor
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-balance">
            Add the Jazma MCP server to Cursor in seconds. No local setup required.
          </p>
        </div>

        <div className="relative max-w-6xl mx-auto">
          <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-br from-white/30 via-white/10 to-transparent opacity-30 blur"></div>
          <div className="relative rounded-2xl border border-white/15 bg-white/5 backdrop-blur-xl shadow-2xl">
            {/* Top bar */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10">
              <div className="w-3 h-3 rounded-full bg-red-500/90"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-400/90"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/90"></div>
              <span className="ml-3 text-xs text-white/60">Jazma MCP Installer</span>
            </div>

            <div className="p-6 md:p-8">
              <div className="grid grid-cols-1 lg:grid-cols-7 gap-8">
                {/* Steps */}
                <div className="lg:col-span-2">
                  <h3 className="text-lg font-semibold mb-4">Steps</h3>
                  <ol className="list-decimal list-inside space-y-3 text-sm md:text-base">
                    <li>Open Cursor → Settings → MCP</li>
                    <li>Click <span className="font-medium">Add new global MCP server</span></li>
                    <li>Paste the config JSON shown → Save</li>
                    <li>Click the refresh icon next to <span className="font-mono">jazma</span></li>
                  </ol>

                  <a
                    href="https://jasma.workers.dev/"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 mt-6 text-sm text-primary hover:underline"
                  >
                    Visit server docs
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>

                {/* Divider */}
                <div className="hidden lg:block lg:col-span-1">
                  <div className="h-full w-px bg-gradient-to-b from-white/20 via-white/10 to-transparent mx-auto"></div>
                </div>

                {/* Code blocks */}
                <div className="lg:col-span-4 space-y-6">
                  <div className="rounded-lg border border-white/10 overflow-hidden bg-white/5">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                      <span className="text-xs uppercase tracking-wide text-white/60">Cursor config (mcp.json)</span>
                      <Button variant="outline" size="sm" onClick={() => copy(configJson, "config")} className="gap-2">
                        {copiedConfig ? (<><Check className="w-4 h-4" />Copied</>) : (<><Copy className="w-4 h-4" />Copy</>)}
                      </Button>
                    </div>
                    <div className="p-4">
                      <div className="rounded-md p-4 overflow-x-auto bg-black/50 ring-1 ring-white/10">
                        <pre className="font-mono text-sm leading-relaxed text-white/90"><code>{configJson}</code></pre>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg border border-white/10 overflow-hidden bg-white/5">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                      <span className="text-xs uppercase tracking-wide text-white/60">Test connection (curl)</span>
                      <Button variant="outline" size="sm" onClick={() => copy(curlList, "curl")} className="gap-2">
                        {copiedCurl ? (<><Check className="w-4 h-4" />Copied</>) : (<><Copy className="w-4 h-4" />Copy</>)}
                      </Button>
                    </div>
                    <div className="p-4">
                      <div className="rounded-md p-4 overflow-x-auto bg-black/50 ring-1 ring-white/10">
                        <pre className="font-mono text-sm leading-relaxed text-white/90"><code>{curlList}</code></pre>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

