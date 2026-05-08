/**
 * map_view.js — Leaflet battlefield map (F4.10 v2).
 * Always visible. Shows terrain, cover, deploy zones, objectives, units.
 */
function mapView() {
    return {
        map: null,
        tileLayer: null,
        gridLayer: null,
        objectivesLayer: null,
        deployZoneLayer: null,
        unitLayer: null,
        gridSize: { width: 0, height: 0 },
        cellSize: 22,

        terrainColors: {
            0: '#2d2d44',  // Open
            1: '#4a7a3a',  // Light Cover
            2: '#2a5a2a',  // Heavy Cover
            3: '#1a1a2e',  // Obstacle
            4: '#5a4a2a',  // Difficult
            5: '#1e3a5f',  // Deploy zone (P1 - blue-ish)
            6: '#5f1e1e',  // Deploy zone (P2 - red-ish)
        },

        terrainLabels: {
            0: 'Open',
            1: 'Light Cover',
            2: 'Heavy Cover',
            3: 'Obstacle',
            4: 'Difficult Terrain',
            5: 'Deployment Zone',
            6: 'Deployment Zone',
        },

        initMap(width, height, objectives, deployZones, units) {
            if (this.map) { this.map.remove(); this.map = null; }
            this.gridSize = { width, height };

            setTimeout(() => {
                const el = document.getElementById('battlefield-map');
                if (!el) return;

                const c = this.cellSize;
                const mapH = height * c;
                const mapW = width * c;

                this.map = L.map('battlefield-map', {
                    crs: L.CRS.Simple,
                    minZoom: -2,
                    maxZoom: 2,
                    zoomControl: true,
                    attributionControl: false,
                });

                this.map.setMaxBounds([[0, 0], [mapH, mapW]]);
                this.map.fitBounds([[0, 0], [mapH, mapW]]);

                fetch(`/api/map/tiles?width=${width}&height=${height}`)
                    .then(r => r.json())
                    .then(data => {
                        this._renderTiles(data, c);
                        // Use provided zones or fall back to API response
                        const zones = deployZones || data.deploy_zones;
                        if (zones) this.showDeployZones(zones);
                        if (objectives && objectives.length) this.showObjectives(objectives);
                        if (units && units.length) this.showUnits(units);
                        this._drawGrid(width, height, c);
                    })
                    .catch(err => console.error('Failed to load map tiles:', err));
            }, 100);
        },

        _renderTiles(data, c) {
            if (this.tileLayer) this.map.removeLayer(this.tileLayer);
            const tiles = data.tiles;
            const features = [];

            for (let y = 0; y < tiles.length; y++) {
                for (let x = 0; x < tiles[y].length; x++) {
                    const t = tiles[y][x];
                    const color = this.terrainColors[t] || '#333';
                    features.push({
                        type: 'Feature',
                        geometry: {
                            type: 'Polygon',
                            coordinates: [[
                                [x * c, y * c],
                                [(x + 1) * c, y * c],
                                [(x + 1) * c, (y + 1) * c],
                                [x * c, (y + 1) * c],
                            ]],
                        },
                        properties: { color, tileType: t },
                    });
                }
            }

            const self = this;
            this.tileLayer = L.geoJSON(
                { type: 'FeatureCollection', features },
                {
                    style: (f) => ({
                        fillColor: f.properties.color,
                        color: '#ffffff06',
                        weight: 0.3,
                        fillOpacity: 0.85,
                    }),
                    onEachFeature: function (f, layer) {
                        const label = self.terrainLabels[f.properties.tileType];
                        if (label && f.properties.tileType !== 0) {  // skip "Open" tooltips
                            layer.bindTooltip(label, {
                                sticky: true,
                                opacity: 0.8,
                                className: 'terrain-tooltip',
                            });
                        }
                    },
                }
            ).addTo(this.map);
        },

        _drawGrid(width, height, c) {
            if (this.gridLayer) this.map.removeLayer(this.gridLayer);
            const features = [];
            const step = 6;
            for (let x = 0; x <= width; x += step) {
                features.push({
                    type: 'Feature',
                    geometry: {
                        type: 'LineString',
                        coordinates: [[x * c, 0], [x * c, height * c]],
                    },
                });
            }
            for (let y = 0; y <= height; y += step) {
                features.push({
                    type: 'Feature',
                    geometry: {
                        type: 'LineString',
                        coordinates: [[0, y * c], [width * c, y * c]],
                    },
                });
            }
            this.gridLayer = L.geoJSON(
                { type: 'FeatureCollection', features },
                { style: { color: '#ffffff0a', weight: 0.5 }, interactive: false }
            ).addTo(this.map);
        },

        showObjectives(objectives) {
            if (this.objectivesLayer) this.map.removeLayer(this.objectivesLayer);
            if (!objectives || !objectives.length) return;
            const c = this.cellSize;
            const markers = objectives.map(obj =>
                L.circleMarker([obj.y * c + c / 2, obj.x * c + c / 2], {
                    radius: 10,
                    color: '#fbbf24',
                    fillColor: '#fbbf24',
                    fillOpacity: 0.55,
                    weight: 2.5,
                }).bindTooltip(`<b>${obj.label || 'Objective'}</b>`, { className: 'obj-tooltip' })
            );
            this.objectivesLayer = L.layerGroup(markers).addTo(this.map);
        },

        showDeployZones(zones) {
            if (this.deployZoneLayer) this.map.removeLayer(this.deployZoneLayer);
            if (!zones) return;
            const c = this.cellSize;
            const rects = [];
            for (const [pid, cells] of Object.entries(zones)) {
                const color = pid === 'p1' ? '#3b82f6' : '#ef4444';
                for (const [x, y] of cells) {
                    rects.push(L.rectangle(
                        [[y * c, x * c], [(y + 1) * c, (x + 1) * c]],
                        { color, fillColor: color, fillOpacity: 0.15, weight: 0.5, interactive: false }
                    ));
                }
            }
            if (rects.length) this.deployZoneLayer = L.layerGroup(rects).addTo(this.map);
        },

        showUnits(units) {
            if (this.unitLayer) this.map.removeLayer(this.unitLayer);
            if (!units || !units.length) return;
            const c = this.cellSize;
            const markers = units.map(u => {
                const color = u.color || (u.player === 1 ? '#3b82f6' : '#ef4444');
                const label = u.faction ? `${u.name} (${u.faction})` : u.name;
                return L.circleMarker([u.y * c + c / 2, u.x * c + c / 2], {
                    radius: 7,
                    color: '#fff',
                    fillColor: color,
                    fillOpacity: 0.85,
                    weight: 1.5,
                }).bindTooltip(label, { className: 'unit-tooltip' });
            });
            this.unitLayer = L.layerGroup(markers).addTo(this.map);
        },

        destroy() {
            if (this.map) { this.map.remove(); this.map = null; }
        },
    };
}
