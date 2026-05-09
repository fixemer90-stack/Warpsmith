// Scenario Setup — Alpine.js component with strategic SVG battlefield map
function scenarioSetup() {
    return {
        // State
        player1Roster: '',
        player2Roster: '',
        player2Faction: '',
        player2Generated: null,
        mission: 'only-war',
        gameFormat: '2000',
        firstTurn: 'roll-off',
        rosters: window._rosters || [],
        factions: [],
        generating: false,
        player1Units: [],
        player2Units: [],
        _mapDebounce: null,
        _initialized: false,

        // Computed
        get compatibleRosters() {
            const pts = parseInt(this.gameFormat) || 2000;
            return this.rosters.filter(r => (r.pts_limit || 2000) <= pts);
        },
        get mapLabel() {
            const pts = parseInt(this.gameFormat) || 2000;
            if (pts <= 500) return '44×30″ — Combat Patrol';
            if (pts <= 1000) return '44×44″ — Incursion';
            if (pts <= 2000) return '44×60″ — Strike Force';
            return '44×90″ — Onslaught';
        },

        // ── Lifecycle ──
        init() {
            // Init map once with debounce
            this._scheduleMapRefresh();

            this.$watch('player1Roster', (newVal) => {
                if (newVal) this.loadRoster(1, newVal);
                else { this.player1Units = []; this.updateMapUnits(); }
            });

            this.$watch('player2Roster', (newVal) => {
                if (newVal) {
                    this.player2Generated = null;
                    this.loadRoster(2, newVal);
                } else {
                    this.player2Units = [];
                    this.updateMapUnits();
                }
            });

            this.$watch('player2Generated', (newVal) => {
                if (newVal && newVal.units) this.loadGeneratedUnits(newVal.units);
            });

            this.$watch('gameFormat', () => this._scheduleMapRefresh());
            this.$watch('mission', () => this._scheduleMapRefresh());
        },

        // ── Map (debounced to avoid multiple simultaneous inits) ──
        _scheduleMapRefresh() {
            clearTimeout(this._mapDebounce);
            this._mapDebounce = setTimeout(() => this.refreshMap(), 50);
        },

        refreshMap() {
            const pts = parseInt(this.gameFormat) || 2000;
            const sizes = { 500: [44,30], 1000: [44,44], 2000: [44,60], 3000: [44,90] };
            const [w, h] = sizes[pts] || [44, 60];
            // Destroy previous map instance fully
            if (window.battlefieldMapInstance) {
                window.battlefieldMapInstance.destroy();
                window.battlefieldMapInstance = null;
            }

            window.battlefieldMapInstance = battlefieldMap();
            window.battlefieldMapInstance.initMap(w, h, this.mission, null, null);

            this.updateMapUnits();
        },

        _getMissionObjectives(mw, mh) {
            const cx = Math.floor(mw / 2);
            const cy = Math.floor(mh / 2);
            if (this.mission === 'only-war') {
                return [
                    { x: cx, y: cy, label: 'Center' },
                    { x: Math.floor(cx / 2), y: cy, label: 'Flank L' },
                    { x: cx + Math.floor(cx / 2), y: cy, label: 'Flank R' },
                ];
            }
            return [
                { x: cx, y: cy, label: 'Center' },
                { x: Math.floor(cx / 2), y: cy, label: 'Flank L' },
                { x: cx + Math.floor(cx / 2), y: cy, label: 'Flank R' },
                { x: cx, y: Math.floor(cy / 2), label: 'Home A' },
                { x: cx, y: cy + Math.floor(cy / 2), label: 'Home B' },
            ];
        },

        updateMapUnits() {
            const allUnits = [
                ...this.player1Units.map(u => ({ ...u, player: 1, color: '#3b82f6' })),
                ...this.player2Units.map(u => ({ ...u, player: 2, color: '#ef4444' })),
            ];
            if (window.battlefieldMapInstance) {
                window.battlefieldMapInstance.showUnits(allUnits);
            }
        },

        // ── Roster loading ──
        async loadRoster(player, rosterId) {
            try {
                const resp = await fetch(`/api/rosters/${rosterId}`);
                if (!resp.ok) {
                    // Try to find roster in preloaded list
                    const cached = this.rosters.find(r => r.id == rosterId);
                    if (cached && cached.units) {
                        this._loadRosterFromCache(player, cached);
                        return;
                    }
                    console.warn('Roster API failed:', resp.status);
                    return;
                }
                const roster = await resp.json();
                this._processRosterData(player, roster);
            } catch (e) {
                console.error('Failed to load roster:', e);
            }
        },

        _loadRosterFromCache(player, cached) {
            // cached.units is the raw DB format: [{unit_name, squad_size}, ...]
            const rawUnits = Array.isArray(cached.units) ? cached.units : [];
            this._processRosterData(player, { ...cached, units: rawUnits });
        },

        async _processRosterData(player, roster) {
            const rawUnits = Array.isArray(roster.units) ? roster.units : [];
            if (!rawUnits.length) return;

            const unitDetails = await Promise.all(
                rawUnits.map(u => this.loadUnitDetails(u.unit_name))
            );

            const mapUnits = [];
            for (let i = 0; i < rawUnits.length; i++) {
                const unit = rawUnits[i];
                const details = unitDetails[i];
                if (details) {
                    const pos = this.getDeployPosition(player, i, rawUnits.length);
                    mapUnits.push({
                        name: unit.unit_name,
                        x: pos.x, y: pos.y,
                        faction: roster.faction,
                        icon: details.icon_url,
                        color: details.color,
                    });
                }
            }
            if (player === 1) this.player1Units = mapUnits;
            else this.player2Units = mapUnits;
            this.updateMapUnits();
        },

        async loadGeneratedUnits(units) {
            const arr = Array.isArray(units) ? units : [];
            const unitDetails = await Promise.all(arr.map(u => this.loadUnitDetails(u.unit_name)));
            const mapUnits = [];
            for (let i = 0; i < arr.length; i++) {
                const unit = arr[i];
                const details = unitDetails[i];
                if (details) {
                    const pos = this.getDeployPosition(2, i, arr.length);
                    mapUnits.push({
                        name: unit.unit_name,
                        x: pos.x, y: pos.y,
                        faction: 'generated',
                        icon: details.icon_url,
                        color: details.color,
                    });
                }
            }
            this.player2Units = mapUnits;
            this.updateMapUnits();
        },

        async loadUnitDetails(unitName) {
            try {
                const resp = await fetch(`/api/units/${encodeURIComponent(unitName)}/detail`);
                if (resp.ok) return await resp.json();
            } catch (e) { /* ignore */ }
            return null;
        },

        // ── Deploy positioning ──
        getDeployPosition(player, index, totalUnits) {
            const pts = parseInt(this.gameFormat) || 2000;
            const sizes = { 500: [44,30], 1000: [44,44], 2000: [44,60], 3000: [44,90] };
            const [mw, mh] = sizes[pts] || [44, 60];
            const zoneW = Math.max(1, Math.floor(mw / 5));
            const isPlayer1 = player === 1;
            const startX = isPlayer1 ? 0 : mw - zoneW;
            const endX = isPlayer1 ? zoneW - 1 : mw - 1;
            const unitsPerCol = Math.max(1, Math.ceil(totalUnits / Math.max(mh, 1)));
            const row = Math.floor(index / unitsPerCol);
            const col = index % unitsPerCol;
            const stepX = Math.max(1, Math.floor(zoneW / Math.max(unitsPerCol, 1)));
            return {
                x: Math.min(endX, startX + col * stepX),
                y: Math.min(mh - 1, row),
            };
        },

        // ── Computed ──
        get canStart() {
            return this.player1Roster && (this.player2Roster || this.player2Generated);
        },
        get player1Label() {
            const r = this.rosters.find(r => r.id == this.player1Roster);
            return r ? `${r.name} (${r.faction}, ${r.pts_limit}pts)` : 'Not selected';
        },
        get player2Label() {
            if (this.player2Generated)
                return `${this.player2Generated.name} (${this.player2Generated.faction}, ${this.player2Generated.total_pts}pts) — AI generated`;
            const r = this.rosters.find(r => r.id == this.player2Roster);
            return r ? `${r.name} (${r.faction}, ${r.pts_limit}pts)` : 'Not selected';
        },

        // ── Opponent generation ──
        async generateOpponent() {
            this.generating = true;
            try {
                const p1 = this.rosters.find(r => r.id == this.player1Roster);
                const pts = p1 ? p1.pts_limit : 2000;
                const faction = this.player2Faction || '';
                const resp = await fetch('/api/rosters/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ faction, pts_limit: pts }),
                });
                if (resp.ok) {
                    const data = await resp.json();
                    this.player2Generated = data.roster;
                } else {
                    alert('Failed to generate opponent roster');
                }
            } catch (e) {
                alert('Network error generating opponent');
            } finally { this.generating = false; }
        },

        clearOpponent() {
            this.player2Generated = null;
            this.player2Units = [];
            this.updateMapUnits();
        },

        // ── Simulation start ──
        async startSimulation() {
            if (!this.canStart) return;
            const rosterAId = this.player1Roster;
            let rosterBId = this.player2Roster;
            if (this.player2Generated) {
                try {
                    const saveResp = await fetch('/api/rosters', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            name: this.player2Generated.name,
                            faction: this.player2Generated.faction || '',
                            pts_limit: this.player2Generated.total_pts || 2000,
                            units: (this.player2Generated.units || []).map(u => ({
                                unit_name: u.unit_name,
                                squad_size: u.squad_size,
                                is_warlord: !!u.is_warlord,
                            })),
                            is_public: false,
                        }),
                    });
                    if (!saveResp.ok) { alert('Failed to save generated roster'); return; }
                    const saved = await saveResp.json();
                    rosterBId = saved.id;
                } catch (e) { alert('Network error saving generated roster'); return; }
            }
            if (!rosterBId) { alert('Please select or generate an opponent roster'); return; }
            try {
                const params = new URLSearchParams({
                    roster_a_id: rosterAId, roster_b_id: rosterBId,
                    mission: this.mission, max_rounds: '5',
                    seed: String(Math.floor(Math.random() * 100000)),
                });
                const resp = await fetch(`/api/auto-play?${params}`, { method: 'POST' });
                if (resp.ok) {
                    const data = await resp.json();
                    const gameId = data.game_id || data.result?.game_id;
                    if (gameId)
                        window.location.href = `/result/${gameId}`;
                    else alert('Simulation completed, but no game_id returned');
                } else {
                    const err = await resp.json().catch(() => ({}));
                    alert(`Simulation failed: ${err.detail || resp.statusText}`);
                }
            } catch (e) { alert(`Network error: ${e.message}`); }
        },

        updateFormat() { this._scheduleMapRefresh(); },
    };
}
