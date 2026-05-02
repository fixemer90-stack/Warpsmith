// Team Builder — Alpine.js component
function teamBuilder() {
    return {
        // State
        faction: '',
        detachment: '',
        name: 'My Army',
        ptsLimit: 2000,
        roster: [],
        categories: ['epic-hero', 'HQ', 'Battleline', 'Infantry', 'Vehicle', 'Monster', 'Dedicated Transport'],
        selectedCategory: 'Battleline',
        showModal: false,
        selectedUnit: null,
        squadSize: 1,
        validationErrors: [],
        _units: [],
        detachments: [],

        // Computed
        get unitsByCategory() {
            const grouped = {};
            this._units.forEach(unit => {
                const cat = unit.category || 'Other';
                if (!grouped[cat]) grouped[cat] = [];
                grouped[cat].push(unit);
            });
            // Sort: Character → Battleline → Transport → Vehicle → Monster → Infantry → Legends
            const order = ['Character', 'Battleline', 'Transport', 'Vehicle', 'Monster', 'Infantry', 'Legends'];
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

        // Methods
        updatePtsLimit() {
            this.ptsLimit = parseInt(this.gameSize, 10);
        },
        async loadUnits() {
            if (!this.faction) {
                this.units = [];
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
                    this.detachments = detData.detachments || [];
                }
            } catch (error) {
                console.error('Failed to load units/detachments:', error);
            }
        },
        
        openUnitModal(unit) {
            this.selectedUnit = unit;
            this.squadSize = unit.squad_size || 1; // Default to 1 if not specified
            this.showModal = true;
        },
        
        addUnit() {
            if (!this.selectedUnit) return;
            
            // Check if unit already in roster
            const existingIndex = this.roster.findIndex(u => u.name === this.selectedUnit.name);
            if (existingIndex >= 0) {
                // Increase squad size
                this.roster[existingIndex].squad_size += this.squadSize;
            } else {
                // Add new unit to roster
                this.roster.push({
                    name: this.selectedUnit.name,
                    pts: this.selectedUnit.points,
                    squad_size: this.squadSize
                });
            }
            
            // Reset form
            this.showModal = false;
            this.validationErrors = [];
        },
        
        removeUnit(idx) {
            this.roster.splice(idx, 1);
        },
        
        async saveRoster() {
            if (!this.isValid) {
                alert('Please fix validation errors before saving');
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
                        detachment: this.detachment,
                        units: this.roster.map(u => ({
                            unit_name: u.name,
                            squad_size: u.squad_size
                        }))
                    })
                });
                
                if (response.ok) {
                    alert('Roster saved successfully!');
                    // Reset form after successful save
                    this.name = 'My Army';
                    this.faction = '';
                    this.detachment = '';
                    this.roster = [];
                    this.validationErrors = [];
                } else {
                    const errorData = await response.json();
                    if (errorData.validation_errors) {
                        // Format validation errors for display
                        this.validationErrors = errorData.validation_errors.map(err => ({
                            code: err.error || 'validation_error',
                            message: err.message || 'Validation failed'
                        }));
                    } else {
                        alert('Failed to save roster: ' + (errorData.detail || response.statusText));
                    }
                }
            } catch (error) {
                console.error('Error saving roster:', error);
                alert('Failed to save roster due to network error');
            }
        }
    };
}