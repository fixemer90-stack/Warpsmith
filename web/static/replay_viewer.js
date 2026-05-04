// web/static/replay_viewer.js
// Alpine.js component for replay round viewer (F3.7)

function replayViewer() {
    return {
        // State
        gameId: '',
        replay: null,
        loading: true,
        error: null,

        // Navigation
        currentRoundIndex: 0,
        eventIndex: 0,

        // Canvas
        canvas: null,
        ctx: null,
        CELL_SIZE: 32,
        GRID_COLS: 19,
        GRID_ROWS: 14,

        // Derived
        get currentRoundEvents() {
            if (!this.replay || !this.replay.rounds || this.replay.rounds.length === 0) return [];
            const round = this.replay.rounds[this.currentRoundIndex];
            if (!round) return [];
            return round.events || [];
        },

        get currentEvent() {
            const events = this.currentRoundEvents;
            if (events.length === 0) return null;
            if (this.eventIndex >= events.length) this.eventIndex = events.length - 1;
            if (this.eventIndex < 0) this.eventIndex = 0;
            return events[this.eventIndex] || null;
        },

        get vpA() {
            if (!this.replay) return 0;
            const state = this._getCurrentState();
            if (!state || !state.victory_points) return 0;
            const keys = Object.keys(state.victory_points);
            return state.victory_points[keys[0]] || 0;
        },

        get vpB() {
            if (!this.replay) return 0;
            const state = this._getCurrentState();
            if (!state || !state.victory_points) return 0;
            const keys = Object.keys(state.victory_points);
            return state.victory_points[keys[1]] || 0;
        },

        // ── Lifecycle ──

        async loadReplay(gameId) {
            this.gameId = gameId || this.gameId;
            this.loading = true;
            this.error = null;

            try {
                const resp = await fetch(`/api/replays/${this.gameId}`);
                if (!resp.ok) {
                    if (resp.status === 404) {
                        throw new Error(`Replay "${this.gameId}" not found`);
                    }
                    throw new Error(`Server error: ${resp.status}`);
                }
                this.replay = await resp.json();

                // Initialize navigation
                this.currentRoundIndex = 0;
                this.eventIndex = 0;
                this.loading = false;

                // Canvas rendering (after DOM update)
                this.$nextTick(() => {
                    this.initCanvas();
                    this.renderCanvas();
                });
            } catch (e) {
                this.error = e.message;
                this.loading = false;
            }
        },

        initCanvas() {
            this.canvas = document.getElementById('replay-canvas');
            if (!this.canvas) return;
            this.ctx = this.canvas.getContext('2d');
        },

        // ── Navigation ──

        nextRound() {
            if (!this.replay || !this.replay.rounds) return;
            if (this.currentRoundIndex < this.replay.rounds.length - 1) {
                this.currentRoundIndex++;
                this.eventIndex = 0;
                this.renderCanvas();
            }
        },

        prevRound() {
            if (this.currentRoundIndex > 0) {
                this.currentRoundIndex--;
                this.eventIndex = 0;
                this.renderCanvas();
            }
        },

        nextEvent() {
            const events = this.currentRoundEvents;
            if (this.eventIndex < events.length - 1) {
                this.eventIndex++;
                this.renderCanvas();
            }
        },

        prevEvent() {
            if (this.eventIndex > 0) {
                this.eventIndex--;
                this.renderCanvas();
            }
        },

        // ── Canvas Rendering ──

        renderCanvas() {
            if (!this.ctx) this.initCanvas();
            if (!this.ctx) return;

            const ctx = this.ctx;
            const w = ctx.canvas.width;
            const h = ctx.canvas.height;

            // Clear and draw dark grid background
            ctx.fillStyle = '#111827';
            ctx.fillRect(0, 0, w, h);

            this._drawGrid(ctx, w, h);

            // Determine which state snapshot to use
            const state = this._getCurrentState();
            if (!state || !state.units) return;

            // Track active actor for highlighting
            const activeId = this.currentEvent ? this.currentEvent.actor_id : null;

            // Draw units by player
            const playerIds = Object.keys(state.units);
            const colors = this._getPlayerColors(playerIds.length);

            playerIds.forEach((pid, pidx) => {
                const units = state.units[pid] || [];
                const baseColor = colors[pidx] || '#6b7280';

                units.forEach((unit) => {
                    if (!unit.is_alive) return;
                    const pos = unit.position || { x: 0, y: 0 };
                    const cx = pos.x * this.CELL_SIZE + this.CELL_SIZE / 2 + 20;
                    const cy = pos.y * this.CELL_SIZE + this.CELL_SIZE / 2 + 20;

                    // Skip if out of bounds
                    if (cx < -20 || cx > w + 20 || cy < -20 || cy > h + 20) return;

                    const isActive = activeId && unit.id === activeId;
                    const radius = isActive ? 14 : 10;

                    // Draw glow for active unit
                    if (isActive) {
                        ctx.beginPath();
                        ctx.arc(cx, cy, radius + 6, 0, Math.PI * 2);
                        ctx.fillStyle = 'rgba(250, 204, 21, 0.3)';
                        ctx.fill();
                    }

                    // Draw body circle
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
                    ctx.fillStyle = isActive ? '#facc15' : baseColor;
                    ctx.fill();

                    // Draw border
                    ctx.strokeStyle = isActive ? '#fef08a' : (unit.is_battle_shocked ? '#ef4444' : '#374151');
                    ctx.lineWidth = isActive ? 3 : 1.5;
                    ctx.stroke();

                    // Engagement indicator
                    if (unit.is_engaged) {
                        ctx.beginPath();
                        ctx.arc(cx, cy, radius + 3, 0, Math.PI * 2);
                        ctx.strokeStyle = '#f97316';
                        ctx.lineWidth = 1.5;
                        ctx.setLineDash([3, 3]);
                        ctx.stroke();
                        ctx.setLineDash([]);
                    }

                    // Unit name label below
                    const name = unit.name || '';
                    const displayName = name.length > 12 ? name.substring(0, 10) + '..' : name;
                    ctx.fillStyle = '#d1d5db';
                    ctx.font = '8px monospace';
                    ctx.textAlign = 'center';
                    ctx.fillText(displayName, cx, cy + radius + 10);

                    // Models remaining badge
                    if (unit.models_remaining !== undefined) {
                        const hp = `${unit.models_remaining}/${unit.models_total}`;
                        ctx.fillStyle = '#9ca3af';
                        ctx.font = '7px monospace';
                        ctx.fillText(hp, cx, cy - radius - 4);
                    }
                });
            });

            // Draw event marker for active event (arrow from actor to target)
            this._drawEventMarker(ctx, state);
        },

        _drawGrid(ctx, w, h) {
            ctx.strokeStyle = '#1f2937';
            ctx.lineWidth = 0.5;

            for (let x = 0; x <= this.GRID_COLS; x++) {
                const px = x * this.CELL_SIZE + 20;
                ctx.beginPath();
                ctx.moveTo(px, 10);
                ctx.lineTo(px, h - 10);
                ctx.stroke();
            }

            for (let y = 0; y <= this.GRID_ROWS; y++) {
                const py = y * this.CELL_SIZE + 20;
                ctx.beginPath();
                ctx.moveTo(10, py);
                ctx.lineTo(w - 10, py);
                ctx.stroke();
            }

            // Deploy zone highlights
            ctx.fillStyle = 'rgba(59, 130, 246, 0.05)';
            ctx.fillRect(10, 10, 5 * this.CELL_SIZE, h - 20);
            ctx.fillStyle = 'rgba(239, 68, 68, 0.05)';
            ctx.fillRect(w - 5 * this.CELL_SIZE - 10, 10, 5 * this.CELL_SIZE, h - 20);
        },

        _getCurrentState() {
            if (!this.replay || !this.replay.rounds) return null;
            const round = this.replay.rounds[this.currentRoundIndex];
            if (!round) return null;

            // Use start_state if no events, otherwise use end_state
            const events = round.events || [];
            if (events.length === 0 || this.eventIndex < 0) {
                return round.start_state || null;
            }

            // For the last event, use end_state
            // For earlier events, use start_state (we don't have per-event snapshots)
            if (this.eventIndex >= events.length - 1) {
                return round.end_state || round.start_state || null;
            }
            return round.start_state || null;
        },

        _getPlayerColors(count) {
            const palette = ['#3b82f6', '#ef4444', '#22c55e', '#a855f7'];
            return palette.slice(0, count);
        },

        _drawEventMarker(ctx, state) {
            const evt = this.currentEvent;
            if (!evt) return;

            // Find actor and target positions
            let actorPos = null;
            let targetPos = null;

            if (state && state.units) {
                for (const pid of Object.keys(state.units)) {
                    for (const unit of state.units[pid]) {
                        if (unit.id === evt.actor_id && unit.is_alive) {
                            actorPos = unit.position;
                        }
                        if (unit.id === evt.target_id && unit.is_alive) {
                            targetPos = unit.position;
                        }
                    }
                }
            }

            // Fall back to event position data
            if (!actorPos && evt.position_before) {
                actorPos = evt.position_before;
            }
            if (!actorPos && evt.position_after) {
                actorPos = evt.position_after;
            }

            if (!actorPos || !targetPos) return;

            const ax = actorPos.x * this.CELL_SIZE + this.CELL_SIZE / 2 + 20;
            const ay = actorPos.y * this.CELL_SIZE + this.CELL_SIZE / 2 + 20;
            const tx = targetPos.x * this.CELL_SIZE + this.CELL_SIZE / 2 + 20;
            const ty = targetPos.y * this.CELL_SIZE + this.CELL_SIZE / 2 + 20;

            // Arrow from actor to target
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(tx, ty);
            ctx.strokeStyle = '#facc15';
            ctx.lineWidth = 2;
            ctx.setLineDash([4, 4]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Arrowhead
            const angle = Math.atan2(ty - ay, tx - ax);
            const headLen = 8;
            ctx.beginPath();
            ctx.moveTo(tx, ty);
            ctx.lineTo(tx - headLen * Math.cos(angle - Math.PI / 6), ty - headLen * Math.sin(angle - Math.PI / 6));
            ctx.lineTo(tx - headLen * Math.cos(angle + Math.PI / 6), ty - headLen * Math.sin(angle + Math.PI / 6));
            ctx.closePath();
            ctx.fillStyle = '#facc15';
            ctx.fill();
        },

        // ── UI Helpers ──

        eventTypeClass(type) {
            const map = {
                'shoot': 'bg-blue-800 text-blue-200',
                'charge': 'bg-orange-800 text-orange-200',
                'move': 'bg-green-800 text-green-200',
                'kill': 'bg-red-800 text-red-200',
                'damage': 'bg-red-900 text-red-300',
                'cp_spend': 'bg-purple-800 text-purple-200',
                'battle_shock': 'bg-yellow-800 text-yellow-200',
                'advance': 'bg-teal-800 text-teal-200',
                'fall_back': 'bg-pink-800 text-pink-200',
            };
            return map[type] || 'bg-gray-700 text-gray-200';
        },
    };
}
