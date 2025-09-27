import { Code, Database, Globe, Zap, Shield, Puzzle } from "lucide-react"

const features = [
  {
    icon: Code,
    title: "Standardized Protocol",
    description: "A unified way for AI models to communicate with external tools and services.",
  },
  {
    icon: Database,
    title: "Data Source Integration",
    description: "Connect to databases, APIs, and file systems with built-in security.",
  },
  {
    icon: Globe,
    title: "Web-Scale Ready",
    description: "Built for modern web applications with real-time capabilities.",
  },
  {
    icon: Zap,
    title: "High Performance",
    description: "Optimized for speed with minimal latency and maximum throughput.",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "Built-in authentication, authorization, and audit logging.",
  },
  {
    icon: Puzzle,
    title: "Easy Integration",
    description: "Simple APIs and SDKs for popular programming languages.",
  },
]

export function Features() {
  return (
    <section className="py-16 md:py-24 bg-black">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-balance text-white">Everything you need to build with MCP</h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto text-balance">
            The Model Context Protocol provides all the tools and infrastructure needed to create powerful AI
            applications.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="bg-gray-950 border border-gray-800 rounded-lg p-6 hover:shadow-lg transition-shadow hover:border-gray-700">
              <div className="w-12 h-12 bg-gray-700 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-gray-300" />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-white">{feature.title}</h3>
              <p className="text-gray-300 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
