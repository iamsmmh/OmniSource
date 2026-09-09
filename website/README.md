# Website

The OmniSource website is a dependency-free static application.

```text
website/
├── index.html       # Semantic page structure
├── css/styles.css   # Responsive visual system
└── js/app.js        # Catalog, search, filters, dialogs, and preferences
```

The interface reads `apps.json` and `feeds/health.json` at runtime. These generated files and the shared `assets/` directory are added by `scripts/build_site.py` rather than duplicated here.

From the repository root:

```bash
make site   # assemble _site/
make serve  # preview on port 8000
```

Keep the website dependency-free so GitHub Pages remains fast, portable, and simple to maintain.
