"use client"

import React, { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'

type PathNode = {
	x: number
	y: number
	type: string
}

type PathLayerProps = {
	pathData: PathNode[] | null
	edgeColor?: string
	edgeWidth?: number
	nodeColor?: string
	nodeRadius?: number
	showLabels?: boolean
	animationSpeed?: number // milliseconds per segment
}

export default function PathLayer({
	pathData,
	edgeColor = '#0066ff',
	edgeWidth = 3,
	nodeColor = '#ff0000',
	nodeRadius = 8,
	showLabels = true,
	animationSpeed = 10,
}: PathLayerProps) {
	const map = useMap()
	const layersRef = useRef<L.Layer[]>([])
	const timeoutsRef = useRef<NodeJS.Timeout[]>([])

	useEffect(() => {
		if (!map) return

		// Clear existing layers and timeouts
		layersRef.current.forEach((layer) => {
			if (map.hasLayer(layer)) {
				map.removeLayer(layer)
			}
		})
		layersRef.current = []
		
		timeoutsRef.current.forEach(clearTimeout)
		timeoutsRef.current = []

		// Add edges and endpoint markers if pathData exists
		if (pathData && pathData.length > 0) {
			// Draw start node immediately
			const startNode = pathData[0]
			const startMarker = L.circleMarker([startNode.x, startNode.y], {
				radius: nodeRadius,
				fillColor: '#00ff00', // Green for start
				color: '#00ff00',
				weight: 2,
				opacity: 1,
				fillOpacity: 0.8,
			}).addTo(map)

			if (showLabels) {
				startMarker.bindPopup(`Start: ${startNode.type}`)
			}
			layersRef.current.push(startMarker)

			// Animate edges between consecutive nodes
			for (let i = 0; i < pathData.length - 1; i++) {
				const timeout = setTimeout(() => {
					const start = pathData[i]
					const end = pathData[i + 1]
					
					const line = L.polyline(
						[[start.x, start.y], [end.x, end.y]],
						{
							color: edgeColor,
							weight: edgeWidth,
							opacity: 0.8,
							lineCap: 'round',
							lineJoin: 'round',
						}
					).addTo(map)
					
					layersRef.current.push(line)

					// Draw blue dot for regent_spot nodes
					if (end.type === 'regen_spot') {
						const regentMarker = L.circleMarker([end.x, end.y], {
							radius: 2.5,
							fillColor: '#0066ff',
							color: '#0066ff',
							weight: 1,
							opacity: 1,
							fillOpacity: 0.9,
						}).addTo(map)

						if (showLabels) {
							regentMarker.bindPopup(`Regent Spot: ${end.type}`)
						}
						layersRef.current.push(regentMarker)
					}

					// Add end marker on the last segment
					if (i === pathData.length - 2) {
						const endMarker = L.circleMarker([end.x, end.y], {
							radius: nodeRadius,
							fillColor: nodeColor, // Red for end
							color: nodeColor,
							weight: 2,
							opacity: 1,
							fillOpacity: 0.8,
						}).addTo(map)

						if (showLabels) {
							endMarker.bindPopup(`End: ${end.type}`)
						}
						layersRef.current.push(endMarker)
					}
				}, i * animationSpeed)
				
				timeoutsRef.current.push(timeout)
			}
		}

		return () => {
			layersRef.current.forEach((layer) => {
				if (map.hasLayer(layer)) {
					map.removeLayer(layer)
				}
			})
			layersRef.current = []
			
			timeoutsRef.current.forEach(clearTimeout)
			timeoutsRef.current = []
		}
	}, [pathData, map, edgeColor, edgeWidth, nodeColor, nodeRadius, showLabels, animationSpeed])

	return null
}
