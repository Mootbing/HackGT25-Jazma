import { Header } from "@/components/header"
import { Hero } from "@/components/hero"
import { Particles } from "@/components/ui/particles"
import { InstallCursor } from "@/components/install-cursor"

export default function Home() {
  return (
    <div className="min-h-screen bg-background relative">
      {/* Particles background - full viewport */}
      <Particles
        className="fixed inset-0 w-screen h-screen z-0"
        quantity={300}
        ease={80}
        color="#ffffff"
        size={0.5}
        staticity={50}
      />
      <Header />
      <main>
        <Hero />
        <InstallCursor />
      </main>
    </div>
  )
}
