import React from 'react'
import { Navbar, RouteCalculator } from '../components'
import Footer from '../components/footer'
import network from '../public/network_leaflet.json'

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'var(--color-siteBackgroundColor)' }}>
      <Navbar />
      <RouteCalculator networkData={network} />
      <div className="flex-1"></div>
      <Footer />
    </div>
  )
}
