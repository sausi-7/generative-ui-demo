TOOLS = [
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
    },
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
                "i_have_seen_guidelines": {
                    "type": "boolean",
                    "description": "Set to true after calling load_guidelines."
                },
                "title": {
                    "type": "string",
                    "description": "Short snake_case name for this widget (e.g. 'compound_interest_calculator')."
                },
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
]
