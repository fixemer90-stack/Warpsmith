// Team Builder — Alpine.js component
function teamBuilder() {
    return {
        faction: "",
        ptsLimit: 2000,
        detachment: "",
        roster: [],

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
            const payload = {
                name: prompt("Roster name:", `My ${this.faction} Army`),
                faction: this.faction,
                pts_limit: this.ptsLimit,
                detachment: this.detachment,
                units: this.roster.map(u => ({ name: u.name, count: u.count }))
            };

            if (!payload.name) return;

            const resp = await fetch("/api/rosters", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (resp.ok) {
                alert("Roster saved!");
            } else {
                alert("Failed to save roster");
            }
        }
    };
}
