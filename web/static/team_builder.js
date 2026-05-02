// Team Builder — Alpine.js component
function teamBuilder() {
    return {
        faction: "",
        ptsLimit: 2000,
        detachment: "",
        roster: [],
        units: [],
        factions: [],
        detachments: [],

        async init() {
            const resp = await fetch("/api/factions");
            if (resp.ok) {
                this.factions = (await resp.json()).factions || [];
            }
        },

        async loadUnits() {
            if (!this.faction) {
                this.units = [];
                this.detachments = [];
                return;
            }
            this.units = [];
            this.detachment = "";
            const [unitsResp, detResp] = await Promise.all([
                fetch("/api/units?faction=" + encodeURIComponent(this.faction)),
                fetch("/api/detachments?faction=" + encodeURIComponent(this.faction)),
            ]);
            if (unitsResp.ok) {
                this.units = (await unitsResp.json()).units || [];
            }
            if (detResp.ok) {
                this.detachments = (await detResp.json()).detachments || [];
            }
        },

        get ptsUsed() {
            return this.roster.reduce((sum, u) => sum + u.points * u.count, 0);
        },

        addUnit(name, points) {
            const existing = this.roster.find(u => u.name === name);
            if (existing) {
                existing.count++;
            } else {
                this.roster.push({ name, points, count: 1 });
            }
        },

        removeUnit(idx) {
            if (this.roster[idx].count > 1) {
                this.roster[idx].count--;
            } else {
                this.roster.splice(idx, 1);
            }
        },

        async saveRoster() {
            const name = prompt("Roster name:", `My ${this.faction} Army`);
            if (!name) return;

            const resp = await fetch("/api/rosters", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name,
                    faction: this.faction,
                    pts_limit: this.ptsLimit,
                    detachment: this.detachment,
                    units: this.roster.map(u => ({ unit_name: u.name, squad_size: u.count })),
                }),
            });

            if (resp.ok) {
                alert("Roster saved!");
            } else {
                const err = await resp.json().catch(() => ({}));
                alert("Failed to save: " + (err.detail || resp.statusText));
            }
        }
    };
}
