// Team Builder — Alpine.js component
function teamBuilder() {
    return {
        // ── State ──
        faction: '',
        detachment: '',
        name: 'My Army',
        gameSize: 2000,
        ptsLimit: 2000,
        roster: [],
        selectedCategory: '',
        unitsByCategory: {},
        detachments: [],
        validationErrors: [],

        // ── Computed ──
        get filteredUnits() {
            const cat = this.selectedCategory;
            if (!cat || !this.unitsByCategory[cat]) return [];
            return this.unitsByCategory[cat];
        },
        get totalPts() {
            return this.roster.reduce((sum, u) => sum + u.points * u.count, 0);
        },
        get unitCount() {
            return this.roster.reduce((sum, u) => sum + u.count, 0);
        },
        get isValid() {
            return this.totalPts <= this.ptsLimit
                && this.totalPts > 0
                && this.faction
                && this.roster.length > 0;
        },

        // ── Methods ──
        updatePtsLimit() {
            this.ptsLimit = parseInt(this.gameSize, 10);
        },

        async loadUnits() {
            if (!this.faction) {
                this.unitsByCategory = {};
                this.detachments = [];
                this.selectedCategory = '';
                return;
            }
            try {
                const [unitsResp, detResp] = await Promise.all([
                    fetch(`/api/units?faction=${encodeURIComponent(this.faction)}`),
                    fetch(`/api/detachments?faction=${encodeURIComponent(this.faction)}`),
                ]);

                if (unitsResp.ok) {
                    const data = await unitsResp.json();
                    const grouped = {};
                    (data.units || []).forEach(unit => {
                        const cat = unit.category || 'Other';
                        if (!grouped[cat]) grouped[cat] = [];
                        grouped[cat].push(unit);
                    });
                    this.unitsByCategory = grouped;
                    const keys = Object.keys(grouped);
                    this.selectedCategory = keys.length > 0 ? keys[0] : '';
                }

                if (detResp.ok) {
                    const detData = await detResp.json();
                    this.detachments = detData.detachments || [];
                }
            } catch (error) {
                console.error('Failed to load units/detachments:', error);
            }
        },

        addUnit(unit) {
            const existing = this.roster.find(u => u.name === unit.name);
            if (existing) {
                existing.count++;
            } else {
                this.roster.push({
                    name: unit.name,
                    points: unit.points,
                    count: 1
                });
            }
            this.validationErrors = [];
        },

        removeUnit(idx) {
            if (this.roster[idx].count > 1) {
                this.roster[idx].count--;
            } else {
                this.roster.splice(idx, 1);
            }
        },

        async saveRoster() {
            if (!this.isValid) return;

            try {
                const resp = await fetch('/api/rosters', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.name || 'My Army',
                        faction: this.faction,
                        pts_limit: this.ptsLimit,
                        detachment: this.detachment || null,
                        units: this.roster.map(u => ({
                            unit_name: u.name,
                            squad_size: u.count
                        }))
                    })
                });

                if (resp.ok) {
                    alert('✅ Roster saved!');
                    this.roster = [];
                    this.validationErrors = [];
                } else {
                    const err = await resp.json();
                    if (err.validation_errors) {
                        this.validationErrors = err.validation_errors.map(e => ({
                            code: e.error || 'error',
                            message: e.message || 'Validation failed'
                        }));
                    } else {
                        alert('❌ Failed to save: ' + (err.detail || resp.statusText));
                    }
                }
            } catch (error) {
                console.error('Save error:', error);
                alert('❌ Network error saving roster');
            }
        }
    };
}
