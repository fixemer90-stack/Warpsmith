function factionBrowser() {
    return {
        selectedFaction: '',
        selectedCategory: '',
        ptsMin: null,
        ptsMax: null,
        searchQuery: '',
        selectedRole: '',
        sortBy: 'name',
        sortDir: 'asc',
        currentPage: 1,
        perPage: 50,
        items: [],
        total: 0,
        pages: 0,
        factions: [],
        categories: [],
        loading: false,
        error: false,
        showDetail: false,
        detailUnit: null,

        presets: {
            cheap: { label: 'Under 100pts', ptsMin: null, ptsMax: 100, selectedRole: '' },
            elite: { label: '100-250pts', ptsMin: 100, ptsMax: 250, selectedRole: '' },
            hq: { label: 'Characters', selectedRole: 'leader', ptsMin: null, ptsMax: null },
            battleline: { label: 'Battleline', selectedRole: 'battleline', ptsMin: null, ptsMax: null },
        },

        get activeFilterCount() {
            let count = 0;
            if (this.selectedFaction) count++;
            if (this.selectedCategory) count++;
            if (this.ptsMin || this.ptsMax) count++;
            if (this.searchQuery) count++;
            if (this.selectedRole) count++;
            return count;
        },

        init() {
            this.refresh();
        },

        async refresh() {
            this.loading = true;
            this.error = false;

            const params = new URLSearchParams();
            if (this.selectedFaction) params.set('faction', this.selectedFaction);
            if (this.selectedCategory) params.set('category', this.selectedCategory);
            if (this.ptsMin) params.set('pts_min', this.ptsMin);
            if (this.ptsMax) params.set('pts_max', this.ptsMax);
            if (this.searchQuery) params.set('search', this.searchQuery);
            if (this.selectedRole) params.set('role', this.selectedRole);
            params.set('sort_by', this.sortBy);
            params.set('sort_dir', this.sortDir);
            params.set('page', this.currentPage);
            params.set('per_page', this.perPage);

            try {
                const resp = await fetch(`/api/units/browse?${params}`);
                if (!resp.ok) throw new Error('Request failed');
                const data = await resp.json();
                this.items = data.items || [];
                this.total = data.total || 0;
                this.pages = data.pages || 0;
                if (data.factions) this.factions = data.factions;
                if (data.categories) this.categories = data.categories;
            } catch (e) {
                this.error = true;
                console.error('Browse error:', e);
            } finally {
                this.loading = false;
            }
        },

        applyPreset(preset) {
            if (preset.ptsMin !== undefined) this.ptsMin = preset.ptsMin;
            if (preset.ptsMax !== undefined) this.ptsMax = preset.ptsMax;
            if (preset.selectedRole !== undefined) this.selectedRole = preset.selectedRole;
            this.currentPage = 1;
            this.refresh();
        },

        clearFilters() {
            this.selectedFaction = '';
            this.selectedCategory = '';
            this.ptsMin = null;
            this.ptsMax = null;
            this.searchQuery = '';
            this.selectedRole = '';
            this.currentPage = 1;
            this.refresh();
        },

        setSort(field) {
            if (this.sortBy === field) {
                this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortBy = field;
                this.sortDir = 'asc';
            }
            this.currentPage = 1;
            this.refresh();
        },

        toggleSortDir() {
            this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
            this.refresh();
        },

        goPage(p) {
            if (p < 1 || p > this.pages) return;
            this.currentPage = p;
            this.refresh();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        openDetail(unit) {
            this.detailUnit = unit;
            this.showDetail = true;
        },
    };
}
