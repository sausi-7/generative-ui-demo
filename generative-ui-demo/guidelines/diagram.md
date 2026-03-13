# SVG Diagrams

## SVG Shell
```html
<svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;height:auto;display:block">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0,0 L10,5 L0,10 Z" fill="#666"/>
    </marker>
  </defs>
  <!-- nodes and edges -->
</svg>
```

Always define `<defs>` first so arrow markers are available during streaming.

## Node Types

**Default box:**
```html
<rect x="50" y="50" width="130" height="44" rx="6"
      fill="#1a1a1a" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
<text x="115" y="77" text-anchor="middle" fill="#e8e8e8" font-size="13"
      font-family="system-ui,sans-serif">Node Label</text>
```

**Accented box (highlighted):**
```html
<rect x="50" y="50" width="130" height="44" rx="6"
      fill="rgba(124,58,237,0.15)" stroke="#7c3aed" stroke-width="1.5"/>
<text x="115" y="77" text-anchor="middle" fill="#a78bfa" font-size="13"
      font-family="system-ui,sans-serif">Highlighted</text>
```

**Success / Warning / Danger:**
```html
fill="rgba(16,185,129,0.12)" stroke="#10b981"  <!-- success -->
fill="rgba(245,158,11,0.12)" stroke="#f59e0b"  <!-- warning -->
fill="rgba(239,68,68,0.12)"  stroke="#ef4444"  <!-- danger -->
```

**Pill / rounded:**
```html
<rect ... rx="22"/>  <!-- use rx matching half height for full pill -->
```

## Edges & Arrows

**Straight arrow:**
```html
<line x1="180" y1="72" x2="260" y2="72"
      stroke="#555" stroke-width="1.5" marker-end="url(#arrow)"/>
```

**Labeled edge:**
```html
<line x1="180" y1="72" x2="260" y2="72" stroke="#555" stroke-width="1.5" marker-end="url(#arrow)"/>
<text x="220" y="65" text-anchor="middle" fill="#666" font-size="11"
      font-family="system-ui,sans-serif">calls</text>
```

**Curved path (for loopbacks or crossing lines):**
```html
<path d="M 180 72 C 220 30, 260 30, 300 72" fill="none"
      stroke="#555" stroke-width="1.5" marker-end="url(#arrow)"/>
```

## Layout Tips
- Horizontal flow: left → right, 160–180px between node centers
- Vertical flow: top → bottom, 80–100px between rows
- Keep viewBox proportional to content — 800×400 for wide, 600×500 for tall
- Max 2 accent colors per diagram
- Every `<text>` needs explicit `fill` — never rely on inheritance

## Section Headers in Diagrams
```html
<text x="400" y="25" text-anchor="middle" fill="#555" font-size="13"
      font-family="system-ui,sans-serif" font-weight="500">Section Title</text>
```
