// web/static/tooltips.js
// F4.7 — Tooltips on every stat (M/T/SV/W/LD/OC)

const STAT_TOOLTIPS = {
    M: {
        name: 'Movement',
        full_name: 'Movement Characteristic',
        description: 'How many inches this model can move in the Movement phase.',
        how_it_works: 'Roll 2D6 for charge range. Movement value determines how far you can Advance (M + D6).',
        examples: [
            { unit: 'Gretchin', value: '5"', note: 'Standard infantry speed' },
            { unit: 'Trukk', value: '12"', note: 'Fast vehicle' },
            { unit: 'Warboss', value: '5"', note: 'Standard leader speed' },
            { unit: 'Deff Dread', value: '6"', note: 'Slow walker' },
        ],
        related_stats: ['Advance', 'Charge'],
    },
    T: {
        name: 'Toughness',
        full_name: 'Toughness Characteristic',
        description: 'Compared to weapon Strength (S) to determine wound rolls. Higher T means harder to wound.',
        how_it_works: 'S >= 2xT = 2+, S > T = 3+, S == T = 4+, S < T = 5+, S <= T/2 = 6+',
        examples: [
            { unit: 'Gretchin', value: '2', note: 'Very fragile' },
            { unit: 'Boy', value: '5', note: 'Tough Ork infantry' },
            { unit: 'Warboss', value: '6', note: 'Leader toughness' },
            { unit: 'Trukk', value: '9', note: 'Vehicle' },
        ],
        related_stats: ['Strength (S)'],
    },
    SV: {
        name: 'Save',
        full_name: 'Armour Save Characteristic',
        description: 'D6 roll needed to ignore a wound. Lower is better.',
        how_it_works: 'Roll D6 >= SV value after AP modifier. SV + AP = modified save. Natural 1 always fails.',
        examples: [
            { unit: 'Gretchin', value: '7+', note: 'No armour (always fails)' },
            { unit: 'Boy', value: '6+', note: 'Light armour' },
            { unit: 'Warboss', value: '4+', note: 'Power armour' },
            { unit: 'Meganob', value: '2+', note: 'Heavy armour' },
        ],
        related_stats: ['AP (Armour Penetration)', 'Invulnerable Save'],
    },
    W: {
        name: 'Wounds',
        full_name: 'Wounds Characteristic',
        description: 'How much damage this model can take before it is destroyed.',
        how_it_works: 'Each unsaved wound reduces Wounds by damage value. At 0 wounds, model is removed.',
        examples: [
            { unit: 'Gretchin', value: '1', note: 'One hit kill' },
            { unit: 'Boy', value: '1', note: 'Standard infantry' },
            { unit: 'Warboss', value: '5', note: 'Tough character' },
            { unit: 'Trukk', value: '10', note: 'Vehicle durability' },
        ],
        related_stats: ['Damage (D)'],
    },
    LD: {
        name: 'Leadership',
        full_name: 'Leadership Characteristic',
        description: 'Morale/bravery test. Higher is better (easier to pass).',
        how_it_works: 'Roll 2D6, if result >= LD value, test is passed. Failed = Battle-shock.',
        examples: [
            { unit: 'Gretchin', value: '7+', note: 'Poor morale' },
            { unit: 'Boy', value: '7+', note: 'Average Ork morale' },
            { unit: 'Warboss', value: '8+', note: 'Strong leader morale' },
        ],
        related_stats: ['Battle-shock', 'Command phase'],
    },
    OC: {
        name: 'Objective Control',
        full_name: 'Objective Control Characteristic',
        description: 'Control score for objectives. Higher OC means more influence on objective markers.',
        how_it_works: 'Sum OC of all models within range of an objective. Higher total controls it.',
        examples: [
            { unit: 'Gretchin', value: '1', note: 'Minimal control' },
            { unit: 'Boy (Nob)', value: '2', note: 'Standard battleline' },
            { unit: 'Warboss', value: '3', note: 'Leader presence' },
        ],
        related_stats: ['Objective markers', 'Primary scoring'],
    },
};

function tooltipManager() {
    return {
        visible: false,
        x: 0,
        y: 0,
        tooltip: null,
        activeStat: null,
        glossaryOpen: false,
        glossaryStat: null,

        init() {
            this.registerStatElements();
        },

        registerStatElements() {
            document.querySelectorAll('[data-stat]').forEach(el => {
                el.classList.add('cursor-help');
                el.title = '';
            });
        },

        handleHover(event) {
            const target = event.target.closest('[data-stat]');
            if (!target) {
                this.hideTooltip();
                return;
            }
            const statKey = target.dataset.stat;
            const definition = STAT_TOOLTIPS[statKey];
            if (!definition) return;

            this.tooltip = definition;
            this.activeStat = statKey;

            const rect = target.getBoundingClientRect();
            let tooltipX = rect.right + 8;
            let tooltipY = rect.top - 10;

            const tooltipWidth = 280;
            const tooltipHeight = 350;
            if (tooltipX + tooltipWidth > window.innerWidth) {
                tooltipX = Math.max(8, rect.left - tooltipWidth - 8);
            }
            if (tooltipY + tooltipHeight > window.innerHeight) {
                tooltipY = Math.max(8, window.innerHeight - tooltipHeight - 8);
            }
            if (tooltipY < 0) tooltipY = 8;

            this.x = tooltipX;
            this.y = tooltipY;
            this.visible = true;
        },

        handleOut() {
            setTimeout(() => {
                if (!this.activeStat) return;
                const hovered = document.querySelector('[data-stat]:hover');
                if (!hovered) {
                    this.hideTooltip();
                }
            }, 100);
        },

        handleClick(event) {
            const target = event.target.closest('[data-stat]');
            if (!target) return;
            const statKey = target.dataset.stat;
            if (this.activeStat === statKey && this.visible) {
                this.openGlossary(statKey);
            }
        },

        hideTooltip() {
            this.visible = false;
            this.tooltip = null;
            this.activeStat = null;
        },

        openGlossary(statKey) {
            const definition = STAT_TOOLTIPS[statKey];
            if (!definition) return;
            this.glossaryStat = definition;
            this.glossaryOpen = true;
        },
    };
}
