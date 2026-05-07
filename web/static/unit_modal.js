/**
 * Unit Modal — Alpine.js компонент для отображения полного datasheet юнита.
 *
 * Использование: передать mixin в teamBuilder() или подключить отдельно:
 *   Object.assign(teamBuilder(), unitModalMixin)
 *
 * F4.2 — Squad Size, Loadout, Wargear Selection, Full Stats
 */

const unitModalMixin = {
    // ── State ──────────────────────────────────────────────────
    showUnitModal: false,
    unitDetail: null,
    unitLoading: false,
    squadSize: 5,
    selectedLoadout: '',
    selectedNobOption: '',
    currentUnitName: '',

    // ── Computed ────────────────────────────────────────────────
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

    // ── Methods ─────────────────────────────────────────────────
    openUnitModal(unitName) {
        this.currentUnitName = unitName;
        this.showUnitModal = true;
        this.unitLoading = true;
        this.unitDetail = null;
        this.selectedLoadout = '';
        this.selectedNobOption = '';

        fetch(`/api/units/${encodeURIComponent(unitName)}/detail`)
            .then(r => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            })
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
};
