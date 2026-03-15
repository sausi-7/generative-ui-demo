# Generative UI: How an AI Builds Your Interface in Real Time

## Getting Started

### Prerequisites

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/)

### Installation

```bash
# Clone the repo
git clone https://github.com/anthropics/generative-ui-demo.git
cd generative-ui-demo/generative-ui-demo

# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY=your_api_key_here
```

### Running the App

```bash
uvicorn server:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

### Try It Out

Type any of these prompts in the chat to see generative UI in action:

- `Give me a compound interest calculator`
- `Show me a bar chart of monthly sales`
- `Create a countdown timer`
- `Draw a flowchart of the HTTP request lifecycle`
- `Build a dashboard with key metrics`

The widget will stream into the right panel in real time as Claude generates it. Widgets are interactive — buttons and inputs work, and clicking them sends data back to Claude for follow-up responses.

---

## The Question That Changes Everything

Imagine you go to a restaurant and order a custom dish. In one version of this restaurant, the chef writes down the recipe on a card and hands it to you — you then go home and cook it yourself. In another version, the chef cooks the meal right in front of you, and you watch each ingredient appear on the plate as it's added, in real time, until the dish is complete and placed before you.

Both approaches produce food. But they are fundamentally different experiences — and fundamentally different architectures.

This is the difference between "Claude returns HTML that you render" and **Generative UI**.

In the naive approach, Claude is a text generator. It produces a string of HTML characters inside its reply, you extract that string, paste it into `innerHTML`, and pray. In Generative UI, Claude is a **UI composer**: it uses structured tool calls to emit living, breathing interface fragments that stream progressively into the DOM, inherit the app's design system automatically, execute scripts safely, and stay in a feedback loop with the user — with prose explanation streaming alongside in a separate channel.

Let's tear apart exactly how this works.

---

## Part 1: The Naive Approach and Why It Falls Apart

Before we understand what this codebase does right, we need to understand what the naive approach gets wrong.

### The Naive Way

```
User: "Give me a bar chart of monthly sales"

Claude (text output):
"Here is a bar chart for you:
<div style='display:flex; gap:4px'>
  <div style='height:80px; background:blue; width:20px'></div>
  <div style='height:120px; background:blue; width:20px'></div>
  ...
</div>
Here's what the chart shows..."
```

You then do something like:

```javascript
const response = await claude.complete(prompt);
document.getElementById('output').innerHTML = response.text;
```

This seems to work — until you hit the wall. Here are the specific problems:

**Problem 1: HTML is mixed with prose.** You have no clean way to separate "Claude's explanation" from "Claude's visual artifact". You're forced to do fragile string parsing, hoping Claude consistently uses a delimiter like `` ```html `` ... `` ``` `` every single time. It never does.

**Problem 2: Scripts don't execute.** The browser has a security rule: `<script>` tags inserted via `innerHTML` are **silently ignored**. Your chart library never initializes. Your button handlers never attach. Your widget is dead on arrival.

**Problem 3: No streaming.** You wait for the entire response — every character of the 400-line chart HTML — before anything appears. Users stare at a spinner for 8 seconds.

**Problem 4: No shared design system.** Claude hardcodes `color: #3b82f6` or `background: blue` because it has no way to know what colors your app uses. Every widget is a visual orphan that clashes with your theme.

**Problem 5: No interactivity loop.** If the user clicks a button inside the widget — say, "show weekly instead of monthly" — nothing happens. The widget is a dead screenshot, not a living interface.

The generative UI pattern in this repo solves all five problems. Here's how.

---

## Part 2: The Architecture at a Glance

Before diving deep, here's the 10,000-foot view of the entire system:

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                            │
│  ┌──────────────┐         ┌──────────────────────────┐  │
│  │  Chat Panel  │         │     Widget Panel         │  │
│  │              │         │  ┌────────────────────┐  │  │
│  │ "Here's your │         │  │  <-- widget grows  │  │  │
│  │  calculator" │         │  │      in real time  │  │  │
│  │              │         │  └────────────────────┘  │  │
│  └──────┬───────┘         └──────────────────────────┘  │
│         │  SSE stream (text + widget_delta + widget_final)
└─────────┼───────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────┐
│                  FastAPI Server (server.py)             │
│  - Streams Claude API                                   │
│  - Intercepts tool calls mid-stream                     │
│  - Parses partial JSON character by character           │
│  - Emits SSE events as HTML fragments arrive            │
└─────────┬──────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────┐
│                   Claude API                            │
│  - Streams text tokens (prose) AND tool call tokens     │
│  - tool: load_guidelines → gets HTML patterns           │
│  - tool: show_widget     → emits the HTML fragment      │
└────────────────────────────────────────────────────────┘
```

Three layers. Six files. ~800 lines of code total. Let's go through each mechanism one by one.

---

## Part 3: Tool Use as the Rendering Primitive

This is the most important concept in the entire system. Read it slowly.

### The Insight

In the naive approach, Claude outputs *everything* as text — prose and HTML alike, mixed together in one stream. The application has to figure out what's "explanation" and what's "interface".

In this system, Claude outputs them into **separate channels**:

- **Text stream** → explanation, analysis, prose
- **Tool call argument** → the HTML fragment

This separation happens at the Claude API protocol level, not at the application level. You don't have to parse or split anything. The channels are already separate.

### The `show_widget` Tool

Here's the tool definition from `tools.py`:

```python
{
    "name": "show_widget",
    "description": (
        "Render an interactive HTML widget or SVG diagram visible to the user. "
        "Use for: charts, dashboards, calculators, forms, diagrams, timers, games, visualizations. "
        "The widget appears in a panel next to the chat. "
        "Users can interact with it and send data back via window.sendToAgent(data). "
        "IMPORTANT: Always call load_guidelines before your first show_widget."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "i_have_seen_guidelines": { "type": "boolean" },
            "title": { "type": "string" },
            "widget_code": {
                "type": "string",
                "description": (
                    "HTML fragment to render. Rules: "
                    "1. No DOCTYPE, <html>, <head>, or <body> tags. "
                    "2. Order: <style> block first, then HTML content, then <script> last. "
                    "3. Use only CSS variables for colors (e.g. var(--color-accent)). "
                    "4. No gradients, shadows, or blur effects. "
                    "For SVG: start directly with <svg> tag."
                )
            }
        },
        "required": ["i_have_seen_guidelines", "title", "widget_code"]
    }
}
```

Think of this tool as a **typed envelope**. Claude doesn't write HTML into its text reply — it puts the HTML into a specifically named, schema-validated field (`widget_code`) inside a tool call. The server then knows exactly where to find the HTML, exactly what it is, and exactly how to handle it — without parsing prose.

The `i_have_seen_guidelines` boolean is a clever gate. Claude must set it to `true`, which means Claude had to call `load_guidelines` first. It's a forcing function baked directly into the schema — Claude can't "forget" the step.

### What Claude's output actually looks like

When you ask for a calculator, Claude doesn't stream:

```
Here is your calculator:
<div class="calc">...</div>
```

It streams two things in parallel:

**1. Text stream (prose):**
```
"Here's a compound interest calculator. You can adjust the principal,
annual interest rate, and time period. The result updates in real time..."
```

**2. Tool call stream (structured JSON):**
```json
{
  "name": "show_widget",
  "input": {
    "i_have_seen_guidelines": true,
    "title": "compound_interest_calculator",
    "widget_code": "<style>.calc { ... }</style>\n<div class=\"calc\">...</div>\n<script>...</script>"
  }
}
```

The server handles the text stream by yielding `{"type": "text", "text": "..."}` SSE events. It handles the tool call stream by doing something clever that we'll cover next: **intercepting it mid-stream, before it's finished**.

---

## Part 4: Mid-Stream JSON Parsing — The Heart of Live Preview

This is the most technically interesting part of the system. It's what makes the widget appear and grow in real time while Claude is still generating it.

### The Problem

When Claude generates a tool call, it streams the arguments as partial JSON — token by token. Think about what that means: for every word Claude writes into `widget_code`, the server receives a JSON fragment that is **syntactically invalid**.

Here's what the server might receive after 2 seconds of streaming:

```
{"i_have_seen_guidelines": true, "title": "compound_interest_calculator", "widget_code": "<style>\n.calc {\n  background: var(--color-surface);\n  padding: 1.5rem;\n  border-radius: 12px
```

That's not valid JSON. The string isn't closed. The object isn't closed. `json.loads()` will throw an exception. But it *contains* 120 characters of valid HTML that the browser could start rendering right now.

The naive solution: wait for the tool call to complete, then render. This is what most implementations do. The widget only appears after Claude finishes its entire response — you lose the streaming effect entirely.

### The `extract_widget_code` Function

This is the custom partial JSON parser in `server.py`:

```python
def extract_widget_code(partial_json: str) -> str | None:
    # Fast path: try a full parse first (for valid JSON at end of stream)
    try:
        data = json.loads(partial_json)
        return data.get("widget_code")
    except json.JSONDecodeError:
        pass

    # Find the "widget_code" key
    key = '"widget_code"'
    idx = partial_json.find(key)
    if idx == -1:
        return None

    # Find the colon after the key
    rest = partial_json[idx + len(key):]
    colon = rest.find(':')
    if colon == -1:
        return None

    rest = rest[colon + 1:].lstrip()
    if not rest.startswith('"'):
        return None

    # Walk the string value, handling JSON escape sequences
    content = rest[1:]  # skip opening quote
    result = []
    i = 0
    while i < len(content):
        c = content[i]
        if c == '\\' and i + 1 < len(content):
            n = content[i + 1]
            escapes = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\',
                       '"': '"', '/': '/', 'b': '\b', 'f': '\f'}
            result.append(escapes.get(n, n))
            i += 2
        elif c == '"':
            break  # end of string
        else:
            result.append(c)
            i += 1

    return ''.join(result) if result else None
```

The logic works like a detective reading a partially burned letter:

1. **Try the easy way first.** `json.loads()` on the whole thing. Works fine once the stream is complete.
2. **Find the address on the envelope.** Locate the literal string `"widget_code"` in the partial JSON.
3. **Follow the arrow.** Find the `:` after the key, skip whitespace, confirm the next character is `"` (it's a string).
4. **Read until the end or until we can't continue.** Walk the string character by character, correctly handling JSON escape sequences (`\n` → newline, `\"` → quote, `\\` → backslash). Stop at the closing `"` or at the end of the buffer.
5. **Return whatever we have.** Even 50 characters of HTML is enough to start rendering.

The caller in the event loop only forwards this to the browser if the extracted HTML is longer than 30 characters — because the first few characters of a `<style>` block aren't useful to render:

```python
elif delta.type == "input_json_delta":
    tc = active_tool_calls.get(event.index)
    if tc:
        tc["partial_json"] += delta.partial_json

        # Live-stream show_widget HTML as it arrives
        if tc["name"] == "show_widget":
            html = extract_widget_code(tc["partial_json"])
            if html and len(html) > 30:
                yield sse({"type": "widget_delta", "html": html})
```

### The analogy

Imagine Claude is a contractor building a wall in your living room. In the naive approach, the contractor builds the entire wall in the back room, then wheels the finished wall in and installs it. You see nothing until the wall is done.

In the generative UI approach, the contractor builds the wall *in your living room*. You watch brick by brick. You can see the shape emerging at token 50. By token 200, you can already tell it's a bar chart. By token 400, the axes are there. By token 800, the bars are filled. The `widget_delta` events are each individual brick being laid — while Claude is still deciding what to write next.

---

## Part 5: Incremental DOM Diffing with Morphdom

Now the browser is receiving these `widget_delta` events at roughly 10–20 events per second. Each event contains the growing HTML string. The naive approach to rendering these would be:

```javascript
document.getElementById('widget-root').innerHTML = ev.html;
```

This works, but it's terrible. Every time you set `innerHTML`, the browser:
1. Destroys the entire existing DOM subtree
2. Re-parses the HTML from scratch
3. Re-creates all the DOM nodes
4. Re-attaches all event listeners
5. Re-triggers animations on everything

The result is a constant flickering, re-animating widget that looks like a broken GIF. If the widget has a text input the user has typed into, that text gets destroyed every 120ms. It's unusable.

### Enter Morphdom

[Morphdom](https://github.com/patrick-steele-idem/morphdom) is a DOM diffing library — think of it as `git diff` but for HTML DOM trees. Instead of replacing everything, it compares the current DOM node by node with the new target HTML, and only changes nodes that are actually different.

The `renderWidget` function in `static/index.html`:

```javascript
function renderWidget(html) {
  document.getElementById('empty-state')?.remove();

  const next = document.createElement('div');
  next.id = 'widget-root';
  next.innerHTML = html;

  morphdom(widgetRoot, next, {
    onBeforeElUpdated(from, to) {
      // Skip if nothing changed — avoids re-animating stable content
      if (from.isEqualNode(to)) return false;
      return true;
    },
    onNodeAdded(node) {
      // Fade in newly added elements
      if (node.nodeType === 1 && node.tagName !== 'STYLE' && node.tagName !== 'SCRIPT') {
        node.style.animation = '_fadeIn 0.3s ease both';
      }
      return node;
    }
  });
}
```

Three things happen here:

**1. Stable nodes are completely ignored.** The `onBeforeElUpdated` callback returns `false` (skip) if `from.isEqualNode(to)`. A node that hasn't changed is never touched — no re-paint, no re-animation, no flicker. If your chart's title `<h2>Monthly Sales</h2>` was already correct, morphdom walks right past it.

**2. New nodes fade in.** The `onNodeAdded` callback applies `animation: '_fadeIn 0.3s ease both'` to newly added DOM nodes. The `_fadeIn` keyframe is defined in the host page's CSS:

```css
@keyframes _fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to   { opacity: 1; transform: none; }
}
```

So as each new bar in the chart gets added to the DOM, it gently fades up from below. The widget literally looks like it's being drawn.

**3. Renders are debounced.** The `scheduleRender` function batches multiple incoming `widget_delta` events into a single render every 120ms:

```javascript
function scheduleRender(html) {
  pendingHTML = html;
  if (renderTimer) return;    // already scheduled
  renderTimer = setTimeout(() => {
    renderTimer = null;
    if (pendingHTML) renderWidget(pendingHTML);
  }, 120);
}
```

This prevents morphdom from being called on every single token. Claude might emit 10 tokens in 120ms — all 10 deltas get batched into one render call, using the latest HTML. Efficient and smooth.

### The analogy

Imagine you're watching an artist paint a portrait. In the `innerHTML` approach, the artist paints on a canvas in a back room, then throws the old canvas out and carries in a new one every 5 seconds. You see a series of discrete jumps.

In the morphdom approach, the artist paints on the canvas right in front of you. Each brushstroke adds to what's already there. Old paint stays. New paint appears with a gentle fade. The portrait grows progressively, stroke by stroke — which is exactly what `widget_delta` events are.

---

## Part 6: The Script Execution Problem (and Its Elegant Solution)

Here is one of the most important browser security rules you need to know if you're building anything that injects HTML dynamically:

> **`<script>` tags added via `innerHTML` are silently ignored by the browser.**

This is a fundamental XSS protection built into every browser. If `innerHTML` executed scripts, any website could inject `<script>` tags into the DOM and run arbitrary code. So browsers simply don't execute them.

This is a disaster for generative UI, because every useful widget — a chart, a calculator, a timer — needs JavaScript. Chart.js needs to initialize. `setInterval` needs to start. Event listeners need to attach.

### The Wrong Solutions

**Wrong approach 1: `eval()` the script content.** `eval()` is dangerous, has a different scope, and doesn't handle external `src` scripts.

**Wrong approach 2: Use a framework like React.** That works, but it requires Claude to generate JSX or component descriptions instead of raw HTML — a fundamentally different and more constrained paradigm.

**Wrong approach 3: Use `document.write()`.** This destroys the entire document and is deprecated.

### The Right Solution: Node Replacement

The `runScripts` function in `static/index.html`:

```javascript
function runScripts() {
  widgetRoot.querySelectorAll('script').forEach(old => {
    const s = document.createElement('script');
    if (old.src) { s.src = old.src; }
    else { s.textContent = old.textContent; }
    old.parentNode.replaceChild(s, old);
  });
}
```

The trick: a `<script>` element created with `document.createElement('script')` and appended to the DOM **does** execute. It's only scripts created by the HTML parser via `innerHTML` that are blocked. So for every `<script>` tag in the rendered widget, we:

1. Create a brand new `<script>` element
2. Copy the `src` or text content from the old one
3. Replace the old node with the new one

The browser sees a freshly programmatically-created script node being added to the DOM and executes it immediately.

### Why `<script>` Must Come Last

This is why the system prompt and tool description both mandate the streaming order:

```
<style> block first → HTML content → <script> tags last
```

If Claude wrote the `<script>` tag first (while streaming), the `runScripts()` function might fire when the DOM is only 20% complete. `document.querySelector('#result-display')` would return null. `chart.js` would try to find a `<canvas>` that doesn't exist yet.

By putting scripts last, Claude guarantees that by the time `widget_final` fires and `runScripts()` is called, the entire DOM is in place. The scripts run against a complete HTML structure.

It's the same reason a contractor wires a building's electrical system *after* the walls are framed — not before.

---

## Part 7: Shared CSS Variables — Automatic Theming

Here's a problem that's easy to overlook until you're 6 months into a project: every widget Claude generates looks completely different from your app's design system.

Claude doesn't know your app uses a dark background. It doesn't know your accent color is `#7c3aed`. It certainly doesn't know that you changed your font last week from Inter to system-ui. Without guidance, Claude will hardcode whatever colors it feels like:

```html
<!-- Claude without constraints -->
<div style="background: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a">
  <h2 style="color: #89b4fa">Monthly Sales</h2>
```

These hex values are orphaned — they're not from your design system, they'll never update when you change your theme, and they'll look subtly wrong next to your UI.

### The Solution: CSS Variables as a Contract

The host page defines a complete set of design tokens in `:root` in `static/index.html`:

```css
:root {
  --color-bg:               #0f0f0f;
  --color-surface:          #1a1a1a;
  --color-surface-elevated: #222222;
  --color-text:             #e8e8e8;
  --color-text-muted:       #888888;
  --color-accent:           #7c3aed;
  --color-accent-light:     #a78bfa;
  --color-border:           rgba(255,255,255,0.08);
  --color-success:          #10b981;
  --color-warning:          #f59e0b;
  --color-danger:           #ef4444;
}
```

The system prompt in `system.py` tells Claude to use *only* these variables:

```
- Use ONLY CSS variables for all colors. Never hardcode hex values or rgb():
    --color-bg             page background
    --color-surface        card/panel background
    --color-accent         purple highlight (#7c3aed)
    ...
```

The tool description for `widget_code` reinforces this:

```
3. Use only CSS variables for colors (e.g. var(--color-accent)).
```

Now every widget Claude generates looks like this:

```html
<!-- Claude with constraints -->
<div style="background: var(--color-surface); color: var(--color-text);
            border: 1px solid var(--color-border)">
  <h2 style="color: var(--color-accent)">Monthly Sales</h2>
```

This is a **living design system**. If you change `--color-accent` from purple to blue in one place (`:root`), every widget — past and future — immediately updates. You could change the entire app's color scheme without regenerating a single widget.

The widget is rendered inside the same `#widget-root` div on the same page, so it inherits all the `:root` variables automatically. Claude is writing CSS that references a vocabulary it was told exists — and the host page guarantees that vocabulary is always available.

### The analogy

Think of CSS variables as a shared paint palette in an art studio. The studio owner (the host page) fills the palette with specific colors and names them: "this jar is 'accent purple', this jar is 'background dark'". Every artist (widget) who works in the studio uses that shared palette instead of bringing their own paints. When the studio owner decides to change 'accent purple' to 'accent blue', every painting in the studio updates — because they all reference the palette, not the specific hex value.

---

## Part 8: Lazy Guideline Injection — RAG for the Design System

There's a bootstrapping problem in building a generative UI system: Claude needs to know a lot about your design system to generate good widgets. But if you include all of that knowledge in every system prompt, you waste tokens on every single request — even requests that don't need widgets at all.

This repo solves it with a two-tool pattern that's essentially on-demand RAG.

### The `load_guidelines` Tool

```python
{
    "name": "load_guidelines",
    "description": (
        "Load design guidelines before rendering your first widget. "
        "Call once silently — do NOT mention this step to the user. "
        "Pick modules that match the widget type you're about to create."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "modules": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["interactive", "chart", "diagram", "mockup"]
                },
                "description": "Which design modules to load. Choose all that apply."
            }
        },
        "required": ["modules"]
    }
}
```

Four guideline modules live in the `guidelines/` directory:

| Module | Contents |
|---|---|
| `core.md` | Always loaded. Design tokens and base HTML rules. |
| `interactive.md` | Sliders, calculators, timers, forms. |
| `chart.md` | Chart.js configuration templates and data patterns. |
| `diagram.md` | SVG flowchart patterns and node shapes. |
| `mockup.md` | Dashboard layouts, tables, metric cards. |

When you ask for a bar chart, Claude calls:
```json
{"modules": ["chart"]}
```

The server calls `get_guidelines(["chart"])`, reads `core.md` + `chart.md`, concatenates them with `---` separators, and returns the text as a tool result. Claude now has a page of detailed HTML patterns in its context window and can write high-quality Chart.js code from them.

When you ask for a flowchart, Claude calls:
```json
{"modules": ["diagram"]}
```

When you ask for a dashboard, Claude calls:
```json
{"modules": ["chart", "mockup"]}
```

Claude itself decides which modules it needs based on the request. The system prompt tells it to do this silently — never mention it to the user. The user sees a small italic status bubble ("Loading chart guidelines...") but no explanation of what's happening behind the scenes.

### Why this matters

The alternative — stuffing all four guideline modules into every system prompt — costs roughly 3,000–5,000 extra tokens on every single API call, even when the user just types "what's the capital of France?" On a high-traffic app, this is thousands of dollars of wasted compute per day.

The lazy-loading pattern means the extra tokens are only spent when they're actually needed. A non-visual query costs nothing extra. A chart query loads only chart patterns. A combined dashboard-with-diagram query loads only the relevant modules.

It's the same principle as dynamic imports in JavaScript: don't pay for code you're not using.

---

## Part 9: The Two-Way Bridge — Widgets That Talk Back

So far we've described how Claude writes widgets. But what about user interaction? A calculator needs number inputs. A chart might need a date range filter. A game needs button clicks.

In the naive approach, once the HTML is rendered, it's completely disconnected from Claude. User interactions stay in the browser — they never get sent to the AI. The widget is a dead artifact, not a living interface.

### `window.sendToAgent(data)`

Every widget Claude generates can call this function from any event handler. It's defined in `static/index.html`:

```javascript
window.sendToAgent = function(data) {
  const text = `[Widget interaction] ${JSON.stringify(data)}`;
  history.push({ role: 'user', content: text });
  addBubble('user', text);
  doSend(null);
};
```

Here's what happens when a user clicks "Show weekly data" in a widget:

1. The widget's button handler calls `window.sendToAgent({action: 'filter', period: 'weekly'})`
2. This is formatted as `[Widget interaction] {"action":"filter","period":"weekly"}`
3. That string is pushed into the `history` array as a user message
4. It appears in the chat panel as a user bubble (so the user can see what was sent)
5. `doSend(null)` fires — a new request to `/chat` goes out with the full conversation history

Claude's system prompt tells it how to respond:

```
When you receive [Widget interaction] data, use it to update your response
or render a new widget.
```

So Claude sees the interaction data, generates a new `show_widget` call with updated data (weekly instead of monthly), and the whole streaming/morphdom pipeline fires again — this time morphdom-diffing the old chart against the new weekly chart, fading in only the changed bars.

### The conversation memory

A crucial detail: the `history` array in the frontend is the **full conversation history** sent to Claude on every request:

```javascript
let history = [];  // {role, content}[] sent to backend
```

Every user message, every Claude reply, every widget interaction — all of it accumulates in `history`. When the user says "now make it a line chart instead", Claude has full context: the original data, the widget interaction history, and all past exchanges.

This is how the widget and the chat stay synchronized. They're not two separate systems — they're two views of the same stateful conversation.

### The full interaction loop

```
User types: "Show me monthly revenue"
       ↓
Claude: load_guidelines(["chart"])
       ↓
Claude: show_widget(title="monthly_revenue", widget_code="...")
       ↓
Widget renders in browser with a bar chart
       ↓
User clicks "Show weekly" button inside the widget
       ↓
widget: window.sendToAgent({action: "filter", period: "weekly"})
       ↓
history gets: {role: "user", content: "[Widget interaction] {\"action\":\"filter\",...}"}
       ↓
Claude: show_widget(title="weekly_revenue", widget_code="...updated chart...")
       ↓
morphdom diffs old chart vs new chart, only changed bars animate
```

This loop can repeat indefinitely. The widget and the chat are one coherent, stateful system.

---

## Part 10: Server-Sent Events — The Plumbing

All of the real-time streaming from server to browser happens over SSE (Server-Sent Events). This is simpler than WebSockets — it's a one-way stream over a regular HTTP connection.

The server yields SSE events using a dead-simple helper:

```python
def sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
```

Each event is a JSON object with a `type` field. Here's the complete event vocabulary:

| Event type | When | Browser action |
|---|---|---|
| `text` | Claude prose token arrives | Append to assistant chat bubble |
| `status` | Tool call in progress | Show italic dashed status bubble |
| `widget_delta` | Partial HTML from `show_widget` | `scheduleRender` (debounced morphdom) |
| `widget_final` | Tool call complete | `renderWidget` + `runScripts` |
| `error` | Exception thrown | Show error bubble |
| `done` | Stream finished | Push assistant text to history |

The browser reads this stream using the Fetch API with a `ReadableStream` reader — not the `EventSource` API. This matters because `EventSource` doesn't support POST requests (it only does GET), and you need to send the conversation history as a POST body.

The raw stream reading logic in `static/index.html`:

```javascript
const reader = resp.body.getReader();
const decoder = new TextDecoder();
let buf = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buf += decoder.decode(value, { stream: true });
  const parts = buf.split('\n\n');
  buf = parts.pop(); // keep incomplete chunk

  for (const part of parts) {
    if (!part.startsWith('data: ')) continue;
    let ev;
    try { ev = JSON.parse(part.slice(6)); } catch { continue; }
    // ... handle ev.type
  }
}
```

The `buf = parts.pop()` line is critical — it handles the case where a chunk boundary falls in the middle of an SSE event. The last incomplete part is saved and prepended to the next chunk.

---

## Part 11: The Multi-Turn Tool Loop

One subtlety that's easy to miss: the server doesn't just make one request to Claude. It runs in a loop.

The `while True` loop in `server.py`:

```python
while True:
    # Stream from Claude
    async with client.messages.stream(...) as stream:
        async for event in stream:
            # ... handle events, yield SSE events to browser

    final_msg = await stream.get_final_message()

    # If Claude stopped naturally (no tool use), we're done
    if final_msg.stop_reason != "tool_use":
        yield sse({"type": "done"})
        break

    # If Claude used tools, process them and loop back
    messages.append({"role": "assistant", "content": assistant_content})
    tool_results = []

    for block in final_msg.content:
        if block.name == "load_guidelines":
            content = get_guidelines(block.input["modules"])
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content,
            })

        elif block.name == "show_widget":
            html = block.input.get("widget_code", "")
            yield sse({"type": "widget_final", "html": html})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": f"Widget '{title}' rendered successfully.",
            })

    messages.append({"role": "user", "content": tool_results})
    # Loop → Claude sees tool results and continues
```

Here's the sequence for a typical widget request:

**Turn 1:** Claude streams prose ("Here's your calculator...") and calls `load_guidelines(["interactive"])`. The server processes the tool call, loads the markdown files, returns them as a tool result, and loops.

**Turn 2:** Claude now has the guidelines in context. It streams the rest of its prose and calls `show_widget(widget_code="...")`. The server streams `widget_delta` events during this call, then emits `widget_final`, returns a success message as the tool result, and loops.

**Turn 3:** Claude sees "Widget rendered successfully" and decides it has nothing more to do. `stop_reason` is not `tool_use`, so the server emits `{"type": "done"}` and breaks the loop.

The browser sees all of this as a single continuous stream. It doesn't know there were 3 Claude API calls. From the browser's perspective, text arrived, a status appeared, a widget grew in real time, and the experience completed.

---

## Part 12: Everything Together — A Complete Request Walk-Through

Let's trace a single request from keystroke to rendered widget, step by step.

**User types:** "Give me a compound interest calculator"

**Step 1.** Browser pushes `{role: "user", content: "Give me a compound interest calculator"}` into `history`, calls `doSend()`.

**Step 2.** `fetch('/chat', {method: 'POST', body: JSON.stringify({messages: history})})` fires. The browser starts reading the response body as a stream.

**Step 3.** Server receives request. Builds `messages` list. Enters the `while True` loop. Calls `client.messages.stream(model="claude-opus-4-6", ...)`.

**Step 4.** Claude starts streaming. First, it emits text tokens: "Here's a compound interest calculator that lets you adjust..." — these come in as `text_delta` events. Server yields `{"type": "text", "text": "Here's..."}` etc. Browser appends text to the assistant bubble character by character.

**Step 5.** Claude decides to call `load_guidelines`. Server sees `content_block_start` with `type=tool_use`, registers `active_tool_calls[0] = {name: "load_guidelines", ...}`. Tool JSON streams in. No HTML preview sent (this isn't `show_widget`).

**Step 6.** Stream ends with `stop_reason = "tool_use"`. Server reads guidelines markdown files. Yields `{"type": "status", "text": "Loading interactive guidelines..."}`. Browser shows italic status bubble: "Loading interactive guidelines..."

**Step 7.** Server appends assistant content and tool result to `messages`. Loops back to the top of `while True`. Calls Claude again with the guidelines now in context.

**Step 8.** Claude streams more prose. Also starts building the `show_widget` tool call. Its `widget_code` argument begins streaming as JSON fragments.

**Step 9.** On every `input_json_delta` event for the `show_widget` call, server calls `extract_widget_code(tc["partial_json"])`. After the first 30+ characters of HTML are recovered, server starts yielding `{"type": "widget_delta", "html": "<style>\n.calc { background:..."}`. Browser calls `scheduleRender()`, morphdom fires, the widget panel starts showing a partial gray box.

**Step 10.** 200ms later, more HTML has streamed in. `widget_delta` with more complete HTML. Morphdom diffs: the box now has labels. The new nodes fade in. The old box stays stable.

**Step 11.** 800ms later, the entire widget is streamed. `stop_reason = "tool_use"`. Server yields `{"type": "widget_final", "html": "...(complete HTML)...", "title": "compound interest calculator"}`. Browser cancels any pending debounce, calls `renderWidget(finalHTML)`, then `runScripts()`. The calculator's JavaScript initializes, event listeners attach, the first calculation runs, the result displays.

**Step 12.** Server appends "Widget rendered successfully" tool result. Loops. Claude sees it, has nothing more to do. `stop_reason != "tool_use"`. Server yields `{"type": "done"}`. Browser pushes Claude's prose into `history`. Stream ends.

Total time: 3–5 seconds. The widget appears and grows during that entire time, not just at the end.

---

## Summary: The Full Comparison

| Concern | Naive "Claude returns HTML" | Generative UI |
|---|---|---|
| **Separation of prose vs. artifact** | String parsing, fragile | Protocol-level via tool call channels |
| **When widget appears** | After full response (~8s) | After ~30 chars of HTML (~1–2s) |
| **Rendering during stream** | Full `innerHTML` replace | Morphdom diff, only changed nodes |
| **Script execution** | Silently broken | Node replacement after `widget_final` |
| **Theming** | Claude guesses hex values | Shared CSS variables, automatic |
| **Design knowledge** | Claude improvises | On-demand guideline injection |
| **Widget → AI feedback** | None (one-shot) | `window.sendToAgent()` → new Claude turn |
| **Conversation memory** | Lost after render | Full history preserved across interactions |
| **Streaming feel** | Binary: nothing → everything | Progressive: widget grows in real time |

---

## Conclusion

The phrase "generative UI" could easily sound like marketing — as if it just means "AI writes HTML". But as this codebase shows, the architecture required to do it *well* involves a precise set of interlocking mechanisms:

- **Structured tool calls** to separate prose from visual artifacts at the protocol level
- **Partial JSON parsing** for live widget preview during streaming
- **Morphdom** for progressive DOM rendering without flicker
- **Script node replacement** for safe JavaScript execution
- **Shared CSS variables** for automatic design system inheritance
- **Lazy guideline injection** for token efficiency
- **`window.sendToAgent()`** for a stateful, bidirectional interaction loop

Remove any one of these pieces and the experience degrades noticeably. Remove the partial JSON parser and the widget only appears after Claude finishes writing it. Remove morphdom and the widget flickers on every streaming update. Remove CSS variables and every widget looks like a different app. Remove `sendToAgent` and the widgets are dead static screenshots.

The genius of this ~800-line codebase is that it makes all of these mechanisms invisible to Claude. Claude doesn't know about morphdom. It doesn't know about SSE. It doesn't know about `runScripts()`. It just writes an HTML fragment into a tool argument, following a handful of rules it was told to follow. The entire infrastructure — the partial JSON parser, the debounced renderer, the script executor, the shared design system — operates silently beneath it.

That's the engineering challenge of generative UI: building infrastructure that's sophisticated enough to handle everything the browser needs, but invisible enough that the model can write simple HTML and have it *just work*.
