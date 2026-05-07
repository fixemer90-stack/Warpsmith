// web/static/result_chart.js
// Alpine.js + Chart.js component for Battle Result screen (F3.8)

function resultScreen() {
    return {
        // State
        gameId: '',
        replay: null,
        loading: true,
        error: null,
        chart: null,

        // ── Lifecycle ──

        async loadResult(gameId) {
            this.gameId = gameId || this.gameId;
            this.loading = true;
            this.error = null;

            try {
                const resp = await fetch(`/api/results/${this.gameId}`);
                if (!resp.ok) {
                    if (resp.status === 404) {
                        throw new Error(`Result "${this.gameId}" not found`);
                    }
                    throw new Error(`Server error: ${resp.status}`);
                }
                this.replay = await resp.json();
                this.loading = false;

                // Init chart after DOM update
                this.$nextTick(() => {
                    this.initChart();
                });
            } catch (e) {
                this.error = e.message;
                this.loading = false;
            }
        },

        initChart() {
            const canvas = document.getElementById('vp-chart');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            if (!ctx) return;
            if (!this.replay || !this.replay.rounds) return;

            // Build VP timeline data from round snapshots
            const labels = [];
            const vp1Data = [];
            const vp2Data = [];

            const playerKeys = this._getPlayerKeys();

            this.replay.rounds.forEach((round, idx) => {
                const roundNum = round.round || idx + 1;
                labels.push(`R${roundNum}`);

                const endState = round.end_state || round.start_state || {};
                const vps = endState.victory_points || {};
                const keys = Object.keys(vps);
                vp1Data.push(keys.length > 0 ? (vps[keys[0]] || 0) : 0);
                vp2Data.push(keys.length > 1 ? (vps[keys[1]] || 0) : 0);
            });

            // If no rounds, show empty
            if (labels.length === 0) {
                labels.push('Start');
                vp1Data.push(0);
                vp2Data.push(0);
            }

            // Destroy previous chart instance
            if (this.chart) {
                this.chart.destroy();
            }

            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: this._getPlayerName(0) || 'Player 1',
                            data: vp1Data,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointBackgroundColor: '#3b82f6',
                            pointBorderColor: '#93c5fd',
                            pointRadius: 4,
                        },
                        {
                            label: this._getPlayerName(1) || 'Player 2',
                            data: vp2Data,
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointBackgroundColor: '#ef4444',
                            pointBorderColor: '#fca5a5',
                            pointRadius: 4,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#d1d5db',
                                font: { family: 'monospace', size: 12 },
                            },
                        },
                        tooltip: {
                            backgroundColor: '#1f2937',
                            titleColor: '#f3f4f6',
                            bodyColor: '#d1d5db',
                            borderColor: '#374151',
                            borderWidth: 1,
                        },
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(75, 85, 99, 0.3)' },
                            ticks: { color: '#9ca3af', font: { family: 'monospace' } },
                        },
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(75, 85, 99, 0.3)' },
                            ticks: {
                                color: '#9ca3af',
                                font: { family: 'monospace' },
                                stepSize: 5,
                            },
                        },
                    },
                },
            });
        },

        // ── Computed Properties ──

        get phaseTable() {
            if (!this.replay || !this.replay.rounds) return [];

            const rows = [];
            this.replay.rounds.forEach((round) => {
                const events = round.events || [];
                const phaseGroups = {};

                events.forEach((evt) => {
                    const key = `${round.round || '?'}-${evt.phase || 'general'}`;
                    if (!phaseGroups[key]) {
                        phaseGroups[key] = {
                            round: round.round || '?',
                            phase: evt.phase || 'unknown',
                            events: 0,
                            damage_p1: 0,
                            damage_p2: 0,
                            kills: 0,
                        };
                    }
                    const g = phaseGroups[key];
                    g.events++;

                    // Determine which player dealt damage
                    const pid = this._actorPlayerId(evt.actor_id);
                    if (evt.event_type === 'damage' || evt.event_type === 'shoot') {
                        const dmg = evt.result_value || 0;
                        if (pid === 0 || pid === '1' || pid === 'player1' || pid === 'roster_a') {
                            g.damage_p1 += dmg;
                        } else {
                            g.damage_p2 += dmg;
                        }
                    }
                    if (evt.event_type === 'kill') {
                        g.kills++;
                    }
                });

                Object.values(phaseGroups).forEach((g) => rows.push(g));
            });

            return rows;
        },

        get phaseTotals() {
            const rows = this.phaseTable;
            return {
                events: rows.reduce((s, r) => s + r.events, 0),
                damage_p1: rows.reduce((s, r) => s + r.damage_p1, 0),
                damage_p2: rows.reduce((s, r) => s + r.damage_p2, 0),
                kills: rows.reduce((s, r) => s + r.kills, 0),
            };
        },

        get destroyedUnits() {
            const result = { player1: [], player2: [] };
            if (!this.replay || !this.replay.rounds) return result;

            const killedIds = new Set();

            this.replay.rounds.forEach((round) => {
                (round.events || []).forEach((evt) => {
                    if (evt.event_type === 'kill') {
                        // Kill events have actor_name = dead unit ("X was destroyed")
                        const deadName = evt.actor_name;
                        const deadId = evt.actor_id;
                        if (!deadName) return;
                        // Try to determine which player owned the dead unit
                        const victimPid = this._victimPlayerId(deadId || deadName);
                        if (victimPid === 0 && !killedIds.has(deadId || deadName)) {
                            killedIds.add(deadId || deadName);
                            result.player2.push(deadName);
                        } else if (victimPid === 1 && !killedIds.has(deadId || deadName)) {
                            killedIds.add(deadId || deadName);
                            result.player1.push(deadName);
                        }
                    }
                });
            });

            return result;
        },

        // ── Helpers ──

        _getPlayerKeys() {
            if (!this.replay || !this.replay.rosters) return ['0', '1'];
            const keys = Object.keys(this.replay.rosters);
            return keys.length >= 2 ? keys : ['roster_a', 'roster_b'];
        },

        _getPlayerName(index) {
            if (!this.replay || !this.replay.rosters) return '';
            const keys = this._getPlayerKeys();
            const key = keys[index];
            const roster = this.replay.rosters[key];
            return roster ? (roster.faction || roster.name || key) : key;
        },

        _getPlayerIdent(index) {
            const keys = this._getPlayerKeys();
            return keys[index] || `player${index + 1}`;
        },

        _actorPlayerId(actorId) {
            // Try to determine which player an actor belongs to
            if (!this.replay || !this.replay.rounds) return 0;
            const keys = this._getPlayerKeys();
            for (let i = 0; i < keys.length; i++) {
                const roster = this.replay.rosters[keys[i]];
                if (roster && roster.units) {
                    for (const unit of roster.units) {
                        if (unit.unit_id === actorId || unit.name === actorId) {
                            return i;
                        }
                    }
                }
            }
            // Fallback: check first round end_state units
            const firstRound = this.replay.rounds[0];
            if (firstRound) {
                const state = firstRound.start_state || firstRound.end_state;
                if (state && state.units) {
                    const pids = Object.keys(state.units);
                    for (let i = 0; i < pids.length; i++) {
                        const units = state.units[pids[i]] || [];
                        for (const u of units) {
                            if (u.id === actorId) {
                                return i;
                            }
                        }
                    }
                }
            }
            return 0;
        },

        _victimPlayerId(unitId) {
            // Determine which player a dead unit belonged to (reverse of _actorPlayerId)
            return this._actorPlayerId(unitId);
        },

        get winnerName() {
            if (!this.replay || !this.replay.summary) return '';
            const winner = this.replay.summary.winner;
            if (winner === undefined || winner === null) return 'Draw';
            if (winner === 1 || winner === '1' || winner === 'player1' || winner === 'roster_a') {
                return this._getPlayerName(0) || 'Player 1';
            }
            if (winner === 2 || winner === '2' || winner === 'player2' || winner === 'roster_b') {
                return this._getPlayerName(1) || 'Player 2';
            }
            return String(winner);
        },

        get winnerReason() {
            if (!this.replay || !this.replay.summary) return '';
            return this.replay.summary.reason || this.replay.summary.reason || '';
        },

        // ── Export ──

        exportJSON() {
            if (!this.replay) return;
            const blob = new Blob(
                [JSON.stringify(this.replay, null, 2)],
                { type: 'application/json' }
            );
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `result_${this.gameId}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        },
    };
}
