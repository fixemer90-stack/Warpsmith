// web/static/synergy_hints.js
function synergyHints() {
    return {
        synergyChecks: [],
        debounceTimer: null,
        lastCheck: '',

        get errorCount() {
            return this.synergyChecks.filter(c => c.severity === 'error').length;
        },
        get warningCount() {
            return this.synergyChecks.filter(c => c.severity === 'warning').length;
        },
        get infoCount() {
            return this.synergyChecks.filter(c => c.severity === 'info').length;
        },

        checkSynergies() {
            // Debounce to avoid excessive API calls
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                const payload = {
                    faction: this.faction,
                    units: this.roster,
                };
                const payloadStr = JSON.stringify(payload);
                if (payloadStr === this.lastCheck) return; // No change
                this.lastCheck = payloadStr;

                if (this.roster.length === 0) {
                    this.synergyChecks = [];
                    return;
                }

                fetch('/api/rosters/synergies', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: payloadStr,
                })
                .then(r => r.json())
                .then(data => {
                    this.synergyChecks = data.checks || [];
                })
                .catch(err => {
                    console.error('Synergy check error:', err);
                    this.synergyChecks = [];
                });
            }, 500); // 500ms debounce
        },

        // Visual indicators for roster units
        getSynergyClass(unitName) {
            const checks = this.synergyChecks.filter(c =>
                c.source_unit === unitName || c.target_unit === unitName);
            if (checks.some(c => c.severity === 'error')) return 'border-l-4 border-red-500';
            if (checks.some(c => c.severity === 'warning')) return 'border-l-4 border-yellow-500';
            if (checks.some(c => c.severity === 'info')) return 'border-l-4 border-green-500';
            return '';
        },

        getSynergyDot(unitName) {
            const checks = this.synergyChecks.filter(c =>
                c.source_unit === unitName || c.target_unit === unitName);
            if (checks.some(c => c.severity === 'error')) return 'bg-red-500';
            if (checks.some(c => c.severity === 'warning')) return 'bg-yellow-500';
            if (checks.some(c => c.severity === 'info')) return 'bg-green-500';
            return 'bg-gray-600';
        },
    };
}