<div align="center">

  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 240" width="100%" height="100%">
    <defs>
      <linearGradient id="grad-bg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#0f172a" />
        <stop offset="50%" stop-color="#1e1b4b" />
        <stop offset="100%" stop-color="#0f172a" />
      </linearGradient>
      <linearGradient id="grad-icon" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#38bdf8" />
        <stop offset="50%" stop-color="#818cf8" />
        <stop offset="100%" stop-color="#c084fc" />
      </linearGradient>
      <linearGradient id="grad-text" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#ffffff" />
        <stop offset="100%" stop-color="#cbd5e1" />
      </linearGradient>
      <linearGradient id="grad-accent" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#38bdf8" />
        <stop offset="100%" stop-color="#c084fc" />
      </linearGradient>
      <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="6" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
      </filter>
      <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
        <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000000" flood-opacity="0.5"/>
      </filter>
    </defs>
    <rect x="10" y="10" width="780" height="220" rx="24" fill="url(#grad-bg)" stroke="#334155" stroke-width="2" filter="url(#shadow)"/>
    <g transform="translate(45, 30)">
      <circle cx="80" cy="80" r="64" fill="none" stroke="url(#grad-icon)" stroke-width="4" stroke-dasharray="12 8" opacity="0.4"/>
      <circle cx="80" cy="80" r="28" fill="url(#grad-icon)" filter="url(#glow)"/>
      <path d="M 80,24 A 56,56 0 1,1 24,80" fill="none" stroke="url(#grad-icon)" stroke-width="8" stroke-linecap="round"/>
      <path d="M 80,136 A 56,56 0 1,1 136,80" fill="none" stroke="url(#grad-icon)" stroke-width="8" stroke-linecap="round"/>
      <circle cx="80" cy="24" r="7" fill="#ffffff" filter="url(#glow)"/>
      <circle cx="136" cy="80" r="7" fill="#ffffff" filter="url(#glow)"/>
      <circle cx="24" cy="80" r="7" fill="#ffffff" filter="url(#glow)"/>
      <path d="M 82,64 L 70,82 H 82 L 78,96 L 90,78 H 78 Z" fill="#0f172a"/>
    </g>
    <text x="245" y="115" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-weight="900" font-size="54" letter-spacing="-1" fill="url(#grad-text)">
      Omni<tspan fill="url(#grad-accent)">Source</tspan>
    </text>
    <rect x="245" y="138" width="460" height="32" rx="8" fill="#1e293b" stroke="#475569" stroke-width="1"/>
    <text x="257" y="159" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-weight="600" font-size="14" fill="#94a3b8" letter-spacing="1.5">
      AUTOMATED ALTSTORE &amp; SIDELOAD REPOSITORY
    </text>
  </svg>

  <br>

  <p align="center">
    <strong>The next-generation, automated repository engine for iOS sideloading & Android mods.</strong><br>
    Delivering pre-patched IPAs, customized YouTube mods, and system extensions—updated automatically via GitHub Actions.
  </p>

  <p align="center">
    <a href="https://altstore.io"><img src="https://img.shields.io/badge/AltStore-Compatible-00C9A7?style=for-the-badge&logo=altstore&logoColor=white" alt="AltStore"></a>
    <a href="https://sidestore.io"><img src="https://img.shields.io/badge/SideStore-Compatible-845EC2?style=for-the-badge&logo=iOS&logoColor=white" alt="SideStore"></a>
    <a href="https://github.com"><img src="https://img.shields.io/badge/GitHub_Actions-Automated-D65DB1?style=for-the-badge&logo=githubactions&logoColor=white" alt="GitHub Actions"></a>
    <a href="https://github.com"><img src="https://img.shields.io/badge/Maintained%3F-Yes-FF6F91?style=for-the-badge" alt="Maintained"></a>
  </p>

</div>

---

## ⚡ Quick Add to Sideload Manager

Tap the quick-add link or paste the raw source manifest URL directly into **AltStore**, **SideStore**, or **TrollStore**:

```text
[https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json](https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json)
