"use client"

import React, { useState } from 'react'
import dynamic from 'next/dynamic'

const Graph = dynamic(() => import('./Graph'), { ssr: false })

const CITY_OPTIONS = {"New York": 49233, "Los Angeles": 48177, "Chicago": 730132, "Miami": 794874, "Houston": 963794, "Dallas": 222262, "Philadelphia": 359683, "Atlanta": 81033, "Washington": 990965, "Boston": 687668, "Phoenix": 273331, "Detroit": 59112, "Seattle": 377822, "San Francisco": 388257, "San Diego": 966374, "Minneapolis": 373130, "Tampa": 230424, "Brooklyn": 613078, "Denver": 704506, "Queens": 131010, "Riverside": 40060, "Las Vegas": 285824, "Baltimore": 616410, "St. Louis": 409624, "Portland": 178183, "San Antonio": 451327, "Sacramento": 865262, "Austin": 532265, "Orlando": 196284, "San Juan": 339601, "San Jose": 549660, "Indianapolis": 762457, "Pittsburgh": 180964, "Cincinnati": 333274, "Manhattan": 896573, "Kansas City": 212923, "Cleveland": 199409, "Columbus": 692576, "Bronx": 526436, "Charlotte": 901048, "Virginia Beach": 942990, "Jacksonville": 519058, "Milwaukee": 911113, "Providence": 11974, "Nashville": 924671, "Salt Lake City": 742226, "Raleigh": 486410, "Richmond": 890976, "Memphis": 299587, "Oklahoma City": 806931, "Hartford": 793963, "Louisville": 538313, "Buffalo": 17330, "Fort Worth": 596181, "Bridgeport": 303369, "New Orleans": 24175, "Tucson": 465825, "El Paso": 89135, "Omaha": 524994, "McAllen": 514290, "Birmingham": 304761, "Albuquerque": 388205, "Tulsa": 613174, "Charleston": 500044, "Fresno": 577513, "Rochester": 244737, "Dayton": 587883, "Cape Coral": 159413, "Provo": 362397, "Colorado Springs": 669275, "Mission Viejo": 767642, "Allentown": 986996, "Baton Rouge": 185474, "Ogden": 288189, "Knoxville": 347983, "Grand Rapids": 533911, "Columbia": 552304, "Albany": 638986, "Bakersfield": 215684, "New Haven": 302053, "Des Moines": 116642, "Palm Bay": 223794, "Akron": 919737, "Concord": 30530, "Mesa": 300949, "Wichita": 213611}

type RouteCalculatorProps = {
  networkData: any
}

export default function RouteCalculator({ networkData }: RouteCalculatorProps) {
  const [latencyWeight, setLatencyWeight] = useState('0.5')
  const [riskWeight, setRiskWeight] = useState('0.5')
  const [costWeight, setCostWeight] = useState('0.5')
  const [algorithm, setAlgorithm] = useState('dijkstra')
  const [source, setSource] = useState('')
  const [destination, setDestination] = useState('')
  const [result, setResult] = useState<string | null>(null)
  const [pathData, setPathData] = useState<Array<{x: number, y: number, type: string}> | null>(null)

  async function handleCalculate() {
    if (!source || !destination) {
      alert('Please select both source and destination')
      return
    }
    if (source === destination) {
      alert('Source and destination must be different')
      return
    }

    try {
      setResult('Calculating route...')
      setPathData(null)

      // First, make POST request to initiate route calculation
      const params = new URLSearchParams()
      params.set('start', source)
      params.set('goal', destination)
      params.set('w_lat', latencyWeight)
      params.set('w_traffic', costWeight)
      params.set('w_risk', riskWeight)
      params.set('algorithm', algorithm)

      const postUrl = `http://127.0.0.1:8000/api/route?${params.toString()}`
      console.log('POST request:', postUrl)

      const postResponse = await fetch(postUrl, {
        method: 'POST',
      })

      if (!postResponse.ok) {
        throw new Error(`POST request failed: ${postResponse.status}`)
      }

      // Then fetch the result
      const resultUrl = `http://127.0.0.1:8000/api/route/result`
      console.log('Fetching result:', resultUrl)

      const response = await fetch(resultUrl)
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`)
      }

      const data = await response.json()
      console.log('API Response:', data)

      if (data.path && Array.isArray(data.path)) {
        setPathData(data.path)
        setResult(`Path found with ${data.path.length} nodes`)
      } else {
        setResult('No path data in response')
      }
    } catch (err) {
      console.error('Error fetching route:', err)
      setResult(`Error: ${(err as Error).message}`)
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-4 flex-1 w-full">
      <div className="flex flex-row flex-nowrap gap-4 overflow-x-auto h-full">
        {/* Left column: selection menu */}
        <aside
          className="w-80 flex-shrink-0 rounded-md p-4"
          style={{
            backgroundColor: 'var(--color-siteBackgroundColor)',
            color: 'var(--color-sitePrimaryColor)'
          }}
        >
          <h2 className="text-lg font-semibold mb-3">Controls</h2>

          {/* Weights for optimization types */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Latency weight</label>
            <select
              value={latencyWeight}
              onChange={(e) => setLatencyWeight(e.target.value)}
              className="w-full rounded-md border px-3 py-2 mb-2"
              style={{
                backgroundColor: 'var(--color-siteBackgroundColor)',
                color: 'var(--color-sitePrimaryColor)',
                borderColor: 'var(--color-siteSecondaryColor)'
              }}
            >
              {Array.from({ length: 11 }).map((_, i) => {
                const v = (i / 10).toFixed(1)
                return (
                  <option key={`lat-${v}`} value={v}>
                    {v}
                  </option>
                )
              })}
            </select>

            <label className="block text-sm font-medium mb-1">Risk weight</label>
            <select
              value={riskWeight}
              onChange={(e) => setRiskWeight(e.target.value)}
              className="w-full rounded-md border px-3 py-2 mb-2"
              style={{
                backgroundColor: 'var(--color-siteBackgroundColor)',
                color: 'var(--color-sitePrimaryColor)',
                borderColor: 'var(--color-siteSecondaryColor)'
              }}
            >
              {Array.from({ length: 11 }).map((_, i) => {
                const v = (i / 10).toFixed(1)
                return (
                  <option key={`risk-${v}`} value={v}>
                    {v}
                  </option>
                )
              })}
            </select>

            <label className="block text-sm font-medium mb-1">Cost weight</label>
            <select
              value={costWeight}
              onChange={(e) => setCostWeight(e.target.value)}
              className="w-full rounded-md border px-3 py-2"
              style={{
                backgroundColor: 'var(--color-siteBackgroundColor)',
                color: 'var(--color-sitePrimaryColor)',
                borderColor: 'var(--color-siteSecondaryColor)'
              }}
            >
              {Array.from({ length: 11 }).map((_, i) => {
                const v = (i / 10).toFixed(1)
                return (
                  <option key={`cost-${v}`} value={v}>
                    {v}
                  </option>
                )
              })}
            </select>
          </div>

          {/* Algorithm selector */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Algorithm</label>
            <select
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value)}
              className="w-full rounded-md border px-3 py-2"
              style={{
                backgroundColor: 'var(--color-siteBackgroundColor)',
                color: 'var(--color-sitePrimaryColor)',
                borderColor: 'var(--color-siteSecondaryColor)'
              }}
            >
              <option value="dijkstra">Dijkstra</option>
              <option value="a-star">A*</option>
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
              {Object.keys(CITY_OPTIONS).map((c) => (
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
              {Object.keys(CITY_OPTIONS).map((c) => (
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

        {/* Right column: graph area */}
        <main
          className="flex-1 rounded-md p-4 flex flex-col"
          style={{
            backgroundColor: 'var(--color-siteBackgroundColor)',
            color: 'var(--color-sitePrimaryColor)'
          }}
        >
          <h2 className="text-lg font-semibold mb-3">Graph</h2>
          <div
            className="flex-1 flex items-center justify-center rounded-md w-full"
            style={{
              border: '2px dashed var(--color-siteSecondaryColor)',
              backgroundColor: 'transparent'
            }}
          >
            <div className="w-full h-full">
              <Graph
                edges={networkData as any}
                stroke={'#dddddd'}
                strokeWidth={3.5}
                showPoints={true}
                pointRadius={5}
                pathData={pathData}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
