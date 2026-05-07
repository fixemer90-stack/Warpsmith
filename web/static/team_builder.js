// Team Builder — Alpine.js component

// Global helper: inline SVG icon
function getIconHtml(category, size = 16) {
    const svgMap = window._iconSvgMap || {};
    const svg = svgMap[category] || svgMap['infantry'] || '';
    if (!svg) return '';
    return svg.replace('<svg ', <svg width="\" height="\" style="fill: currentColor" );
}

function teamBuilder() {
    return {
        // State
        faction: '',
        detachment: '',
        name: 'My Army',
        gameSize: 2000,
        ptsLimit: 2000,
        roster: [],
        selectedCategory: '',
        squadSize: 1,
        validationErrors: [],
        _units: [],
        detachments: [],
        editRosterId: null,

        // Unit Modal State
        showUnitModal: false,
        unitDetail: null,
        unitLoading: false,
        selectedLoadout: '',
        selectedNobOption: '',
        currentUnitName: '',

        // Detachment State
        // (detachment is defined above in State section)

        // Computed
        get unitsByCategory() {
            const grouped = {};
            this._units.forEach(unit => {
                const cat = unit.category || 'Other';
                if (!grouped[cat]) grouped[cat] = [];
                grouped[cat].push(unit);
            });
            // Sort: Epic Hero → Character → Battleline → Transport → Vehicle → Monster → Infantry → Legends
            const order = ['Epic Hero', 'Character', 'Battleline', 'Transport', 'Vehicle', 'Monster', 'Infantry', 'Legends'];
            const sorted = {};
            order.forEach(c => { if (grouped[c]) sorted[c] = grouped[c]; });
            Object.keys(grouped).filter(c => !order.includes(c)).forEach(c => sorted[c] = grouped[c]);
            return sorted;
        },
        get filteredUnits() {
            const cat = this.selectedCategory;
            return (this.unitsByCategory[cat] || [])
                .filter(u => u.faction === this.faction || !this.faction);
        },
        get totalPts() {
            return this.roster.reduce((sum, u) => sum + u.pts * u.squad_size, 0);
        },
        get unitCount() {
            return this.roster.length;
        },
        get isValid() {
            return this.totalPts <= this.ptsLimit
                && this.totalPts > 0
                && this.faction
                && this.roster.length > 0;
        },

        // Unit Modal Computed
        get currentWeapons() {
            if (!this.unitDetail) return [];
            const loadout = this.unitDetail.wargear_options
                ?.find(o => o.name === this.selectedLoadout);
            const nobOpt = this.unitDetail.nob_options
                ?.find(o => o.name === this.selectedNobOption);

            let weaponNames = loadout?.weapons || [];
            if (nobOpt?.replaces && nobOpt?.weapons) {
                weaponNames = weaponNames.filter(w => w !== nobOpt.replaces);
                weaponNames.push(...nobOpt.weapons);
            }

            return this.unitDetail.weapons
                ?.filter(w => weaponNames.includes(w.name)) || [];
        },

        get totalCost() {
            if (!this.unitDetail) return 0;
            const minSquad = this.unitDetail.squad_size?.min || 1;
            const ptsPerModel = this.unitDetail.points / minSquad;
            const loadout = this.unitDetail.wargear_options
                ?.find(o => o.name === this.selectedLoadout);
            const loadoutPts = loadout?.points || 0;
            return ptsPerModel + loadoutPts;
        },

        getQuickSizes() {
            if (!this.unitDetail?.squad_size) return [];
            const { min, max, step } = this.unitDetail.squad_size;
            const sizes = [];
            for (let s = min; s <= max; s += step) sizes.push(s);
            return sizes;
        },

        // Methods
        updatePtsLimit() {
            this.ptsLimit = parseInt(this.gameSize, 10);
        },

        onFactionChange() {
            this.loadUnits();
            const event = new CustomEvent('faction-changed', {
                detail: { faction: this.faction }
            });
            document.dispatchEvent(event);
        },

        // Unit Modal Methods
        openUnitModal(unitName) {
            this.currentUnitName = unitName;
            this.showUnitModal = true;
            this.unitLoading = true;
            this.unitDetail = null;
            this.selectedLoadout = '';
            this.selectedNobOption = '';

            fetch(`/api/units/${encodeURIComponent(unitName)}/detail`)
                .then(r => r.json())
                .then(data => {
                    this.unitDetail = data;
                    this.squadSize = data.squad_size.min || 5;
                    this.selectedLoadout = data.wargear_options?.[0]?.name || '';
                    this.selectedNobOption = '';
                    this.unitLoading = false;
                })
                .catch(err => {
                    console.error('Failed to load unit detail:', err);
                    this.unitLoading = false;
                });
        },

        addUnitToRoster() {
            if (!this.unitDetail) return;
            this.roster.push({
                name: this.unitDetail.name,
                squad_size: this.squadSize,
                pts: this.totalCost,
                loadout: this.selectedLoadout,
                nob_option: this.selectedNobOption,
                weapons: this.currentWeapons.map(w => w.name),
                category: this.unitDetail.category,
            });
            this.showUnitModal = false;
            this.validationErrors = [];
        },

        init() {
            document.addEventListener('detachment-selected', (e) => {
                this.detachment = e.detail.detachment;
            });

            const params = new URLSearchParams(window.location.search);
            const editId = params.get('edit');
            if (editId) {
                this.loadRosterForEdit(editId);
            }
        },

        async loadRosterForEdit(rosterId) {
            try {
                const resp = await fetch(`/api/rosters/${rosterId}`);
                if (!resp.ok) {
                    alert('Failed to load roster for editing');
                    window.location.href = '/my-rosters';
                    return;
                }
                const roster = await resp.json();
                this.editRosterId = roster.id;
                this.name = roster.name;
                this.faction = roster.faction;
                this.ptsLimit = roster.pts_limit;
                this.gameSize = roster.pts_limit;
                this.detachment = roster.detachment || '';
                this.roster = (roster.units || []).map(u => ({
                    name: u.unit_name,
                    squad_size: u.squad_size,
                    pts: u.pts || 0,
                    loadout: u.loadout || '',
                    nob_option: u.nob_option || '',
                    weapons: u.weapons || [],
                }));
                await this.loadUnits();
            } catch (e) {
                console.error('Failed to load roster for edit:', e);
                alert('Failed to load roster for editing');
            }
        },

        async loadUnits() {
            if (!this.faction) {
                this._units = [];
                this.detachments = [];
                return;
            }
            try {
                const [unitsResp, detResp] = await Promise.all([
                    fetch(`/api/units?faction=${encodeURIComponent(this.faction)}`),
                    fetch(`/api/detachments?faction=${encodeURIComponent(this.faction)}`),
                ]);

                if (unitsResp.ok) {
                    const unitsData = await unitsResp.json();
                    this._units = unitsData.units || [];
                    const keys = Object.keys(this.unitsByCategory);
                    this.selectedCategory = keys.length > 0 ? keys[0] : '';
                }

                if (detResp.ok) {
                    const detData = await detResp.json();
                    this.detachments = Array.isArray(detData)
                        ? detData.map(d => d.name)
                        : (detData.detachments || []);
                }
            } catch (error) {
                console.error('Failed to load units/detachments:', error);
            }
        },

        removeUnit(idx) {
            this.roster.splice(idx, 1);
        },

        async saveRoster() {
            if (!this.name || !this.faction || this.roster.length === 0) {
                this.validationErrors = [{
                    code: 'missing_field',
                    message: 'Name, faction, and at least one unit are required'
                }];
                return;
            }

            if (this.totalPts > this.ptsLimit) {
                this.validationErrors = [{
                    code: 'points_exceeded',
                    message: Total points(\) exceed limit(\)
                }];
                return;
            }

            const method = this.editRosterId ? 'PUT' : 'POST';
            const url = this.editRosterId
                ? /api/rosters /\
                : '/api/rosters';

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.name,
                        faction: this.faction,
                        pts_limit: this.ptsLimit,
                        detachment: this.detachment || '',
                        units: this.roster.map(u => ({
                            unit_name: u.name,
                            squad_size: u.squad_size,
                            pts: u.pts,
                            loadout: u.loadout || '',
                            weapons: u.weapons || []
                        }))
                    })
                });

                if (response.ok) {
                    alert(this.editRosterId ? 'Roster updated!' : 'Roster saved!');
                    if (this.editRosterId) {
                        this.editRosterId = null;
                        window.location.href = '/my-rosters';
                    } else {
                        this.name = 'My Army';
                        this.faction = '';
                        this.detachment = '';
                        this.roster = [];
                    }
                    this.validationErrors = [];
                } else {
                    const errorData = await response.json();
                    const detail = errorData.detail || errorData;

                    if (detail.validation_errors) {
                        this.validationErrors = detail.validation_errors;
                    } else if (typeof detail === 'string') {
                        this.validationErrors = [{
                            code: 'error',
                            message: detail
                        }];
                    } else {
                        this.validationErrors = [{
                            code: 'error',
                            message: detail.message || 'Unknown error'
                        }];
                    }
                }
            } catch (error) {
                console.error('Error saving roster:', error);
                this.validationErrors = [{
                    code: 'network_error',
                    message: 'Failed to save roster due to network error'
                }];
            }
        }
    };
}
