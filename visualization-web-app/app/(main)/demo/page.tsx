"use client"

import React, { useState, useRef } from 'react'
import { Graph } from '../../../components'
import network from '../../../public/network_leaflet.json'

const CITY_OPTIONS = {"New York": 49233, "Los Angeles": 48177, "Chicago": 730132, "Miami": 794874, "Houston": 963794, "Dallas": 222262, "Philadelphia": 359683, "Atlanta": 81033, "Washington": 990965, "Boston": 687668, "Phoenix": 273331, "Detroit": 59112, "Seattle": 377822, "San Francisco": 388257, "San Diego": 966374, "Minneapolis": 373130, "Tampa": 230424, "Brooklyn": 613078, "Denver": 704506, "Queens": 131010, "Riverside": 40060, "Las Vegas": 285824, "Baltimore": 616410, "St. Louis": 409624, "Portland": 178183, "San Antonio": 451327, "Sacramento": 865262, "Austin": 532265, "Orlando": 196284, "San Juan": 339601, "San Jose": 549660, "Indianapolis": 762457, "Pittsburgh": 180964, "Cincinnati": 333274, "Manhattan": 896573, "Kansas City": 212923, "Cleveland": 199409, "Columbus": 692576, "Bronx": 526436, "Charlotte": 901048, "Virginia Beach": 942990, "Jacksonville": 519058, "Milwaukee": 911113, "Providence": 11974, "Nashville": 924671, "Salt Lake City": 742226, "Raleigh": 486410, "Richmond": 890976, "Memphis": 299587, "Oklahoma City": 806931, "Hartford": 793963, "Louisville": 538313, "Buffalo": 17330, "Fort Worth": 596181, "Bridgeport": 303369, "New Orleans": 24175, "Tucson": 465825, "El Paso": 89135, "Omaha": 524994, "McAllen": 514290, "Birmingham": 304761, "Albuquerque": 388205, "Tulsa": 613174, "Charleston": 500044, "Fresno": 577513, "Rochester": 244737, "Dayton": 587883, "Cape Coral": 159413, "Provo": 362397, "Colorado Springs": 669275, "Mission Viejo": 767642, "Allentown": 986996, "Baton Rouge": 185474, "Ogden": 288189, "Knoxville": 347983, "Grand Rapids": 533911, "Columbia": 552304, "Albany": 638986, "Bakersfield": 215684, "New Haven": 302053, "Des Moines": 116642, "Palm Bay": 223794, "Akron": 919737, "Concord": 30530, "Mesa": 300949, "Wichita": 213611}

const SAMPLE_POINTS = network

export default function Demo() {
  const [latencyWeight, setLatencyWeight] = useState('0.5')
  const [riskWeight, setRiskWeight] = useState('0.5')
  const [costWeight, setCostWeight] = useState('0.5')
  const [algorithm, setAlgorithm] = useState('dijkstra')
  const [source, setSource] = useState('')
  const [destination, setDestination] = useState('')
  const [result, setResult] = useState<string | null>(null)
  const streamAbortRef = useRef<AbortController | null>(null)

  async function handleCalculate() {
    if (!source || !destination) {
      alert('Please select both source and destination')
      return
    }
    if (source === destination) {
      alert('Source and destination must be different')
      return
    }

    // Build weights array [latency, cost, risk] per user request (latency, cost, risk order)
    const weights = [parseFloat(latencyWeight), parseFloat(costWeight), parseFloat(riskWeight)]

    // API host
    const API_HOST = '34.27.157.215'

    try {
      // Abort any previous streaming request
      if (streamAbortRef.current) {
        streamAbortRef.current.abort()
        streamAbortRef.current = null
      }

      // Perform health check
      const healthURL = `http://${API_HOST}:8000/`
      console.log('Performing health check:', healthURL)

      const healthResp = await fetch(healthURL, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      })
      
      if (!healthResp.ok) {
        const txt = await healthResp.text()
        throw new Error(`route id request failed: ${healthResp.status} ${txt}`)
      }

      console.log('API health check passed')

      // Make GET request to /api/route with from,to,weights,algorithm as query params
      const params = new URLSearchParams()
      params.set('start', source)
      params.set('goal', destination)
      // algorithm: 'dijkstra' or 'a-star'
      params.set('w_lat', weights[0].toString())
      params.set('w_traffic', weights[1].toString())
      params.set('w_risk', weights[2].toString())
      params.set('algorithm', algorithm)

      const routeUrl = `http://${API_HOST}:8000/api/route?${params.toString()}`
      console.log('Requesting job id:', routeUrl)

      const idResp = await fetch(routeUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json'
        }
      })

      if (!idResp.ok) {
        const txt = await idResp.text()
        throw new Error(`route id request failed: ${idResp.status} ${txt}`)
      }

      const idJson = await idResp.json()
      // const jobId = idJson?.id ?? idJson?.job_id ?? idJson?.job ?? idJson
      const jobId = idJson.jobId || idJson.job_id || idJson.id;
      console.log('Received job id:', jobId)
      setResult(`Started job ${jobId}`)

      // Now POST to the streaming endpoint
      const streamUrl = `http://${API_HOST}:8000/api/route/stream?id=${encodeURIComponent(jobId)}`

      const abortCtrl = new AbortController()
      streamAbortRef.current = abortCtrl

      console.log('[STREAM] Starting stream:', streamUrl);

      const streamResp = await fetch(streamUrl, {
        method: 'GET',
        signal: abortCtrl.signal,
        headers: {
          'Accept': 'text/event-stream, application/json, text/plain'
        }
      })

      if (!streamResp.ok || !streamResp.body) {
        const txt = await streamResp.text()
        throw new Error(`stream request failed: ${streamResp.status} ${txt}`)
      }

      // Read streaming body and print chunks to console
      const reader = streamResp.body.getReader()
      const decoder = new TextDecoder()
      let done = false

      while (!done) {
        const { value, done: rdone } = await reader.read()
        done = rdone
        if (value) {
          const chunk = decoder.decode(value, { stream: true })
          // Log raw chunk; backend may send JSON lines or SSE
          console.log('[STREAM]', chunk)
        }
      }

      console.log('Stream completed')
      setResult((prev) => (prev ? prev + ' — stream completed' : 'stream completed'))
      streamAbortRef.current = null
    } catch (err) {
      console.error('Error during route/stream:', err)
      setResult(`Error: ${(err as Error).message}`)
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-4">
      <div className="flex flex-row flex-nowrap gap-4 overflow-x-auto">
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
                stroke={'#dddddd'}
                strokeWidth={3.5}
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