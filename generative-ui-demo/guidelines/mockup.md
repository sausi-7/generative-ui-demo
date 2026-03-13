# UI Mockups & Dashboards

## Stat Grid (metric cards)
```html
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:1rem;margin-bottom:1.5rem">
  <div style="background:var(--color-surface);border-radius:12px;padding:1.25rem;border:1px solid var(--color-border)">
    <div style="font-size:12px;color:var(--color-text-muted);margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:.05em">Revenue</div>
    <div style="font-size:26px;font-weight:500;color:var(--color-text)">$48,200</div>
    <div style="font-size:12px;color:var(--color-success);margin-top:0.25rem">↑ 12% vs last month</div>
  </div>
</div>
```

## Badge / Tag
```html
<span style="display:inline-block;padding:2px 9px;background:rgba(124,58,237,0.15);
  color:var(--color-accent-light);border-radius:20px;font-size:12px;font-weight:500">
  Active
</span>
```

Status badge variants — use rgba matching each color variable:
- Success: `background:rgba(16,185,129,0.15); color:#34d399`
- Warning: `background:rgba(245,158,11,0.15); color:#fbbf24`
- Danger:  `background:rgba(239,68,68,0.15); color:#f87171`

## Progress Bar
```html
<div style="background:var(--color-surface);border-radius:999px;height:6px;margin:0.5rem 0">
  <div style="background:var(--color-accent);border-radius:999px;height:6px;width:65%;
              transition:width .3s ease"></div>
</div>
```

## Data Table
```html
<table style="width:100%;border-collapse:collapse;font-size:14px">
  <thead>
    <tr style="border-bottom:1px solid var(--color-border)">
      <th style="padding:0.6rem 0.75rem;text-align:left;color:var(--color-text-muted);
                 font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.05em">Name</th>
      <th style="padding:0.6rem 0.75rem;text-align:right;color:var(--color-text-muted);
                 font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.05em">Value</th>
    </tr>
  </thead>
  <tbody>
    <tr style="border-bottom:1px solid var(--color-border)">
      <td style="padding:0.65rem 0.75rem;color:var(--color-text)">Row name</td>
      <td style="padding:0.65rem 0.75rem;text-align:right;color:var(--color-text-muted)">Value</td>
    </tr>
  </tbody>
</table>
```

## Section Card
```html
<div style="background:var(--color-surface);border-radius:14px;padding:1.5rem;
            border:1px solid var(--color-border);margin-bottom:1rem">
  <div style="font-size:13px;font-weight:500;color:var(--color-text-muted);
              text-transform:uppercase;letter-spacing:.06em;margin-bottom:1rem">Section Title</div>
  <!-- content -->
</div>
```

## Icon + Label Row
```html
<div style="display:flex;align-items:center;gap:0.75rem;padding:0.75rem 0;
            border-bottom:1px solid var(--color-border)">
  <div style="width:32px;height:32px;background:rgba(124,58,237,0.12);border-radius:8px;
              display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0">
    ⚡
  </div>
  <div style="flex:1">
    <div style="font-size:14px;color:var(--color-text)">Feature name</div>
    <div style="font-size:12px;color:var(--color-text-muted)">Description</div>
  </div>
  <div style="font-size:14px;font-weight:500;color:var(--color-accent)">Value</div>
</div>
```
