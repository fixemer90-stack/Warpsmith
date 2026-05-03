// web/static/detachment_picker.js
function detachmentPicker() {
    return {
        faction: '',
        detachments: [],
        selectedDetachment: null,
        loading: false,
        error: null,

        init() {
            // Listen for faction changes from parent
            document.addEventListener('faction-changed', (e) => {
                this.faction = e.detail.faction || '';
                this.loadDetachments();
            });

            // Listen for detachment selection confirmation
            document.addEventListener('detachment-confirmed', (e) => {
                this.selectedDetachment = null; // Close detail after confirmation
            });
        },

        loadDetachments() {
            if (!this.faction) {
                this.detachments = [];
                this.selectedDetachment = null;
                this.error = null;
                return;
            }

            this.loading = true;
            this.error = null;
            this.selectedDetachment = null;

            fetch(`/api/detachments?faction=${encodeURIComponent(this.faction)}`)
                .then(r => {
                    if (!r.ok) throw new Error('Request failed');
                    return r.json();
                })
                .then(data => {
                    this.detachments = data;
                    this.loading = false;
                })
                .catch(err => {
                    this.error = err.message || 'Failed to load detachments';
                    this.loading = false;
                    console.error('Detachment load error:', err);
                });
        },

        selectDetachment(name) {
            if (this.selectedDetachment?.name === name) {
                // Clicking the same detachment closes it
                this.selectedDetachment = null;
                return;
            }

            this.loading = true;
            fetch(`/api/detachments/${encodeURIComponent(name)}`)
                .then(r => {
                    if (!r.ok) throw new Error('Request failed');
                    return r.json();
                })
                .then(data => {
                    this.selectedDetachment = data;
                    this.loading = false;
                })
                .catch(err => {
                    this.error = err.message || 'Failed to load detachment details';
                    this.loading = false;
                    console.error('Detachment detail error:', err);
                });
        },

        confirmDetachment() {
            if (!this.selectedDetachment) return;

            // Emit event to parent team builder
            const event = new CustomEvent('detachment-selected', {
                detail: { detachment: this.selectedDetachment.name }
            });
            document.dispatchEvent(event);

            // Also emit confirmation event
            const confirmEvent = new CustomEvent('detachment-confirmed', {
                detail: { detachment: this.selectedDetachment.name }
            });
            document.dispatchEvent(confirmEvent);
        },
    };
}