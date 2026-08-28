<div align="center">

<!-- OmniSource Custom Animated/Modern Logo -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 240" width="100%" max-width="650" style="background: transparent;">
  <defs>
    <!-- Background / Symbol Gradients -->
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

    <!-- Drop Shadows & Glow Effects -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000000" flood-opacity="0.5"/>
    </filter>
  </defs>

  <!-- Container Box -->
  <rect x="10" y="10" width="780" height="220" rx="24" fill="url(#grad-bg)" stroke="#334155" stroke-width="2" filter="url(#shadow)"/>

  <!-- Logo Mark (Connected Infinite Orbit / Node Symbol) -->
  <g transform="translate(45, 30)">
    <!-- Outer Glow Ring -->
    <circle cx="80" cy="80" r="64" fill="none" stroke="url(#grad-icon)" stroke-width="4" stroke-dasharray="12 8" opacity="0.4"/>
    
    <!-- Central Node Core -->
    <circle cx="80" cy="80" r="28" fill="url(#grad-icon)" filter="url(#glow)"/>
    
    <!-- Dynamic Orbiting App Nodes -->
    <path d="M 80,24 A 56,56 0 1,1 24,80" fill="none" stroke="url(#grad-icon)" stroke-width="8" stroke-linecap="round"/>
    <path d="M 80,136 A 56,56 0 1,1 136,80" fill="none" stroke="url(#grad-icon)" stroke-width="8" stroke-linecap="round"/>

    <!-- Orbital Satellites (Representing Repos/IPAs) -->
    <circle cx="80" cy="24" r="7" fill="#ffffff" filter="url(#glow)"/>
    <circle cx="136" cy="80" r="7" fill="#ffffff" filter="url(#glow)"/>
    <circle cx="24" cy="80" r="7" fill="#ffffff" filter="url(#glow)"/>

    <!-- Center Lightning / Arrow Bolt (Instant Sync Symbol) -->
    <path d="M 82,64 L 70,82 H 82 L 78,96 L 90,78 H 78 Z" fill="#0f172a"/>
  </g>

  <!-- Brand Typography -->
  <!-- Main Title -->
  <text x="245" y="115" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-weight="900" font-size="54" letter-spacing="-1" fill="url(#grad-text)">
    Omni<tspan fill="url(#grad-accent)">Source</tspan>
  </text>
  
  <!-- Subtitle Badge -->
  <rect x="245" y="138" width="460" height="32" rx="8" fill="#1e293b" stroke="#475569" stroke-width="1"/>
  <text x="257" y="159" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-weight="600" font-size="14" fill="#94a3b8" letter-spacing="1.5">
    AUTOMATED ALTSTORE &amp; SIDELOAD REPOSITORY
  </text>
</svg>

<br/>

[![GitHub Stars](https://img.shields.io/github/stars/iamsmmh/OmniSource?style=for-the-badge&logo=github&color=38bdf8)](https://github.com/iamsmmh/OmniSource/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/iamsmmh/OmniSource?style=for-the-badge&logo=github&color=818cf8)](https://github.com/iamsmmh/OmniSource/network/members)
[![License](https://img.shields.io/github/license/iamsmmh/OmniSource?style=for-the-badge&logo=open-source-initiative&color=c084fc)](LICENSE)
[![Auto-Sync Status](https://img.shields.io/github/actions/workflow/status/iamsmmh/OmniSource/check-updates.yml?branch=main&style=for-the-badge&logo=github-actions&label=AUTO%20SYNC)](https://github.com/iamsmmh/OmniSource/actions)

*The ultimate self-updating **AltStore**, **SideStore**, **ESign**, **Feather**, and **LiveContainer** source for pre-built iOS tweaks.*  
*No manual compiling, no extra forks, no hunting for decrypted IPAs!* ⚡

---

</div>

## 📲 How to Add This Source

1. **Open** your preferred sideloader (**AltStore**, **SideStore**, **ESign**, **Feather**, or **LiveContainer**).
2. **Navigate** to your **Sources** / **Repos** section.
3. **Tap `+`** and paste any of the raw source URLs listed below:

---

### 📺 YouTube Tweaks

| App / Tweak | Description | Source URL |
| :--- | :--- | :--- |
| **YTLite** | Lightweight YouTube experience | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytlite.json` |
| **YTKillerPlus** | Feature-packed premium YouTube suite | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkp.json` |
| **YouPro** | Streamlined YouTube enhancement | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youpro.json` |
| **YouMod** | Essential YouTube modifications | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youmod.json` |
| **YTKACE** | Custom feature-rich YouTube client | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkace.json` |

---

### 🎵 Music Apps

| App / Tweak | Description | Source URL |
| :--- | :--- | :--- |
| **YTMusicUltimate** | Unlocked YouTube Music experience | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytmusic.json` |
| **SpotiFLAC Mobile** | Hi-Res Lossless music client | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/spotiflac.json` |

---

### 📦 All-In-One Source (ESign / SideStore)

> [!TIP]
> **ESign** and **SideStore** users can add all apps simultaneously using the master combined source:

```text
[https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json](https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json)
