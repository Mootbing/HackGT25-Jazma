export function ComputerMockup() {
  return (
    <section className="py-16 md:py-24">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-card border border-border rounded-lg p-8 shadow-lg">
            <div className="bg-muted rounded-lg p-6 font-mono text-sm">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              </div>
              <div className="space-y-2">
                <div className="text-green-400">$ npm install @modelcontextprotocol/client</div>
                <div className="text-blue-400">import &#123; Client &#125; from &apos;@modelcontextprotocol/client&apos;</div>
                <div className="text-gray-300">const client = new Client(&#123;</div>
                <div className="text-gray-300 ml-4">server: &apos;your-mcp-server&apos;,</div>
                <div className="text-gray-300 ml-4">capabilities: [&apos;resources&apos;, &apos;tools&apos;]</div>
                <div className="text-gray-300">&#125;)</div>
                <div className="text-gray-300">await client.connect()</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
