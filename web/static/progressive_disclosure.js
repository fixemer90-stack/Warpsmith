// web/static/progressive_disclosure.js
// F4.6 — Three display modes: Beginner, Intermediate, Expert
// Saves choice to localStorage, applies CSS class to <body>

function progressiveDisclosure() {
    return {
        mode: 'intermediate',

        loadMode() {
            const saved = localStorage.getItem('warpsmith_display_mode');
            if (saved && ['beginner', 'intermediate', 'expert'].includes(saved)) {
                this.mode = saved;
            }
            this.applyMode();
        },

        setMode(newMode) {
            this.mode = newMode;
            try {
                localStorage.setItem('warpsmith_display_mode', newMode);
            } catch (e) {
                // localStorage blocked — silently ignore
            }
            this.applyMode();
        },

        applyMode() {
            document.body.classList.remove('mode-beginner', 'mode-intermediate', 'mode-expert');
            document.body.classList.add('mode-' + this.mode);

            document.dispatchEvent(new CustomEvent('display-mode-changed', {
                detail: { mode: this.mode },
            }));
        },
    };
}
