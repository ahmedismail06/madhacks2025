"use client"

import React, { useState } from 'react'
import { Graph } from '../../../components'
import network from '../../../public/network_leaflet.json'

const CITY_OPTIONS = [
  'New York, NY',
  'San Francisco, CA',
  'Jersey City, NJ',
  'Boston, MA',
  'Cambridge, MA',
  'Chicago, IL',
  'Miami, FL',
  'Honolulu, HI',
  'Newark, NJ',
  'Philadelphia, PA',
]


// const SAMPLE_POINTS = ...;
// const SAMPLE_POINTS = [
  // { lat: 40.7128, lng: -74.0060 }, // New York
  // { lat: 37.7749, lng: -122.4194 }, // San Francisco
  // { lat: 34.0522, lng: -118.2437 }, // Los Angeles
  // { lat: 41.8781, lng: -87.6298 }, // Chicago
  // { lat: 25.7617, lng: -80.1918 }, // Miami
  // { lat: 39.7392, lng: -104.9903 }, // Denver
  // { lat: 47.6062, lng: -122.3321 }, // Seattle
  // { lat: 29.7604, lng: -95.3698 }, // Houston
// ]

const SAMPLE_POINTS = network

export default function Demo() {
  const [optimizeBy, setOptimizeBy] = useState('latency')
  const [source, setSource] = useState('')
  const [destination, setDestination] = useState('')
  const [result, setResult] = useState<string | null>(null)

  function handleCalculate() {
    if (!source || !destination) {
      alert('Please select both source and destination')
      return
    }
    if (source === destination) {
      alert('Source and destination must be different')
      return
    }

    // Placeholder calculation — later replace with real logic / API call
    const placeholder = `Calculated path from ${source} → ${destination} (optimize by: ${optimizeBy})`
    setResult(placeholder)
    console.log(placeholder)
  }

  return (
    <div className="max-w-7xl mx-auto p-4">
      <div className="flex flex-row flex-nowrap gap-4 overflow-x-auto h-[600px]">
        {/* Left column: selection menu */}
        <aside
          className="w-80 flex-shrink-0 rounded-md p-4"
          style={{
            backgroundColor: 'var(--color-siteBackgroundColor)',
            color: 'var(--color-sitePrimaryColor)'
          }}
        >
          <h2 className="text-lg font-semibold mb-3">Controls</h2>

          {/* Optimize by */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Optimize by</label>
            <select
              value={optimizeBy}
              onChange={(e) => setOptimizeBy(e.target.value)}
              className="w-full rounded-md border px-3 py-2"
              style={{
                backgroundColor: 'var(--color-siteBackgroundColor)',
                color: 'var(--color-sitePrimaryColor)',
                borderColor: 'var(--color-siteSecondaryColor)'
              }}
            >
              <option value="latency">Latency</option>
            </select>
          </div>

          {/* Source */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Source</label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full rounded-md border px-3 py-2"
              style={{
                backgroundColor: 'var(--color-siteBackgroundColor)',
                color: 'var(--color-sitePrimaryColor)',
                borderColor: 'var(--color-siteSecondaryColor)'
              }}
            >
              <option value="">Select source</option>
              {CITY_OPTIONS.map((c) => (
                <option key={`src-${c}`} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Destination */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Destination</label>
            <select
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className="w-full rounded-md border px-3 py-2"
              style={{
                backgroundColor: 'var(--color-siteBackgroundColor)',
                color: 'var(--color-sitePrimaryColor)',
                borderColor: 'var(--color-siteSecondaryColor)'
              }}
            >
              <option value="">Select destination</option>
              {CITY_OPTIONS.map((c) => (
                <option key={`dst-${c}`} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="mt-2">
            <button
              onClick={handleCalculate}
              className="w-full rounded-md bg-blue-600 text-white px-4 py-2 hover:bg-blue-700"
            >
              Calculate Path
            </button>
          </div>

          {result && (
            <div
              className="mt-4 p-2 rounded-md text-sm"
              style={{
                backgroundColor: 'var(--color-sitePrimaryColor)',
                color: 'var(--color-siteTextColor)',
                border: '1px solid var(--color-siteSecondaryColor)'
              }}
            >
              <strong>Result:</strong>
              <div className="mt-1 break-words">{result}</div>
            </div>
          )}
        </aside>

        {/* Right column: graph area (placeholder) */}
        <main
          className="flex-1 rounded-md p-4 min-h-[60vh]"
          style={{
            backgroundColor: 'var(--color-siteBackgroundColor)',
            color: 'var(--color-sitePrimaryColor)'
          }}
        >
          <h2 className="text-lg font-semibold mb-3">Graph</h2>
          <div
            className="h-[60vh] flex items-center justify-center rounded-md w-full"
            style={{
              border: '2px dashed var(--color-siteSecondaryColor)',
              backgroundColor: 'transparent'
            }}
          >
              <div className="w-full h-full">
              <Graph
                edges={SAMPLE_POINTS as any}
                stroke={'var(--color-sitePrimaryColor)'}
                strokeWidth={3}
                showPoints={true}
                pointRadius={5}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}