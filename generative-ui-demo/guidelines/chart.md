# Charts with Chart.js

## Loading
```html
<canvas id="chart" style="width:100%;max-height:380px"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
const ctx = document.getElementById('chart').getContext('2d');
new Chart(ctx, { /* config */ });
</script>
```

Always load Chart.js via `<script src>` first, then your `<script>` block after.

## Base Config Template
```javascript
{
  type: 'bar', // bar | line | pie | doughnut | radar | scatter
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [{
      label: 'Revenue',
      data: [12000, 15000, 11000, 18000, 22000],
      backgroundColor: 'rgba(124,58,237,0.65)',
      borderColor: 'rgba(124,58,237,1)',
      borderWidth: 1,
      borderRadius: 4
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: {
        labels: { color: '#888', font: { size: 13 } }
      }
    },
    scales: {
      x: {
        ticks: { color: '#888', font: { size: 12 } },
        grid: { color: 'rgba(255,255,255,0.05)' }
      },
      y: {
        ticks: { color: '#888', font: { size: 12 } },
        grid: { color: 'rgba(255,255,255,0.05)' }
      }
    }
  }
}
```

## Color Palette (use these hex values — they match CSS variables)
| Color | Solid | Semi-transparent |
|---|---|---|
| Purple (accent) | `#7c3aed` | `rgba(124,58,237,0.65)` |
| Teal | `#0d9488` | `rgba(13,148,136,0.65)` |
| Amber | `#d97706` | `rgba(217,119,6,0.65)` |
| Rose | `#e11d48` | `rgba(225,29,72,0.65)` |
| Blue | `#2563eb` | `rgba(37,99,235,0.65)` |
| Green | `#16a34a` | `rgba(22,163,74,0.65)` |

## Line Chart
```javascript
{
  type: 'line',
  data: {
    labels: [...],
    datasets: [{
      label: 'Series',
      data: [...],
      borderColor: '#7c3aed',
      backgroundColor: 'rgba(124,58,237,0.1)',
      borderWidth: 2,
      tension: 0.4,
      fill: true,
      pointRadius: 4,
      pointBackgroundColor: '#7c3aed'
    }]
  }
}
```

## Multi-dataset
Use 2–4 datasets max. Each gets a distinct color from the palette above.

## Doughnut / Pie
```javascript
{
  type: 'doughnut',
  data: {
    labels: ['A', 'B', 'C'],
    datasets: [{
      data: [30, 45, 25],
      backgroundColor: ['rgba(124,58,237,0.8)', 'rgba(13,148,136,0.8)', 'rgba(217,119,6,0.8)'],
      borderWidth: 0
    }]
  },
  options: {
    plugins: {
      legend: { position: 'bottom', labels: { color: '#888', padding: 20 } }
    },
    cutout: '65%'
  }
}
```
