// Scenario Setup — Alpine.js component
function scenarioSetup() {
    return {
        // State
        player1Roster: '',
        player2Roster: '',
        player2Faction: '',
        player2Generated: null,
        mission: 'only-war',
        mapSize: 'strike-force',
        firstTurn: 'roll-off',
        rosters: window._rosters || [],
        factions: [],
        generating: false,
        player1Units: [],
        player2Units: [],

        // Lifecycle
        init() {
            this.$watch('player1Roster', (newVal) => {
                if (newVal) this.loadRoster(1, newVal);
                else this.player1Units = [];
                this.updateMapUnits();
            });

            this.$watch('player2Roster', (newVal) => {
                if (newVal) {
                    this.player2Generated = null;
                    this.loadRoster(2, newVal);
                } else {
                    this.player2Units = [];
                }
                this.updateMapUnits();
            });

            // Watch for generated opponent
            this.$watch('player2Generated', (newVal) => {
                if (newVal && newVal.units) {
                    this.loadGeneratedUnits(newVal.units);
                }
            });
        },

        async loadGeneratedUnits(units) {
            const unitDetails = await Promise.all(
                units.map(u => this.loadUnitDetails(u.unit_name))
            );

            const mapUnits = [];
            for (let i = 0; i < units.length; i++) {
                const unit = units[i];
                const details = unitDetails[i];
                if (details) {
                    const pos = this.getDeployPosition(2, i, units.length);
                    mapUnits.push({
                        name: unit.unit_name,
                        x: pos.x,
                        y: pos.y,
                        faction: 'generated',
                        icon: details.icon_url,
                        color: details.color,
                    });
                }
            }
            this.player2Units = mapUnits;
            this.updateMapUnits();
        },

        // Computed
        get canStart() {
            return this.player1Roster && (this.player2Roster || this.player2Generated);
        },
        get player1Label() {
            const r = this.rosters.find(r => r.id == this.player1Roster);
            return r ? `${r.name} (${r.faction}, ${r.pts_limit}pts)` : 'Not selected';
        },
        get player2Label() {
            if (this.player2Generated) {
                return `${this.player2Generated.name} (${this.player2Generated.faction}, ${this.player2Generated.total_pts}pts) — AI generated`;
            }
            const r = this.rosters.find(r => r.id == this.player2Roster);
            return r ? `${r.name} (${r.faction}, ${r.pts_limit}pts)` : 'Not selected';
        },

        async generateOpponent() {
            this.generating = true;
            try {
                // Determine pts limit from player 1's roster
                const p1 = this.rosters.find(r => r.id == this.player1Roster);
                const pts = p1 ? p1.pts_limit : 2000;
                const faction = this.player2Faction || '';

                const resp = await fetch(
                    `/api/rosters/generate`,
                    {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({faction, pts_limit: pts}),
                    }
                );
                if (resp.ok) {
                    const data = await resp.json();
                    this.player2Generated = data.roster;
                } else {
                    alert('Failed to generate opponent roster');
                }
            } catch (e) {
                alert('Network error generating opponent');
            } finally {
                this.generating = false;
            }
        },

        clearOpponent() {
            this.player2Generated = null;
            this.player2Units = [];
            this.updateMapUnits();
        },

        async loadRoster(player, rosterId) {
            try {
                const resp = await fetch(`/api/rosters/${rosterId}`);
                if (resp.ok) {
                    const roster = await resp.json();
                    const units = roster.units || [];
                    const unitDetails = await Promise.all(
                        units.map(u => this.loadUnitDetails(u.unit_name))
                    );

                    const mapUnits = [];
                    for (let i = 0; i < units.length; i++) {
                        const unit = units[i];
                        const details = unitDetails[i];
                        if (details) {
                            // Place units in deploy zones
                            const pos = this.getDeployPosition(player, i, units.length);
                            mapUnits.push({
                                name: unit.unit_name,
                                x: pos.x,
                                y: pos.y,
                                faction: roster.faction,
                                icon: details.icon_url,
                                color: details.color,
                            });
                        }
                    }

                    if (player === 1) {
                        this.player1Units = mapUnits;
                    } else {
                        this.player2Units = mapUnits;
                    }
                    this.updateMapUnits();
                }
            } catch (e) {
                console.error('Failed to load roster:', e);
            }
        },

        async loadUnitDetails(unitName) {
            try {
                const resp = await fetch(`/api/units/${encodeURIComponent(unitName)}/detail`);
                if (resp.ok) {
                    return await resp.json();
                }
            } catch (e) {
                console.error('Failed to load unit details:', e);
            }
            return null;
        },

        getDeployPosition(player, index, totalUnits) {
            // Simple deploy positioning
            const isPlayer1 = player === 1;
            const deployZone = isPlayer1 ? { startX: 0, endX: 3 } : { startX: 13, endX: 15 };

            // Spread units across deploy zone
            const unitsPerRow = Math.ceil(totalUnits / 16); // 16 rows available
            const row = Math.floor(index / unitsPerRow);
            const colOffset = (index % unitsPerRow) * Math.floor((deployZone.endX - deployZone.startX + 1) / Math.max(unitsPerRow, 1));

            return {
                x: Math.min(deployZone.endX, deployZone.startX + colOffset),
                y: Math.min(15, row),
            };
        },

        updateMapUnits() {
            // Combine units from both players
            const allUnits = [...this.player1Units, ...this.player2Units];

            // Update canvas map data
            if (window.canvasMapInstance) {
                window.canvasMapInstance.mapData.units = allUnits;
                window.canvasMapInstance.render();
            }
        },

        async startSimulation() {
            if (!this.canStart) return;
            // TODO: F3.5 — call auto-play endpoint
            alert('AI simulation not yet implemented (Phase 3). Coming soon!');
        }
    };
}
