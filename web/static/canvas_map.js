// web/static/canvas_map.js
function canvasMap() {
    return {
        // Canvas state
        canvas: null,
        ctx: null,
        mapData: null,
        CELL_SIZE: 50,
        GRID_SIZE: 16,

        // Viewport
        offsetX: 0,
        offsetY: 0,
        zoom: 1,

        // Interaction
        isDragging: false,
        dragStartX: 0,
        dragStartY: 0,
        hoveredCell: null,
        selectedCell: null,
        tooltipX: 0,
        tooltipY: 0,
        selectedUnitForDrag: null,
        isDraggingUnit: false,

        // Tile type colors (mirrors Python enum)
        TILE_COLORS: {
            0: '#3a3a3a',    // OPEN
            1: '#2d5a27',    // LIGHT_COVER
            2: '#4a3728',    // HEAVY_COVER
            3: '#555555',    // OBSTACLE
            4: '#3a5c6e',    // DIFFICULT
            5: '#3a3a3a',    // DEPLOY_ZONE (base)
        },

        TILE_LABELS: {
            0: 'Open Ground', 1: 'Light Cover', 2: 'Heavy Cover',
            3: 'Obstacle', 4: 'Difficult Ground', 5: 'Deploy Zone',
        },

        TILE_SYMBOLS: {
            0: '', 1: '🌿', 2: '🏛', 3: '🧱', 4: '💧', 5: '',
        },

        async initMap() {
            this.canvas = document.getElementById('battle-map');
            if (!this.canvas) return;
            this.ctx = this.canvas.getContext('2d');
            this.CELL_SIZE = 800 / this.GRID_SIZE; // = 50

            // Make instance globally available for scenario setup
            window.canvasMapInstance = this;

            // Load map data
            try {
                const resp = await fetch('/api/map/tiles');
                this.mapData = await resp.json();
                this.render();
            } catch (e) {
                console.error('Failed to load map tiles:', e);
                // Generate default empty map
                this.generateDefaultMap();
                this.render();
            }
        },

        generateDefaultMap() {
            // Generate a balanced map with central obstacles
            const tiles = [];
            for (let y = 0; y < this.GRID_SIZE; y++) {
                const row = [];
                for (let x = 0; x < this.GRID_SIZE; x++) {
                    let type = 0; // OPEN
                    // Central obstacles
                    if ((x >= 6 && x <= 9) && (y >= 6 && y <= 9)) type = 3;
                    // Some cover on flanks
                    if ((x === 3 || x === 12) && y >= 4 && y <= 11) type = 1;
                    // Difficult terrain near obstacles
                    if (x >= 5 && x <= 10 && y >= 5 && y <= 10 && type === 0) {
                        if ((x + y) % 3 === 0) type = 4;
                    }
                    row.push(type);
                }
                tiles.push(row);
            }

            this.mapData = {
                width: this.GRID_SIZE,
                height: this.GRID_SIZE,
                tiles: tiles,
                deploy_zones: {
                    player1: this.getDeployZoneCoords(0, 3),   // left
                    player2: this.getDeployZoneCoords(13, 15), // right
                },
                units: [],
            };
        },

        getDeployZoneCoords(xMin, xMax) {
            const coords = [];
            for (let x = xMin; x <= xMax; x++)
                for (let y = 0; y < this.GRID_SIZE; y++)
                    coords.push([x, y]);
            return coords;
        },

        render() {
            if (!this.ctx || !this.mapData) return;
            const ctx = this.ctx;
            const size = this.CELL_SIZE;
            const tiles = this.mapData.tiles;

            // Clear
            ctx.fillStyle = '#1a1a1a';
            ctx.fillRect(0, 0, 800, 800);

            // Apply zoom & pan
            ctx.save();
            ctx.translate(this.offsetX, this.offsetY);
            ctx.scale(this.zoom, this.zoom);

            // Draw tiles
            for (let y = 0; y < this.GRID_SIZE; y++) {
                for (let x = 0; x < this.GRID_SIZE; x++) {
                    const type = tiles[y]?.[x] ?? 0;
                    const px = x * size;
                    const py = y * size;

                    // Fill
                    ctx.fillStyle = this.TILE_COLORS[type] || '#3a3a3a';
                    ctx.fillRect(px, py, size, size);

                    // Grid lines
                    ctx.strokeStyle = '#444';
                    ctx.lineWidth = 0.5;
                    ctx.strokeRect(px, py, size, size);

                    // Deploy zone overlay
                    if (this.isDeployZone(x, y, 'player1')) {
                        ctx.fillStyle = 'rgba(37, 99, 235, 0.2)'; // blue
                        ctx.fillRect(px, py, size, size);
                    }
                    if (this.isDeployZone(x, y, 'player2')) {
                        ctx.fillStyle = 'rgba(220, 38, 38, 0.2)'; // red
                        ctx.fillRect(px, py, size, size);
                    }

                    // Terrain symbol
                    const symbol = this.TILE_SYMBOLS[type];
                    if (symbol) {
                        ctx.fillStyle = '#fff';
                        ctx.font = '18px serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(symbol, px + size / 2, py + size / 2);
                    }
                }
            }

            // Draw deploy zone labels
            ctx.font = 'bold 11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillStyle = 'rgba(37, 99, 235, 0.7)';
            ctx.fillText('PLAYER 1 DEPLOY ZONE', 2 * size, 1.5 * size);
            ctx.fillStyle = 'rgba(220, 38, 38, 0.7)';
            ctx.fillText('PLAYER 2 DEPLOY ZONE', 14 * size, 1.5 * size);

            // Draw units
            if (this.mapData.units) {
                for (const unit of this.mapData.units) {
                    this.drawUnit(ctx, unit);
                }
            }

            // Highlight selected cell
            if (this.selectedCell) {
                ctx.strokeStyle = '#3b82f6';
                ctx.lineWidth = 3;
                ctx.strokeRect(
                    this.selectedCell.x * size,
                    this.selectedCell.y * size,
                    size, size
                );
            }

            // Hover highlight
            if (this.hoveredCell && !this.isDragging && !this.isDraggingUnit) {
                ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
                ctx.fillRect(
                    this.hoveredCell.x * size,
                    this.hoveredCell.y * size,
                    size, size
                );
            }

            ctx.restore();
        },

        drawUnit(ctx, unit) {
            const size = this.CELL_SIZE;
            const cx = unit.x * size + size / 2;
            const cy = unit.y * size + size / 2;
            const radius = size * 0.35;

            // Circle
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.fillStyle = unit.color || '#a855f7';
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Label
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 9px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(unit.name.substring(0, 6), cx, cy);
        },

        // Coordinate conversion
        screenToGrid(screenX, screenY) {
            const rect = this.canvas.getBoundingClientRect();
            const scaleX = 800 / rect.width;
            const scaleY = 800 / rect.height;
            const canvasX = (screenX - rect.left) * scaleX;
            const canvasY = (screenY - rect.top) * scaleY;

            // Apply inverse zoom/pan
            const gridX = Math.floor((canvasX - this.offsetX) / this.zoom / this.CELL_SIZE);
            const gridY = Math.floor((canvasY - this.offsetY) / this.zoom / this.CELL_SIZE);

            if (gridX < 0 || gridX >= this.GRID_SIZE ||
                gridY < 0 || gridY >= this.GRID_SIZE) return null;
            return { x: gridX, y: gridY };
        },

        // Event handlers
        handleMouseDown(event) {
            const cell = this.screenToGrid(event.clientX, event.clientY);
            if (!cell) return;

            // Check if clicking on a unit
            const unit = this.getUnitAt(cell.x, cell.y);
            if (unit) {
                this.selectedUnitForDrag = unit;
                this.isDraggingUnit = true;
            }

            this.isDragging = true;
            this.dragStartX = event.clientX;
            this.dragStartY = event.clientY;
        },

        handleMouseMove(event) {
            const cell = this.screenToGrid(event.clientX, event.clientY);
            if (cell) {
                this.hoveredCell = {
                    ...cell,
                    type: this.TILE_LABELS[this.mapData.tiles[cell.y]?.[cell.x] || 0],
                };
                this.tooltipX = event.clientX - this.canvas.getBoundingClientRect().left + 12;
                this.tooltipY = event.clientY - this.canvas.getBoundingClientRect().top + 12;
            } else {
                this.hoveredCell = null;
            }

            if (this.isDragging && !this.isDraggingUnit) {
                // Pan the map
                const dx = event.clientX - this.dragStartX;
                const dy = event.clientY - this.dragStartY;
                this.offsetX += dx;
                this.offsetY += dy;
                this.dragStartX = event.clientX;
                this.dragStartY = event.clientY;
                this.render();
            }
        },

        handleMouseUp(event) {
            if (this.selectedUnitForDrag) {
                const cell = this.screenToGrid(event.clientX, event.clientY);
                if (cell) {
                    this.moveUnit(this.selectedUnitForDrag.name, cell.x, cell.y);
                }
                this.selectedUnitForDrag = null;
                this.isDraggingUnit = false;
            }
            this.isDragging = false;
        },

        handleClick(event) {
            if (this.isDragging || this.isDraggingUnit) return;
            const cell = this.screenToGrid(event.clientX, event.clientY);
            if (cell) {
                this.selectedCell = {
                    ...cell,
                    type: this.TILE_LABELS[this.mapData.tiles[cell.y]?.[cell.x] || 0],
                    unit: this.getUnitAt(cell.x, cell.y),
                };
                this.render();
            }
        },

        handleScroll(event) {
            const delta = event.deltaY > 0 ? -0.1 : 0.1;
            const newZoom = Math.max(0.5, Math.min(2, this.zoom + delta));

            // Zoom toward cursor position
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = (event.clientX - rect.left) * (800 / rect.width);
            const mouseY = (event.clientY - rect.top) * (800 / rect.height);

            this.offsetX = mouseX - (mouseX - this.offsetX) * (newZoom / this.zoom);
            this.offsetY = mouseY - (mouseY - this.offsetY) * (newZoom / this.zoom);

            this.zoom = newZoom;
            this.render();
        },

        // Unit management
        getUnitAt(x, y) {
            return this.mapData?.units?.find(u => u.x === x && u.y === y) || null;
        },

        moveUnit(name, newX, newY) {
            const unit = this.mapData?.units?.find(u => u.name === name);
            if (unit && !this.getUnitAt(newX, newY)) { // Don't allow stacking units
                unit.x = newX;
                unit.y = newY;
                this.render();
            }
        },

        startUnitDrag(unit) {
            this.selectedUnitForDrag = unit;
            this.isDraggingUnit = true;
        },

        isDeployZone(x, y, player) {
            const zones = this.mapData?.deploy_zones?.[player] || [];
            return zones.some(([zx, zy]) => zx === x && zy === y);
        },

        // Controls
        zoomIn() {
            if (this.zoom < 2) {
                this.zoom = Math.min(2, this.zoom + 0.2);
                this.render();
            }
        },

        zoomOut() {
            if (this.zoom > 0.5) {
                this.zoom = Math.max(0.5, this.zoom - 0.2);
                this.render();
            }
        },

        resetView() {
            this.zoom = 1;
            this.offsetX = 0;
            this.offsetY = 0;
            this.selectedCell = null;
            this.hoveredCell = null;
            this.render();
        },
    };
}