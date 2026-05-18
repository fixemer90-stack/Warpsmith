// Team Builder — Alpine.js component

// Global helper: inline SVG icon
function getIconHtml(category, size = 16) {
    const svgMap = window._iconSvgMap || {};
    const svg = svgMap[category] || svgMap['infantry'] || '';
    if (!svg) return '';
    return svg.replace('<svg ', '<svg width="' + size + '" height="' + size + '" style="fill: currentColor" ');
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
            return this.roster.reduce((sum, u) => sum + u.pts, 0);
        },
        get unitCount() {
            return this.roster.length;
        },
        get warlordCandidates() {
            return this.roster
                .map((entry, idx) => ({ ...entry, idx }))
                .filter(entry => this.isWarlordEligibleEntry(entry));
        },
        get warlordRequired() {
            // Per 10e: every army must have a Warlord. 0 candidates = invalid, 1 = auto-select, 2+ = pick one.
            return this.warlordCandidates.length !== 1;
        },
        get hasValidWarlordSelection() {
            const count = this.warlordCandidates.length;
            if (count === 0) return false;  // No eligible unit = impossible to have a Warlord
            if (count === 1) return true;   // Exactly one candidate = auto-valid
            return this.warlordCandidates.filter(entry => entry.is_warlord).length === 1;
        },
        get warlordWarningMessage() {
            if (this.warlordCandidates.length === 0) {
                return 'This roster has no eligible Character. Add a Character unit to serve as Warlord.';
            }
            return 'Multiple Characters detected. Click one 👑 crown in the roster to choose the Warlord.';
        },
        get isValid() {
            return this.totalPts <= this.ptsLimit
                && this.totalPts > 0
                && this.faction
                && this.roster.length > 0
                && this.hasValidWarlordSelection;
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
            // Canonical PTS formula (must match backend calculate_squad_pts())
            // Backend:  (points / minSquad + loadoutPts) * squadSize + nobPts
            // See backend/state/roster.py:calculate_squad_pts()
            const minSquad = this.unitDetail.squad_size?.min || 1;
            const ptsPerModel = this.unitDetail.points / minSquad;
            const loadout = this.unitDetail.wargear_options
                ?.find(o => o.name === this.selectedLoadout);
            const loadoutPts = loadout?.points || 0;
            const nobOpt = this.unitDetail.nob_options
                ?.find(o => o.name === this.selectedNobOption);
            const nobPts = nobOpt?.points || 0;
            const squadPts = (ptsPerModel + loadoutPts) * this.squadSize;
            return squadPts + nobPts;
        },

        getQuickSizes() {
            if (!this.unitDetail?.squad_size) return [];
            const { min, max, step } = this.unitDetail.squad_size;
            const sizes = [];
            for (let s = min; s <= max; s += step) sizes.push(s);
            return sizes;
        },

        isWarlordEligibleEntry(entry) {
            const normalizedTags = (entry.tags || []).map(tag => String(tag).toLowerCase());
            const normalizedKeywords = (entry.keywords || []).map(keyword => String(keyword).toLowerCase());
            return !!(
                entry.can_be_warlord
                || entry.is_leader
                || entry.category === 'Character'
                || normalizedTags.includes('character')
                || normalizedKeywords.includes('character')
            );
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
                    this.squadSize = data.squad_size?.min || 1;
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
            const wasSingleWarlordCandidate = this.warlordCandidates.length === 1;
            this.roster.push({
                name: this.unitDetail.name,
                squad_size: this.squadSize,
                pts: this.totalCost,
                loadout: this.selectedLoadout,
                nob_option: this.selectedNobOption,
                weapons: this.currentWeapons.map(w => w.name),
                category: this.unitDetail.category,
                tags: this.unitDetail.icon_tags || [],
                keywords: this.unitDetail.keywords || [],
                is_leader: !!this.unitDetail.is_leader,
                can_be_warlord: !!(this.unitDetail.can_be_warlord || this.unitDetail.is_leader || this.unitDetail.category === 'Character' || (this.unitDetail.icon_tags || []).includes('character') || (this.unitDetail.keywords || []).map(keyword => String(keyword).toLowerCase()).includes('character')),
                is_warlord: false,
            });
            const newIndex = this.roster.length - 1;
            if (this.roster[newIndex].can_be_warlord && this.warlordCandidates.length === 1) {
                this.roster[newIndex].is_warlord = true;
            }
            if (wasSingleWarlordCandidate && this.warlordCandidates.length > 1) {
                this.roster.forEach(entry => {
                    entry.is_warlord = false;
                });
                this.validationErrors = [{
                    code: 'warlord_required',
                    message: 'Multiple Characters detected. Click the crown next to exactly one Character to mark the Warlord.'
                }];
            } else {
                this.validationErrors = [];
            }
            this.showUnitModal = false;
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
                    category: u.category || '',
                    tags: u.tags || [],
                    keywords: u.keywords || [],
                    is_leader: !!u.is_leader,
                    can_be_warlord: !!u.can_be_warlord,
                    is_warlord: !!u.is_warlord,
                }));
                await this.loadUnits();
                this.roster = this.roster.map(entry => {
                    const unit = this._units.find(u => u.name === entry.name) || {};
                    return {
                        ...entry,
                        category: entry.category || unit.category || '',
                        tags: entry.tags?.length ? entry.tags : (unit.icon || []),
                        keywords: entry.keywords?.length ? entry.keywords : (unit.keywords || []),
                        is_leader: !!(entry.is_leader || unit.is_leader),
                        can_be_warlord: !!(entry.can_be_warlord || unit.can_be_warlord || unit.is_leader || unit.category === 'Character' || (unit.icon || []).includes('character') || (unit.keywords || []).map(keyword => String(keyword).toLowerCase()).includes('character')),
                    };
                });
                if (this.warlordCandidates.length === 1) {
                    this.roster[this.warlordCandidates[0].idx].is_warlord = true;
                }
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
            if (this.warlordCandidates.length === 1) {
                this.roster[this.warlordCandidates[0].idx].is_warlord = true;
            }
        },

        setWarlord(idx) {
            this.roster.forEach((entry, entryIdx) => {
                entry.is_warlord = entryIdx === idx;
            });
            this.validationErrors = this.validationErrors.filter(err => err.code !== 'warlord_required');
        },

        async saveRoster() {
            if (!this.name || !this.faction || this.roster.length === 0) {
                this.validationErrors = [{
                    code: 'missing_field',
                    message: 'Name, faction, and at least one unit are required'
                }];
                return;
            }

            if (!this.hasValidWarlordSelection) {
                this.validationErrors = [{
                    code: 'warlord_required',
                    message: this.warlordWarningMessage
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

            const method = this.editRosterId ? 'PUT' : 'POST';
            const url = this.editRosterId
                ? `/api/rosters/${this.editRosterId}`
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
                            nob_option: u.nob_option || '',
                            weapons: u.weapons || [],
                            pts: u.pts,
                            is_warlord: !!u.is_warlord
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
