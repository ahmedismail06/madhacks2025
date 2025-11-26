"use client"

import React, { useEffect, useRef } from 'react'
import { MapContainer, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import PathLayer from './PathLayer'

type GraphProps = {
	edges: any // GeoJSON or array of line segments
	stroke?: string
	strokeWidth?: number
	showPoints?: boolean
	pointRadius?: number
	className?: string
	pathData?: Array<{x: number, y: number, type: string}> | null
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

		// Use setTimeout to ensure map is fully initialized
		const timeoutId = setTimeout(() => {
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
		}, 0)

		return () => {
			clearTimeout(timeoutId)
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

export default function Graph({
	edges,
	stroke = 'var(--color-sitePrimaryColor)',
	strokeWidth = 3,
	className,
	pathData = null,
}: GraphProps) {
	const center: [number, number] = [39.8283, -98.5795] // center of USA

	return (
		<MapContainer
			center={center}
			zoom={4}
			style={{ width: '100%', height: '100%', borderRadius: '6px', overflow: 'hidden' }}
			className={className}
			scrollWheelZoom={false}
			doubleClickZoom={false}
			dragging={true}
			touchZoom={false}
			boxZoom={false}
			keyboard={false}
		>
			{/* No tile layer - blank canvas */}
			<MapBackground color="#ffffff" />

			{edges && (
				<GeoJSONLayer edges={edges} stroke={stroke} strokeWidth={strokeWidth} />
			)}

			<PathLayer pathData={pathData} />
		</MapContainer>
	)
}