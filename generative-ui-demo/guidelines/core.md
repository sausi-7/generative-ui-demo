# Core Design System

## HTML Structure
- HTML fragments only — no DOCTYPE, <html>, <head>, or <body>
- Streaming order: `<style>` → content HTML → `<script>` (critical for smooth streaming)
- No comments (`<!-- -->` or `/* */`) — waste tokens during streaming
- No `display:none` sections, tabs, or carousels during streaming — stack content vertically
- Scripts execute after streaming completes — safe to use CDN globals in a trailing `<script>`

## CSS Variables (mandatory — never hardcode colors)
| Variable | Purpose |
|---|---|
| `--color-bg` | Page background |
| `--color-surface` | Card / panel background |
| `--color-surface-elevated` | Elevated panel |
| `--color-text` | Primary text |
| `--color-text-muted` | Secondary / hint text |
| `--color-accent` | Purple highlight |
| `--color-accent-light` | Lighter purple |
| `--color-border` | Subtle borders |
| `--color-success` | Green |
| `--color-warning` | Amber |
| `--color-danger` | Red |

## Typography
- `h1`: 22px, weight 500
- `h2`: 18px, weight 500
- `h3`: 16px, weight 500
- Body: 16px, weight 400, line-height 1.6
- Labels/captions: 13px
- Never below 11px

## Design Rules
- **Flat design only** — no gradients, box-shadow, blur, text-shadow, or glow
- No outer background color on root container — host provides the page background
- Border radius: 6px (small), 10px (medium), 16px (large/cards)
- CDN allowed: `cdnjs.cloudflare.com`, `cdn.jsdelivr.net`, `unpkg.com`, `esm.sh` only

## Two-Way Communication
`window.sendToAgent(data)` — sends JSON data back to chat as a user message.

```html
<button onclick="sendToAgent({action:'filter', value:'weekly'})">Weekly</button>
<select onchange="sendToAgent({selected: this.value})">...</select>
```

Use it for: filter selections, form submissions, quiz answers, calculator results to analyze.
