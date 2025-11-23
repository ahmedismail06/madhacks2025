"use client"

import React, { useEffect, useRef, useState } from 'react'
import { MapContainer, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

type PathNode = {
	x: number // latitude
	y: number // longitude
	type: string
}

type StreamDataItem = any

function TestPoint({ lat, lng, label }: { lat: number; lng: number; label?: string }) {
    const map = useMap()

    useEffect(() => {
        if (!map) return

        const marker = L.circleMarker([lat, lng], {
            radius: 6,
            fillColor: '#ff0000',
            color: '#ff0000',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8,
        }).addTo(map)

        if (label) {
            marker.bindPopup(label)
        }

        return () => {
            if (marker && map.hasLayer(marker)) {
                map.removeLayer(marker)
            }
        }
    }, [lat, lng, map, label])

    return null
}

type GraphProps = {
	edges: any // GeoJSON or array of line segments
	stroke?: string
	strokeWidth?: number
	showPoints?: boolean
	pointRadius?: number
	className?: string
	streamData?: StreamDataItem[]
}

function GeoJSONLayer({
	edges,
	stroke,
	strokeWidth,
}: {
	edges: any
	stroke: string
	strokeWidth: number
}) {
	const map = useMap()
	const geoJsonLayerRef = useRef<L.GeoJSON | null>(null)

	useEffect(() => {
		if (!map || !edges) return

		// Remove existing layer
		if (geoJsonLayerRef.current) {
			map.removeLayer(geoJsonLayerRef.current)
		}

		// Convert edges array to GeoJSON FeatureCollection
		let geojson: GeoJSON.FeatureCollection

		if (Array.isArray(edges) && edges[0] && Array.isArray(edges[0][0])) {
			// edges is an array of line segments: [[[lat, lng], [lat, lng]], ...]
			const features = edges.map((segment, idx) => ({
				type: 'Feature' as const,
				properties: { id: idx },
				geometry: {
					type: 'LineString' as const,
					coordinates: segment.map(([lat, lng]: [number, number]) => [lng, lat]), // GeoJSON uses [lon, lat]
				},
			}))
			geojson = { type: 'FeatureCollection' as const, features }
		} else {
			// Assume it's already GeoJSON format
			geojson = edges
		}

		// Create GeoJSON layer with styling
		const geoJsonLayer = L.geoJSON(geojson, {
			style: {
				color: stroke,
				weight: strokeWidth,
				opacity: 0.8,
				lineCap: 'round',
				lineJoin: 'round',
			},
		})

		geoJsonLayer.addTo(map)
		geoJsonLayerRef.current = geoJsonLayer

		// Auto-fit bounds
		const bounds = geoJsonLayer.getBounds()
		if (bounds.isValid()) {
			map.fitBounds(bounds, { padding: [50, 50] })
		}

		return () => {
			if (geoJsonLayerRef.current && map.hasLayer(geoJsonLayerRef.current)) {
				map.removeLayer(geoJsonLayerRef.current)
			}
		}
	}, [edges, map, stroke, strokeWidth])

	return null
}

function MapBackground({ color = '#ffffff' }: { color?: string }) {
    const map = useMap()
    useEffect(() => {
        const c = map.getContainer()
        if (c && c.style) c.style.backgroundColor = color
    }, [map, color])
    return null
}

function PathOverlay({ streamQueue }: { streamQueue: StreamDataItem[] }) {
	const map = useMap()
	const [pathData, setPathData] = useState<PathNode[] | null>(null)
	const [noPath, setNoPath] = useState(false)
	const pathLayerRef = useRef<L.Polyline | null>(null)
	const markersRef = useRef<L.CircleMarker[]>([])

	useEffect(() => {
		console.log('[PathOverlay] streamQueue updated, length:', streamQueue.length)
		if (!map || streamQueue.length === 0) return

		// Process queue: find item with final-path or no-path event
		for (const element of streamQueue) {
			console.log('[PathOverlay] Processing element:', element)
			if (!element || typeof element !== 'object') continue

      console.log("Heres the event")
      console.log(element.event)

			if (element.event === 'final-path') {
				// Extract path
				const path = element?.data?.path
				console.log('[PathOverlay] Found final-path, path data:', path)
				if (Array.isArray(path) && path.length > 0) {
					console.log('[PathOverlay] Setting path data with', path.length, 'nodes')
					setPathData(path)
					setNoPath(false)
					return
				} else {
					console.log('[PathOverlay] Path is empty or not an array')
				}
			} else if (element.event === 'no-path') {
				console.log('[PathOverlay] Found no-path event')
				setNoPath(true)
				setPathData(null)
				return
			}
		}
	}, [streamQueue, map])

	useEffect(() => {
		console.log('[PathOverlay] pathData updated:', pathData)
		if (!map) return

		// Clean up previous path and markers
		if (pathLayerRef.current && map.hasLayer(pathLayerRef.current)) {
			map.removeLayer(pathLayerRef.current)
		}
		markersRef.current.forEach((m) => {
			if (map.hasLayer(m)) map.removeLayer(m)
		})
		markersRef.current = []

		if (!pathData || pathData.length === 0) {
			console.log('[PathOverlay] No path data to render')
			return
		}

		console.log('[PathOverlay] Drawing path with', pathData.length, 'nodes')
		// Draw polyline connecting all nodes
		const coords: [number, number][] = pathData.map((node) => [node.y, node.x])
		console.log('[PathOverlay] Coordinates:', coords.slice(0, 3), '...', coords.length, 'total')
		const polyline = L.polyline(coords, {
			color: '#0066ff',
			weight: 4,
			opacity: 0.8,
			lineCap: 'round',
			lineJoin: 'round',
		}).addTo(map)
		pathLayerRef.current = polyline
		console.log('[PathOverlay] Polyline added to map')

		// Draw markers for special node types
		pathData.forEach((node) => {
			if (node.type === 'regen_spot') {
				const marker = L.circleMarker([node.y, node.x], {
					radius: 5,
					fillColor: '#00ff00',
					color: '#00aa00',
					weight: 2,
					opacity: 1,
					fillOpacity: 0.8,
				}).addTo(map)
				markersRef.current.push(marker)
			} else if (node.type === 'routing_node') {
				const marker = L.circleMarker([node.y, node.x], {
					radius: 5,
					fillColor: '#87ceeb',
					color: '#4682b4',
					weight: 2,
					opacity: 1,
					fillOpacity: 0.8,
				}).addTo(map)
				markersRef.current.push(marker)
			}
			// network_node and city_connection: no marker drawn
		})
		console.log('[PathOverlay] Added', markersRef.current.length, 'markers')

		// Fit map to path bounds
		if (coords.length > 0) {
			const bounds = L.latLngBounds(coords)
			map.fitBounds(bounds, { padding: [50, 50] })
			console.log('[PathOverlay] Fitted bounds to path')
		}

		return () => {
			if (pathLayerRef.current && map.hasLayer(pathLayerRef.current)) {
				map.removeLayer(pathLayerRef.current)
			}
			markersRef.current.forEach((m) => {
				if (map.hasLayer(m)) map.removeLayer(m)
			})
		}
	}, [pathData, map])

	if (noPath) {
		// Display "no path found" message via a custom control
		useEffect(() => {
			if (!map) return
			const NoPathControl = L.Control.extend({
				onAdd: function () {
					const div = L.DomUtil.create('div', 'no-path-message')
					div.innerHTML = '<strong>No path found</strong>'
					div.style.backgroundColor = 'white'
					div.style.padding = '10px'
					div.style.border = '2px solid red'
					div.style.borderRadius = '4px'
					div.style.fontWeight = 'bold'
					return div
				}
			})
			const ctrl = new NoPathControl({ position: 'topright' })
			ctrl.addTo(map)
			return () => {
				ctrl.remove()
			}
		}, [map])
	}

	return null
}

export default function Graph({
	edges,
	stroke = 'var(--color-sitePrimaryColor)',
	strokeWidth = 3,
	className,
	streamData = [],
}: GraphProps) {
	const center: [number, number] = [39.8283, -98.5795] // center of USA

	return (
		<MapContainer
			center={center}
			zoom={5}
			style={{ width: '100%', height: '100%' }}
			className={className}
      scrollWheelZoom={false}    
      doubleClickZoom={false}
      touchZoom={false} 
      
		>
			{/* No tile layer - blank canvas */}
			{edges && (
				<GeoJSONLayer edges={edges} stroke={stroke} strokeWidth={strokeWidth} />
			)}
      <MapBackground color="#ffffff" />
			{/* PathOverlay rendered after base layers so it appears on top */}
			<PathOverlay streamQueue={streamData} />
		</MapContainer>
	)
}

