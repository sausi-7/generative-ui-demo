# Interactive Widgets

## Sliders & Controls
Use HTML range inputs — they're styled by the browser and adapt to the design system.

```html
<style>
label { display:block; font-size:13px; color:var(--color-text-muted); margin-bottom:4px }
input[type=range] { width:100%; accent-color:var(--color-accent); cursor:pointer }
</style>
<div style="margin-bottom:1.25rem">
  <label>Annual rate — <strong id="rv">7%</strong></label>
  <input type="range" min="1" max="20" step="0.5" value="7"
         oninput="document.getElementById('rv').textContent=this.value+'%'; recalc()">
</div>
```

Show the live value inline in the label — update it with `oninput`.

## Metric / Result Card
```html
<div style="background:var(--color-surface);border-radius:12px;padding:1.5rem;
            border:1px solid var(--color-border);margin-bottom:1rem">
  <div style="font-size:13px;color:var(--color-text-muted);margin-bottom:0.5rem">Final Amount</div>
  <div style="font-size:32px;font-weight:500;color:var(--color-accent)" id="result">$19,672</div>
  <div style="font-size:13px;color:var(--color-text-muted);margin-top:0.25rem">
    Interest: <span id="interest">$9,672</span>
  </div>
</div>
```

## Input Field
```html
<input type="text" style="width:100%;padding:0.6rem 0.9rem;background:var(--color-surface);
  border:1px solid var(--color-border);border-radius:8px;color:var(--color-text);
  font-size:15px;outline:none" placeholder="Enter value...">
```

## Button
```html
<button style="padding:0.6rem 1.2rem;background:var(--color-accent);color:#fff;
  border:none;border-radius:8px;cursor:pointer;font-size:15px;font-weight:500">
  Calculate
</button>
```

## Script Pattern for Calculators
Put all state in module-level `let` variables. Use `oninput` on each control.

```html
<script>
let principal = 10000, rate = 7, years = 10;

function recalc() {
  const amount = principal * Math.pow(1 + rate / 100, years);
  document.getElementById('result').textContent = '$' + Math.round(amount).toLocaleString();
}

recalc(); // initial render
</script>
```

## Timer Pattern
```html
<script>
let seconds = 0;
const display = document.getElementById('time');
const timer = setInterval(() => {
  seconds++;
  display.textContent = String(Math.floor(seconds/60)).padStart(2,'0')
    + ':' + String(seconds%60).padStart(2,'0');
}, 1000);
</script>
```

## Grid Layout for Controls
```html
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem">
  <!-- left control -->
  <!-- right control -->
</div>
```
