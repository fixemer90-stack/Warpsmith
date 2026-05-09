/**
 * battlefield_map.js — minimal SVG battlefield preview.
 * Replaces both old previews (F4.5 Canvas and F4.10 Leaflet) for scenario setup.
 * Requirements: real 2D table scale, mission-derived objectives, roster-derived units.
 */
function battlefieldMap() {
    return {
        svg: null,
        summary: null,
        mapWidth: 44,
        mapHeight: 60,
        mission: 'only-war',
        objectives: [],
        deployZones: null,
        units: [],
        pxPerInch: 10,
        padding: 28,

        initMap(width, height, missionOrObjectives, deployZones, units) {
            this.svg = document.getElementById('battlefield-map-svg');
            this.summary = document.getElementById('battlefield-map-summary');
            if (!this.svg) return;

            this.mapWidth = Number(width) || 44;
            this.mapHeight = Number(height) || 60;
            this.deployZones = deployZones || this.getDefaultDeployZones(this.mapWidth, this.mapHeight);
            this.units = Array.isArray(units) ? units : [];

            if (typeof missionOrObjectives === 'string') {
                this.mission = missionOrObjectives;
                this.objectives = this.getMissionObjectives(this.mission, this.mapWidth, this.mapHeight);
            } else if (Array.isArray(missionOrObjectives)) {
                this.mission = 'custom';
                this.objectives = missionOrObjectives;
            } else {
                this.objectives = this.getMissionObjectives(this.mission, this.mapWidth, this.mapHeight);
            }

            this.render();
        },

        getMissionObjectives(mission, width, height) {
            const cx = Math.floor(width / 2);
            const cy = Math.floor(height / 2);
            const flankOffset = Math.floor(cx / 2);
            const homeOffset = Math.floor(cy / 2);
            const objectives = [
                { x: cx, y: cy, label: 'Center' },
                { x: cx - flankOffset, y: cy, label: 'Flank L' },
                { x: cx + flankOffset, y: cy, label: 'Flank R' },
            ];

            if (mission === 'take-and-hold' || mission === 'purge-the-foe') {
                objectives.push(
                    { x: cx, y: cy - homeOffset, label: 'Home A' },
                    { x: cx, y: cy + homeOffset, label: 'Home B' }
                );
            }
            return objectives;
        },

        getDefaultDeployZones(width, height) {
            const zoneWidth = Math.max(1, Math.floor(width / 5));
            return {
                p1: { x: 0, y: 0, width: zoneWidth, height },
                p2: { x: width - zoneWidth, y: 0, width: zoneWidth, height },
            };
        },

        showUnits(units) {
            this.units = Array.isArray(units) ? units : [];
            this.render();
        },

        render() {
            if (!this.svg) return;
            const fieldW = this.mapWidth * this.pxPerInch;
            const fieldH = this.mapHeight * this.pxPerInch;
            const viewW = fieldW + this.padding * 2;
            const viewH = fieldH + this.padding * 2;
            this.svg.setAttribute('viewBox', `0 0 ${viewW} ${viewH}`);
            this.svg.setAttribute('data-width-inches', String(this.mapWidth));
            this.svg.setAttribute('data-height-inches', String(this.mapHeight));
            this.svg.style.aspectRatio = `${viewW} / ${viewH}`;

            const title = `${this.mapWidth}×${this.mapHeight}″ · ${this.formatMission(this.mission)} · ${this.objectives.length} objectives · ${this.units.length} units`;
            if (this.summary) this.summary.textContent = title;

            const parts = [];
            parts.push(`<rect x="0" y="0" width="${viewW}" height="${viewH}" fill="#020617"></rect>`);
            parts.push(`<rect x="${this.padding}" y="${this.padding}" width="${fieldW}" height="${fieldH}" rx="6" fill="#0f172a" stroke="#475569" stroke-width="1.5"></rect>`);
            parts.push(this.drawGrid(fieldW, fieldH));
            parts.push(this.drawDeployZones());
            parts.push(this.drawObjectives());
            parts.push(this.drawUnits());
            parts.push(this.drawScaleRuler());
            parts.push(this.drawAxisLabels());
            this.svg.innerHTML = parts.join('\n');
        },

        drawGrid(fieldW, fieldH) {
            const lines = [];
            for (let x = 0; x <= this.mapWidth; x += 6) {
                const px = this.padding + x * this.pxPerInch;
                const major = x % 12 === 0;
                lines.push(`<line x1="${px}" y1="${this.padding}" x2="${px}" y2="${this.padding + fieldH}" stroke="#334155" stroke-opacity="${major ? 0.55 : 0.28}" stroke-width="${major ? 1 : 0.6}"></line>`);
            }
            for (let y = 0; y <= this.mapHeight; y += 6) {
                const py = this.padding + y * this.pxPerInch;
                const major = y % 12 === 0;
                lines.push(`<line x1="${this.padding}" y1="${py}" x2="${this.padding + fieldW}" y2="${py}" stroke="#334155" stroke-opacity="${major ? 0.55 : 0.28}" stroke-width="${major ? 1 : 0.6}"></line>`);
            }
            return `<g class="battlefield-grid">${lines.join('')}</g>`;
        },

        drawDeployZones() {
            const zone = this.getDefaultDeployZones(this.mapWidth, this.mapHeight);
            const rect = (z, color, label) => {
                const x = this.padding + z.x * this.pxPerInch;
                const y = this.padding + z.y * this.pxPerInch;
                const w = z.width * this.pxPerInch;
                const h = z.height * this.pxPerInch;
                return `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${color}" fill-opacity="0.20" stroke="${color}" stroke-opacity="0.75" stroke-width="1"></rect><text x="${x + w / 2}" y="${y + 18}" fill="${color}" font-size="11" text-anchor="middle" font-weight="700">${label}</text></g>`;
            };
            return `<g class="deployment-zones">${rect(zone.p1, '#3b82f6', 'P1 DEPLOY')}${rect(zone.p2, '#ef4444', 'P2 DEPLOY')}</g>`;
        },

        drawObjectives() {
            const items = this.objectives.map((obj, idx) => {
                const x = this.padding + obj.x * this.pxPerInch;
                const y = this.padding + obj.y * this.pxPerInch;
                const label = this.escape(obj.label || `Objective ${idx + 1}`);
                return `<g class="objective" data-label="${label}"><circle cx="${x}" cy="${y}" r="13" fill="#fbbf24" fill-opacity="0.78" stroke="#fde68a" stroke-width="2"></circle><circle cx="${x}" cy="${y}" r="30" fill="none" stroke="#fbbf24" stroke-opacity="0.22" stroke-width="1" stroke-dasharray="4 4"></circle><text x="${x}" y="${y + 4}" text-anchor="middle" fill="#111827" font-size="11" font-weight="800">${idx + 1}</text><title>${label} (${obj.x}, ${obj.y})</title></g>`;
            });
            return `<g class="objectives">${items.join('')}</g>`;
        },

        drawUnits() {
            const used = new Map();
            const items = this.units.map((unit) => {
                const key = `${unit.x},${unit.y}`;
                const stack = used.get(key) || 0;
                used.set(key, stack + 1);
                const x = this.padding + Number(unit.x || 0) * this.pxPerInch + (stack % 3) * 7;
                const y = this.padding + Number(unit.y || 0) * this.pxPerInch + Math.floor(stack / 3) * 7;
                const color = unit.color || (unit.player === 1 ? '#3b82f6' : '#ef4444');
                const name = this.escape(unit.name || 'Unit');
                const initials = this.escape(this.unitInitials(unit.name || '?'));
                return `<g class="map-unit map-unit-p${unit.player || ''}" data-unit="${name}"><circle cx="${x}" cy="${y}" r="9" fill="${color}" stroke="#e5e7eb" stroke-width="1.5"></circle><text x="${x}" y="${y + 3}" text-anchor="middle" fill="#ffffff" font-size="7" font-weight="800">${initials}</text><title>${name}${unit.faction ? ` (${this.escape(unit.faction)})` : ''} — ${Math.round(unit.x)}, ${Math.round(unit.y)}</title></g>`;
            });
            return `<g class="units">${items.join('')}</g>`;
        },

        drawScaleRuler() {
            const x = this.padding;
            const y = this.padding + this.mapHeight * this.pxPerInch + 17;
            const length = 12 * this.pxPerInch;
            return `<g class="scale-ruler"><line x1="${x}" y1="${y}" x2="${x + length}" y2="${y}" stroke="#94a3b8" stroke-width="2"></line><line x1="${x}" y1="${y - 5}" x2="${x}" y2="${y + 5}" stroke="#94a3b8" stroke-width="2"></line><line x1="${x + length}" y1="${y - 5}" x2="${x + length}" y2="${y + 5}" stroke="#94a3b8" stroke-width="2"></line><text x="${x + length / 2}" y="${y + 16}" fill="#94a3b8" text-anchor="middle" font-size="10">12″</text></g>`;
        },

        drawAxisLabels() {
            const fieldW = this.mapWidth * this.pxPerInch;
            const fieldH = this.mapHeight * this.pxPerInch;
            return `<g class="axis-labels" fill="#64748b" font-size="10"><text x="${this.padding + fieldW / 2}" y="${this.padding - 10}" text-anchor="middle">width ${this.mapWidth}″</text><text x="${this.padding + fieldW + 18}" y="${this.padding + fieldH / 2}" text-anchor="middle" transform="rotate(90 ${this.padding + fieldW + 18} ${this.padding + fieldH / 2})">height ${this.mapHeight}″</text></g>`;
        },

        formatMission(mission) {
            return String(mission || '')
                .replace(/-/g, ' ')
                .replace(/\b\w/g, (m) => m.toUpperCase());
        },

        unitInitials(name) {
            const words = String(name).split(/\s+/).filter(Boolean);
            if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
            return words.slice(0, 2).map(w => w[0]).join('').toUpperCase();
        },

        escape(value) {
            return String(value)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        },

        destroy() {
            if (this.svg) this.svg.innerHTML = '';
        },
    };
}
