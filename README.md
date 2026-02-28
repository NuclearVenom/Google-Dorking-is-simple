# 🔍 Google Dork Query Builder

A Python/PyQt5 desktop GUI for constructing advanced Google search queries using the full set of Google dorking operators and filters — no manual syntax required.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-5.x-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

---

## Overview

Google dorking is the practice of using advanced search operators to surface information that standard queries miss — exposed configuration files, open directory listings, login panels, sensitive documents, and more. Writing these queries by hand is error-prone and requires memorising a large set of operators and their exact syntax.

This tool provides a structured, visual interface for composing dork queries. Each filter gets its own input field with per-row operator toggles that modify the token correctly. Filters can be grouped into logical blocks that get wrapped in parentheses, enabling compound boolean expressions that would be tedious to write manually.

The final query is assembled live in a preview bar at the bottom, ready to copy or launch directly in your default browser.

---

## Screenshots

![Main Panel](<screenshots/Screenshot 2026-02-28 154759.png>)
![An Example](<screenshots/Screenshot 2026-02-28 154822.png>)

---

## Features

### All 19 Google Dork Filters
Every standard dork filter is available as a dedicated input row with a placeholder example and a hover tooltip showing its syntax and a real-world usage example.

| Filter | What it does |
|---|---|
| `allintext:` | All keywords must appear in page body text |
| `intext:` | At least one keyword appears in page text |
| `inurl:` | Keyword appears somewhere in the URL |
| `allinurl:` | All keywords must appear in the URL |
| `intitle:` | Keyword appears in the page title tag |
| `allintitle:` | All keywords must appear in the title |
| `site:` | Restrict results to a specific domain |
| `filetype:` | Match a specific file type extension |
| `ext:` | Alternative to filetype |
| `link:` | Pages linking to a given URL |
| `numrange:` | Search within a numeric range |
| `before:` | Results before a date (YYYY-MM-DD) |
| `after:` | Results after a date (YYYY-MM-DD) |
| `inanchor:` | Keyword in anchor/link text pointing to a page |
| `allinanchor:` | All keywords in anchor texts |
| `inpostauthor:` | Blog posts by a specific author |
| `allinpostauthor:` | All keywords in post-author field |
| `related:` | Pages similar to a given URL |
| `cache:` | Google's cached snapshot of a page |

---

### Per-Row Operator Toggles

Each filter row has five toggle buttons that modify **only that token**, applied in the correct order so the output is always valid syntax.

| Toggle | Symbol | Effect | Example output |
|---|---|---|---|
| Exclude | `−` | Prepend `-` to omit this token from results | `-site:facebook.com` |
| Require | `+` | Prepend `+` to force inclusion of this token | `+intext:password` |
| Exact phrase | `"` | Wrap value in quotes for exact matching | `intitle:"index of"` |
| Synonym | `~` | Prefix value with `~` to include synonyms | `intext:~hack` |
| Wildcard | `∗` | Append `*` as an unknown word placeholder | `site:*.com` |

Exclude and Require are mutually exclusive — toggling one automatically untogles the other. Multi-word values without the Exact toggle are auto-quoted.

---

### Grouping with Parentheses

Every filter row has a group radio selector with three states: **· (none)**, **A**, and **B**.

- Rows tagged **A** are collected and wrapped together: `(tokenA1 tokenA2 …)`
- Rows tagged **B** are collected and wrapped together: `(tokenB1 tokenB2 …)`
- Grouped rows are visually highlighted with a coloured left border (teal for A, peach for B)

The right panel exposes two join controls:

- **Default Join** — how ungrouped tokens connect to each other (`AND` / `OR`)
- **Group A ⟷ Group B Join** — the operator placed between the two group blocks (`AND` / `OR`)

This makes it straightforward to build expressions like:

```
(intitle:"login" | inurl:admin) -site:example.com
```
```
(filetype:pdf | ext:doc) intext:"confidential" site:gov
```
```
(site:twitter.com | site:linkedin.com) | (site:facebook.com intext:"profile")
```

---

### 20 Categorised Presets

A scrollable preset panel on the right provides ready-to-use examples across three categories. Each preset sets the filter values, operator toggles, group assignments, and join modes all at once. Hovering a preset shows its description and the join modes it uses.

**Basic**
- 📂 Open Directories
- ⚙️ Config Files
- 📄 Exposed PDFs on .gov
- 🔐 Login Panels
- 🗄️ SQL Backup Files
- 📊 Excel Sheets with Passwords
- 📸 Exposed Webcams
- 🔑 Private SSH Keys
- 📰 Recent Security Research
- 🧑‍💻 GitHub Exposed Tokens

**Intermediate**
- 📁 Docs with Salary Info
- 🌐 WordPress Login Pages (with site exclusion)
- 🗂️ Exposed ENV Files
- 📋 phpMyAdmin Panels
- 🎵 Open Music Directories

**Complex (Grouped)**
- 🔀 Login OR Register pages — two URL patterns OR-grouped
- 🏛️ Gov OR Edu confidential PDFs — domain alternatives in a group
- 🔍 Exposed DB on Any TLD — wildcard + OR-grouped extensions
- 🧩 Admin Panel — Title OR URL detection methods grouped
- 📦 Leaked Archives — `ext:` and `filetype:` variants OR-grouped
- 🕵️ OSINT: Person on Social — two platform groups joined by OR
- 📡 IoT Device Panels — title variants in A, URL patterns in B
- 📜 Sensitive Docs Excluding Known Sites — exact phrase with exclusions

---

### Additional Features

- **Live query preview** — the assembled dork query updates in real time as you type or toggle operators
- **One-click copy** — copies the full query to the clipboard with a status bar confirmation
- **Open in browser** — launches the query directly in Google via your system's default browser
- **Character counter** — shows the query length and warns if it approaches Google's truncation limit
- **Hover tooltips everywhere** — every filter, toggle button, group control, and preset has a descriptive tooltip with syntax examples
- **High-contrast dark theme** — built with PyQt5's Fusion style engine for crisp, DPI-aware rendering on all platforms

---

## Installation

**Requirements:** Python 3.8 or higher

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/google-dork-builder.git
   cd google-dork-builder
   ```

2. Install the dependency:
   ```bash
   pip install PyQt5
   ```

3. Run the app:
   ```bash
   python GoogleDorker.py
   ```

No other dependencies. The standard library handles URL encoding and browser launching.

---

## Usage

1. **Type your base query** in the top field — this is plain text, the same as a normal Google search.
2. **Fill in any filter fields** you want to use. Leave the rest blank — blank rows are skipped automatically.
3. **Apply per-row toggles** as needed. For example, enable `"` (exact) on `intitle:` to wrap the value in quotes, or enable `−` (exclude) on `site:` to block a domain from results.
4. **Assign groups** using the `A` / `B` radio buttons on each row if you want tokens wrapped in parentheses together.
5. **Set the join modes** in the right panel to control whether tokens are combined with AND or OR.
6. **Copy or search** using the buttons in the query bar at the bottom.

---

## How the Query Is Assembled

```
base_query  ungrouped_tokens  (group_A_tokens)  [join]  (group_B_tokens)
```

1. Each row's value is processed through its active toggles in order: wildcard → synonym → exact → prefix:value → exclude/require.
2. Tokens are sorted into three buckets: ungrouped, Group A, Group B.
3. Group A tokens are joined by the Default Join and wrapped in `(…)` if there is more than one.
4. Group B tokens are handled the same way.
5. If both groups are active, all top-level parts are joined by the Group Join operator. Otherwise the Default Join is used throughout.

---

## Disclaimer

This tool is intended for legitimate research, security assessments, OSINT investigations, and learning purposes. Google dorking on systems you do not own or have explicit permission to test may violate terms of service or applicable law. Use responsibly.

---

## License

MIT License — see `LICENSE` for details.
