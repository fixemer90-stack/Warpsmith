// Team Builder — Alpine.js component

// Global helper: inline SVG icon
function getIconHtml(category, size = 16) {
    const svgMap = window._iconSvgMap || {};
    const svg = svgMap[category] || svgMap['infantry'] || '';
    if (!svg) return '';
    return svg.replace('<svg ', `<svg width="${size}" height="${size}" style="fill: currentColor" `);
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
            // Any uncategorized go at the end but before Legends (if not already in order)
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
            // Resolve weapons from selected loadout + nob option
            const loadout = this.unitDetail.wargear_options
                ?.find(o => o.name === this.selectedLoadout);
            const nobOpt = this.unitDetail.nob_options
                ?.find(o => o.name === this.selectedNobOption);

            let weaponNames = loadout?.weapons || [];
            // If nob option has weapons, they replace the default
            if (nobOpt?.replaces && nobOpt?.weapons) {
                weaponNames = weaponNames.filter(w => w !== nobOpt.replaces);
                weaponNames.push(...nobOpt.weapons);
            }

            return this.unitDetail.weapons
                ?.filter(w => weaponNames.includes(w.name)) || [];
        },

        get totalCost() {
            if (!this.unitDetail) return 0;
            const basePts = this.unitDetail.points;
            // Wargear option cost (per model)
            const loadout = this.unitDetail.wargear_options
                ?.find(o => o.name === this.selectedLoadout);
            const loadoutPts = loadout?.points || 0;
            // Nob option cost (one-time)
            const nobOpt = this.unitDetail.nob_options
                ?.find(o => o.name === this.selectedNobOption);
            const nobPts = nobOpt?.points || 0;

            return (basePts + loadoutPts) * this.squadSize + nobPts;
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
            // Emit faction change event for detachment picker
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
            // Listen for detachment selection
            document.addEventListener('detachment-selected', (e) => {
                this.detachment = e.detail.detachment;
            });
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
            // Проверка обязательных полей
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
                    message: `Total points (${this.totalPts}) exceed limit (${this.ptsLimit})`
                }];
                return;
            }
            
            try {
                const response = await fetch('/api/rosters', {
                    method: 'POST',
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
                    alert('Roster saved successfully!');
                    // Сброс формы
                    this.name = 'My Army';
                    this.faction = '';
                    this.detachment = '';
                    this.roster = [];
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