/**
 * OmniSource website.
 *
 * Zero dependencies, zero build step. Everything on screen is derived from the
 * same generated artefacts the sideloading clients consume:
 *   apps.json    - the master AltStore feed (includes the `omnisource` block)
 *   feeds/health.json - link-health snapshot written by scripts/omnisource.py
 * Adding an app to catalog.json therefore updates the site with no code change.
 */

const BASE = new URL(".", location.href).href.replace(/\/$/, "");
const CLIENTS = [
  { id: "altstore", name: "AltStore", icon: "AltStore.png", url: "https://altstore.io" },
  { id: "sidestore", name: "SideStore", icon: "SideStore.png", url: "https://sidestore.io" },
  { id: "feather", name: "Feather", icon: "Feather.png", url: "https://github.com/khcrysalis/Feather" },
  { id: "esign", name: "ESign", icon: "E-Sign.png", url: "https://github.com/esigncert/esign" },
  { id: "livecontainer", name: "LiveContainer", icon: "LiveContainer.png", url: "https://github.com/khanhduytran0/LiveContainer" },
];
const STATUS = {
  stable: ["ok", "Stable"],
  beta: ["warn", "Beta"],
  manual: ["accent", "Manual"],
  unmaintained: ["bad", "Unmaintained"],
  deprecated: ["bad", "Deprecated"],
};

const view = document.getElementById("view");
let feed = null;
let health = null;

/* ---------------------------------------------------------------- helpers */
const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const mb = (bytes) => (bytes ? `${(bytes / 1048576).toFixed(1)} MB` : "—");

const slugOf = (app) => app.omnisource?.slug ?? app.name.toLowerCase().replace(/\W+/g, "-");

const statusPill = (status) => {
  const [tone, label] = STATUS[status] ?? ["", status ?? "unknown"];
  return `<span class="pill ${tone}">${esc(label)}</span>`;
};

const healthPill = (app) =>
  app.omnisource?.health?.downloadReachable === false
    ? `<span class="pill bad" title="${esc(app.omnisource.health.detail)}">Link down</span>`
    : `<span class="pill ok">Online</span>`;

function toast(message) {
  let node = document.querySelector(".toast");
  if (!node) {
    node = document.createElement("div");
    node.className = "toast";
    document.body.append(node);
  }
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(node._timer);
  node._timer = setTimeout(() => node.classList.remove("show"), 1900);
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast("Copied to clipboard");
  } catch {
    toast(text);
  }
}

/** Deep-link URLs understood by each client for one-tap subscription. */
function subscribeLinks(feedURL) {
  const bare = feedURL.replace(/^https?:\/\//, "");
  return [
    ["AltStore", `altstore://source?url=${encodeURIComponent(feedURL)}`],
    ["SideStore", `sidestore://source?url=${encodeURIComponent(feedURL)}`],
    ["Feather", `feather://source/${bare}`],
  ];
}

function appCard(app) {
  const slug = slugOf(app);
  return `
    <article class="card">
      <img src="${esc(app.iconURL)}" alt="" loading="lazy" width="54" height="54">
      <div class="card-body">
        <h3><a href="#/app/${esc(slug)}">${esc(app.name)}</a></h3>
        <p class="sub">${esc(app.subtitle || app.developerName)}</p>
        <div class="meta">
          <span class="pill">v${esc(app.version)}</span>
          ${statusPill(app.omnisource?.status)}
          ${healthPill(app)}
          ${app.omnisource?.featured ? '<span class="pill accent">Featured</span>' : ""}
        </div>
      </div>
    </article>`;
}

/* ------------------------------------------------------------------ views */
function renderHome() {
  const apps = feed.apps;
  const featured = apps.filter((a) => a.omnisource?.featured);
  const totals = health?.totals ?? { apps: apps.length, reachable: apps.length };
  const newest = [...apps].sort((a, b) => String(b.versionDate).localeCompare(String(a.versionDate))).slice(0, 4);

  return `
    <section class="hero">
      <h1>A curated iOS application repository</h1>
      <p class="lede">
        OmniSource tracks upstream releases automatically, verifies every download link,
        and publishes one AltStore-compatible feed for AltStore, SideStore, Feather, ESign and LiveContainer.
      </p>
      <div class="subscribe">
        <code id="feed-url">${esc(BASE)}/apps.json</code>
        <button class="btn" data-copy="${esc(BASE)}/apps.json">Copy feed URL</button>
        ${subscribeLinks(`${BASE}/apps.json`)
          .map(([name, href]) => `<a class="btn secondary" href="${esc(href)}">Add to ${esc(name)}</a>`)
          .join("")}
      </div>
      <div class="stats">
        <div class="stat"><b>${totals.apps}</b><span>Apps</span></div>
        <div class="stat"><b>${totals.reachable}/${totals.apps}</b><span>Links online</span></div>
        <div class="stat"><b>${featured.length}</b><span>Featured</span></div>
        <div class="stat"><b>${esc(health?.generatedAt ?? "—")}</b><span>Last change</span></div>
      </div>
    </section>

    <h2>Featured</h2>
    <div class="grid">${featured.map(appCard).join("")}</div>

    <h2>Recently updated</h2>
    <div class="grid">${newest.map(appCard).join("")}</div>

    <h2>Supported clients</h2>
    <div class="grid">
      ${CLIENTS.map(
        (c) => `<article class="card">
          <img src="./assets/${esc(c.icon)}" alt="" loading="lazy" width="54" height="54">
          <div class="card-body">
            <h3><a href="${esc(c.url)}">${esc(c.name)}</a></h3>
            <p class="sub">${feed.apps.filter((a) => (a.omnisource?.compatibility?.clients ?? []).includes(c.id)).length} compatible apps</p>
            <div class="meta"><a class="pill accent" href="#/install">Installation guide</a></div>
          </div>
        </article>`
      ).join("")}
    </div>`;
}

function renderCatalog() {
  const categories = [...new Set(feed.apps.map((a) => a.category).filter(Boolean))].sort();
  return `
    <h1>Catalog</h1>
    <p class="muted">${feed.apps.length} apps. Every entry is rebuilt from upstream releases every six hours.</p>
    <div class="filters">
      <input type="search" id="q" placeholder="Search apps, developers, bundle IDs…" autocomplete="off">
      <select id="f-category"><option value="">All categories</option>${categories
        .map((c) => `<option value="${esc(c)}">${esc(c)}</option>`)
        .join("")}</select>
      <select id="f-status"><option value="">Any status</option>${Object.keys(STATUS)
        .map((s) => `<option value="${esc(s)}">${esc(STATUS[s][1])}</option>`)
        .join("")}</select>
      <select id="f-client"><option value="">Any client</option>${CLIENTS.map(
        (c) => `<option value="${esc(c.id)}">${esc(c.name)}</option>`
      ).join("")}</select>
    </div>
    <div class="grid" id="results"></div>`;
}

function wireCatalog() {
  const q = document.getElementById("q");
  const category = document.getElementById("f-category");
  const status = document.getElementById("f-status");
  const client = document.getElementById("f-client");
  const results = document.getElementById("results");

  const apply = () => {
    const term = q.value.trim().toLowerCase();
    const list = feed.apps.filter((app) => {
      const haystack = `${app.name} ${app.developerName} ${app.bundleIdentifier} ${app.subtitle}`.toLowerCase();
      if (term && !haystack.includes(term)) return false;
      if (category.value && app.category !== category.value) return false;
      if (status.value && app.omnisource?.status !== status.value) return false;
      if (client.value && !(app.omnisource?.compatibility?.clients ?? []).includes(client.value)) return false;
      return true;
    });
    results.innerHTML = list.length
      ? list.map(appCard).join("")
      : `<p class="muted">No app matches those filters.</p>`;
  };

  [q, category, status, client].forEach((el) => el.addEventListener("input", apply));
  apply();
}

function renderApp(slug) {
  const app = feed.apps.find((a) => slugOf(a) === slug);
  if (!app) return `<h1>Unknown app</h1><p><a href="#/catalog">Back to the catalog</a></p>`;

  const meta = app.omnisource ?? {};
  const compat = meta.compatibility ?? {};
  const verification = meta.verification ?? {};
  const feedURL = `${BASE}/${slug}.json`;

  return `
    <div class="app-head">
      <img src="${esc(app.iconURL)}" alt="" width="84" height="84">
      <div style="flex:1 1 320px">
        <h1 style="margin-bottom:4px">${esc(app.name)}</h1>
        <p class="muted" style="margin-bottom:8px">${esc(app.subtitle || "")} · by ${esc(app.developerName)}</p>
        <div class="meta">
          <span class="pill">v${esc(app.version)}</span>
          <span class="pill">${esc(app.versionDate)}</span>
          <span class="pill">${mb(app.size)}</span>
          ${statusPill(meta.status)} ${healthPill(app)}
        </div>
      </div>
    </div>

    <div class="subscribe">
      <code>${esc(feedURL)}</code>
      <button class="btn" data-copy="${esc(feedURL)}">Copy feed URL</button>
      <a class="btn secondary" href="${esc(app.downloadURL)}">Download IPA</a>
      ${(app.fallbackDownloadURLs ?? [])
        .map((u, i) => `<a class="btn secondary" href="${esc(u)}">Mirror ${i + 1}</a>`)
        .join("")}
      ${meta.upstreamURL ? `<a class="btn secondary" href="${esc(meta.upstreamURL)}">Upstream project</a>` : ""}
    </div>

    <p>${esc(app.localizedDescription).slice(0, 900)}</p>

    <div class="detail-grid">
      <div class="panel">
        <h3>Compatibility</h3>
        <dl class="kv">
          <dt>Minimum iOS</dt><dd>${esc(compat.minOSVersion ?? "—")}</dd>
          <dt>Maximum iOS</dt><dd>${esc(compat.maxOSVersion ?? "No limit")}</dd>
          <dt>Devices</dt><dd>${esc((compat.devices ?? []).join(", ") || "—")}</dd>
          <dt>Bundle ID</dt><dd><code>${esc(app.bundleIdentifier)}</code></dd>
        </dl>
        <p class="muted" style="margin:10px 0 0;font-size:.86rem">${esc(compat.notes ?? "")}</p>
      </div>
      <div class="panel">
        <h3>Verification</h3>
        <dl class="kv">
          <dt>Method</dt><dd>${esc(verification.method ?? "—")}</dd>
          <dt>Publisher</dt><dd>${esc(verification.publisher ?? "—")}</dd>
          <dt>Checksum published</dt><dd>${verification.checksumPublished ? "Yes" : "No"}</dd>
          <dt>Pre-signed</dt><dd>${verification.codeSigned ? "Yes" : "No — sign on device"}</dd>
        </dl>
      </div>
      <div class="panel">
        <h3>Clients</h3>
        <div class="meta">
          ${CLIENTS.map((c) =>
            (compat.clients ?? []).includes(c.id)
              ? `<span class="pill ok">${esc(c.name)}</span>`
              : `<span class="pill">${esc(c.name)}: untested</span>`
          ).join("")}
        </div>
        <p class="muted" style="margin:10px 0 0;font-size:.86rem">
          Link ${meta.health?.downloadReachable === false ? "failed" : "verified"} since ${esc(meta.health?.statusSince ?? "—")}.
        </p>
      </div>
    </div>

    <h2>Changelog</h2>
    ${app.versions
      .map(
        (v, index) => `
      <details class="version" ${index === 0 ? "open" : ""}>
        <summary>v${esc(v.version)} — ${esc(v.date)} · ${mb(v.size)} · iOS ${esc(v.minOSVersion ?? "—")}+</summary>
        <div class="changelog">${esc(v.localizedDescription)}</div>
      </details>`
      )
      .join("")}

    <p style="margin-top:20px"><a href="#/catalog">← Back to the catalog</a></p>`;
}

function renderCompare() {
  const options = feed.apps
    .map((a) => `<option value="${esc(slugOf(a))}">${esc(a.name)}</option>`)
    .join("");
  return `
    <h1>Compare apps</h1>
    <p class="muted">Pick up to three builds to compare version, size, compatibility and verification side by side.</p>
    <div class="compare-picker">
      ${[0, 1, 2]
        .map(
          (i) =>
            `<select data-compare="${i}"><option value="">Select an app…</option>${options}</select>`
        )
        .join("")}
    </div>
    <div id="compare-out"></div>`;
}

function wireCompare() {
  const selects = [...document.querySelectorAll("[data-compare]")];
  const out = document.getElementById("compare-out");
  const rows = [
    ["Version", (a) => `v${a.version}`],
    ["Updated", (a) => a.versionDate],
    ["Size", (a) => mb(a.size)],
    ["Developer", (a) => a.developerName],
    ["Bundle ID", (a) => a.bundleIdentifier],
    ["Category", (a) => a.category ?? "—"],
    ["Status", (a) => STATUS[a.omnisource?.status]?.[1] ?? "—"],
    ["Minimum iOS", (a) => a.omnisource?.compatibility?.minOSVersion ?? "—"],
    ["Verification", (a) => a.omnisource?.verification?.method ?? "—"],
    ["Publisher", (a) => a.omnisource?.verification?.publisher ?? "—"],
    ["Link health", (a) => (a.omnisource?.health?.downloadReachable === false ? "Down" : "Online")],
    ["Versions kept", (a) => a.versions.length],
  ];

  const apply = () => {
    const chosen = selects
      .map((s) => feed.apps.find((a) => slugOf(a) === s.value))
      .filter(Boolean);
    if (chosen.length < 2) {
      out.innerHTML = `<p class="muted">Select at least two apps.</p>`;
      return;
    }
    out.innerHTML = `<div class="table-scroll"><table>
      <thead><tr><th></th>${chosen.map((a) => `<th>${esc(a.name)}</th>`).join("")}</tr></thead>
      <tbody>${rows
        .map(
          ([label, fn]) =>
            `<tr><th scope="row">${esc(label)}</th>${chosen
              .map((a) => `<td>${esc(fn(a))}</td>`)
              .join("")}</tr>`
        )
        .join("")}</tbody></table></div>`;
  };

  selects.forEach((s) => s.addEventListener("change", apply));
  selects[0].value = slugOf(feed.apps[0]);
  selects[1].value = slugOf(feed.apps[1] ?? feed.apps[0]);
  apply();
}

function renderCompatibility() {
  return `
    <h1>Compatibility matrix</h1>
    <p class="muted">
      Client support is declared per app in <code>catalog.json</code>. “Untested” means nobody has confirmed
      it yet — <a href="https://github.com/iamsmmh/OmniSource/issues/new">report a result</a> and it moves.
    </p>
    <div class="table-scroll"><table>
      <thead><tr><th>App</th><th>Min iOS</th>${CLIENTS.map((c) => `<th class="center">${esc(c.name)}</th>`).join("")}</tr></thead>
      <tbody>
        ${feed.apps
          .map((app) => {
            const clients = app.omnisource?.compatibility?.clients ?? [];
            return `<tr>
              <td><a href="#/app/${esc(slugOf(app))}">${esc(app.name)}</a></td>
              <td>${esc(app.omnisource?.compatibility?.minOSVersion ?? "—")}</td>
              ${CLIENTS.map((c) => `<td class="center">${clients.includes(c.id) ? "✅" : "·"}</td>`).join("")}
            </tr>`;
          })
          .join("")}
      </tbody>
    </table></div>`;
}

function renderHealth() {
  const items = health?.apps ?? [];
  const totals = health?.totals ?? {};
  return `
    <h1>Health dashboard</h1>
    <p class="muted">
      Every scheduled run probes each download URL without downloading the payload and records the result.
      Snapshot taken at the last catalogue change: ${esc(health?.generatedAt ?? "—")}.
    </p>
    <div class="stats">
      <div class="stat"><b>${totals.apps ?? 0}</b><span>Tracked</span></div>
      <div class="stat"><b>${totals.reachable ?? 0}</b><span>Reachable</span></div>
      <div class="stat"><b>${totals.unreachable ?? 0}</b><span>Failing</span></div>
      <div class="stat"><b>${totals.featured ?? 0}</b><span>Featured</span></div>
    </div>
    <div class="table-scroll"><table>
      <thead><tr><th>App</th><th>Version</th><th>Updated</th><th>Size</th><th>Status</th><th>Download</th><th>Since</th></tr></thead>
      <tbody>${items
        .map(
          (item) => `<tr>
            <td><a href="#/app/${esc(item.slug)}">${esc(item.name)}</a></td>
            <td><code>${esc(item.version)}</code></td>
            <td>${esc(item.updatedAt)}</td>
            <td>${mb(item.sizeBytes)}</td>
            <td>${statusPill(item.status)}</td>
            <td>${item.downloadReachable ? '<span class="pill ok">Online</span>' : `<span class="pill bad" title="${esc(item.detail)}">Down</span>`}</td>
            <td class="muted">${esc(item.statusSince ?? "—")}</td>
          </tr>`
        )
        .join("")}</tbody>
    </table></div>`;
}

function renderInstall() {
  const url = `${BASE}/apps.json`;
  const steps = {
    AltStore: [
      "Install AltStore on your device with AltServer on a Mac or PC.",
      "Open AltStore and go to <strong>Browse → Sources</strong>.",
      "Tap <strong>+</strong> and paste the OmniSource feed URL.",
      "Pick an app and tap <strong>FREE</strong> to install it.",
    ],
    SideStore: [
      "Pair SideStore with your device and make sure your anisette server is reachable.",
      "Open <strong>Browse → Sources → Add Source</strong>.",
      "Paste the OmniSource feed URL and confirm.",
      "Install any app; SideStore refreshes it in the background.",
    ],
    Feather: [
      "Open Feather and go to <strong>Sources</strong>.",
      "Tap <strong>+</strong> and paste the OmniSource feed URL.",
      "Select an app, then <strong>Sign and Install</strong> with your certificate.",
    ],
    ESign: [
      "Open ESign and go to <strong>Sources → Add</strong>.",
      "Paste the OmniSource feed URL.",
      "Download the IPA, then sign it with your certificate and install.",
    ],
    LiveContainer: [
      "Download the IPA from the app page, or add the feed in your store client.",
      "In LiveContainer, tap <strong>+</strong> and choose the IPA.",
      "Launch the app inside LiveContainer — no extra app slot is used.",
    ],
  };

  return `
    <h1>Installation</h1>
    <div class="subscribe">
      <code>${esc(url)}</code>
      <button class="btn" data-copy="${esc(url)}">Copy feed URL</button>
      ${subscribeLinks(url).map(([n, h]) => `<a class="btn secondary" href="${esc(h)}">Add to ${esc(n)}</a>`).join("")}
    </div>
    ${Object.entries(steps)
      .map(
        ([client, list]) => `<section class="guide">
          <h2 style="margin-top:0">${esc(client)}</h2>
          <ol>${list.map((s) => `<li>${s}</li>`).join("")}</ol>
        </section>`
      )
      .join("")}
    <section class="guide">
      <h2 style="margin-top:0">Individual feeds</h2>
      <p class="muted">Prefer to subscribe to a single app? Every app publishes its own feed.</p>
      <div class="table-scroll"><table>
        <thead><tr><th>App</th><th>Feed URL</th><th></th></tr></thead>
        <tbody>${feed.apps
          .map((app) => {
            const single = `${BASE}/${slugOf(app)}.json`;
            return `<tr><td>${esc(app.name)}</td><td><code>${esc(single)}</code></td>
              <td><button class="ghost" data-copy="${esc(single)}">Copy</button></td></tr>`;
          })
          .join("")}</tbody>
      </table></div>
    </section>`;
}

/* ----------------------------------------------------------------- router */
const ROUTES = [
  [/^\/?$/, renderHome, null, ""],
  [/^\/catalog$/, renderCatalog, wireCatalog, "catalog"],
  [/^\/app\/([\w-]+)$/, renderApp, null, "catalog"],
  [/^\/compare$/, renderCompare, wireCompare, "compare"],
  [/^\/compatibility$/, renderCompatibility, null, "compatibility"],
  [/^\/health$/, renderHealth, null, "health"],
  [/^\/install$/, renderInstall, null, "install"],
];

function route() {
  const path = location.hash.replace(/^#/, "") || "/";
  for (const [pattern, render, wire, nav] of ROUTES) {
    const match = path.match(pattern);
    if (!match) continue;
    view.innerHTML = render(...match.slice(1));
    document.querySelectorAll("[data-nav]").forEach((a) =>
      a.toggleAttribute("aria-current", a.dataset.nav === nav)
    );
    if (wire) wire();
    window.scrollTo(0, 0);
    return;
  }
  view.innerHTML = `<h1>Page not found</h1><p><a href="#/">Go home</a></p>`;
}

/* ------------------------------------------------------------------- boot */
document.addEventListener("click", (event) => {
  const target = event.target.closest("[data-copy]");
  if (target) {
    event.preventDefault();
    copy(target.dataset.copy);
  }
});

const themeToggle = document.getElementById("theme-toggle");
const storedTheme = localStorage.getItem("omnisource-theme");
if (storedTheme) document.documentElement.dataset.theme = storedTheme;
themeToggle.addEventListener("click", () => {
  const dark = document.documentElement.dataset.theme === "dark";
  const next = dark ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("omnisource-theme", next);
});

async function boot() {
  try {
    const [feedResponse, healthResponse] = await Promise.all([
      fetch("./apps.json", { cache: "no-cache" }),
      fetch("./feeds/health.json", { cache: "no-cache" }).catch(() => null),
    ]);
    if (!feedResponse.ok) throw new Error(`apps.json returned ${feedResponse.status}`);
    feed = await feedResponse.json();
    health = healthResponse && healthResponse.ok ? await healthResponse.json() : null;
  } catch (error) {
    view.innerHTML = `<h1>Could not load the catalog</h1>
      <p class="muted">${esc(error.message)}</p>
      <p>The raw feed is still available at <a href="./apps.json">apps.json</a>.</p>`;
    return;
  }
  addEventListener("hashchange", route);
  route();
}

boot();
