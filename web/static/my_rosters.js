function myRosters() {
    return {
        rosters: [],
        tier: 'free',
        expanded: null,
        deleteTarget: null,

        async init() {
            await this.loadRosters();
            await this.loadTier();
        },

        async loadRosters() {
            try {
                const resp = await fetch('/api/rosters');
                if (resp.ok) {
                    const data = await resp.json();
                    this.rosters = data.rosters || [];
                    // Parse units JSON if string
                    this.rosters.forEach(r => {
                        if (typeof r.units === 'string') {
                            try { r.units = JSON.parse(r.units); } catch (e) { r.units = []; }
                        }
                    });
                }
            } catch (e) {
                console.error('Failed to load rosters:', e);
            }
        },

        async loadTier() {
            try {
                const resp = await fetch('/api/me');
                if (resp.ok) {
                    const user = await resp.json();
                    this.tier = user?.tier || 'free';
                }
            } catch (e) { /* ignore */ }
        },

        async duplicateRoster(id) {
            try {
                const resp = await fetch(`/api/rosters/${id}/duplicate`, { method: 'POST' });
                if (resp.ok) {
                    await this.loadRosters();
                } else {
                    alert('Failed to duplicate roster');
                }
            } catch (e) {
                alert('Network error');
            }
        },

        confirmDelete(roster) {
            this.deleteTarget = roster;
        },

        async deleteRoster() {
            if (!this.deleteTarget) return;
            try {
                const resp = await fetch(`/api/rosters/${this.deleteTarget.id}`, { method: 'DELETE' });
                if (resp.ok) {
                    this.deleteTarget = null;
                    await this.loadRosters();
                } else {
                    const err = await resp.json().catch(() => ({}));
                    alert(err.detail || 'Failed to delete roster');
                }
            } catch (e) {
                alert('Network error');
            }
        }
    };
}