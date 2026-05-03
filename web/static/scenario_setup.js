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
        rosters: [],
        factions: [],
        generating: false,

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
                    `/api/rosters/generate?faction=${encodeURIComponent(faction)}&pts_limit=${pts}`
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
        },

        async startSimulation() {
            if (!this.canStart) return;
            // TODO: F3.5 — call auto-play endpoint
            alert('AI simulation not yet implemented (Phase 3). Coming soon!');
        }
    };
}
