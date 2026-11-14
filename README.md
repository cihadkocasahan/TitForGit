<p align="center"><img src="titforgit-logo.svg" width="80" alt="TitForGit Logo"/></p>

# TitForGit [![Awesome](https://awesome.re/badge.svg)](https://awesome.re) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<a href="README.md"><img src="https://flagcdn.com/20x15/gb.png" width="20" height="15" alt="English"> **English**</a> &nbsp;·&nbsp; <a href="README.tr.md"><img src="https://flagcdn.com/20x15/tr.png" width="20" height="15" alt="Türkçe"> **Türkçe**</a>

### AI-Native Coding Demo & Educational Project

TitForGit is an open-source Python application built on the **Tit-for-Tat** principle (Star for Star, Follow for Follow) for GitHub engagement. Written entirely with Python's standard library — zero external dependencies — and packaged as a lightweight ~20 MB Docker image.

**This is a test/showcase project for AI-native coding demos; it is NOT a commercial growth service.**

| | |
|---|---|
| [![Docker](https://img.shields.io/badge/Docker-~20_MB-2496ED?logo=docker&logoColor=white)](#-quick-start) | [![Python 3.11](https://img.shields.io/badge/Python-3.11_Stdlib-3776AB?logo=python&logoColor=white)](https://python.org) |
| [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) | [![Awesome](https://awesome.re/badge.svg)](https://awesome.re) |

---

## ⚠️ Disclaimer & GitHub Policies

TitForGit is an educational AI-native coding demo, **not** a commercial automation or growth service.

- **GitHub Terms:** This tool includes micro-delays to stay within GitHub API rate limits, but compliance with GitHub's [Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) and automation rules is the user's responsibility. Usage may result in account limitations or suspension.
- **Liability:** Authors and maintainers accept no responsibility for misuse, third-party ToS violations, or account restrictions from misconfiguration. Use at your own risk.
- **Usage:** Test only on your own GitHub account. Do not automate on behalf of other users or organizations.

---

## 🚀 Quick Start

### Self-Hosted Docker with Control Deck (~20 MB)

Ideal for homelabs, VPS, Raspberry Pi, or local machines.

```bash
# 1. Clone
git clone https://github.com/your-username/titforgit.git
cd titforgit

# 2. Start container
docker compose up -d

# 3. Open http://localhost:8080 in browser
#    - Click "Browser Device Flow" to link GitHub in 5 seconds
#    - Or paste PAT token, configure Telegram bot, and set growth rules
```

### Local Python (No Docker)

```bash
# Run directly with Python 3.10+
python titforgit.py
```

---

## ✨ Features

- **🤝 Smart Follow-Back** — Automatically follows back users who follow you using micro-dosing (1–2 users per cycle) to protect your account
- **📡 Live Activity Radar** — Real-time Telegram alerts for incoming stars, forks, follows, and new issues
- **🎯 Organic Niche Discovery** — Discovers trending repositories in your target topics (e.g., `fastapi`, `delphi`, `mcp`) and stars them with human-like jitter delays (15–35s)
- **🔐 Dual-Mode Authentication**
  - **Browser Device Flow** — Click a button in the web UI, enter a one-time 8-char code on GitHub, authenticate without touching tokens
  - **Direct PAT** — Paste a Personal Access Token directly
- **🪶 Zero Dependencies** — Pure Python stdlib, zero pip packages, ~20 MB Docker image
- **🛡️ Anti-Ban Protection** — Micro-dosing (1–2 actions/cycle) + random jitter delays (15–35s) between operations

---

---

## 📖 Usage Rules & Configuration

| Rule / Parameter | Description | Default |
| :--- | :--- | :--- |
| **👉 Follow-Back** | Auto-follows developers who follow you (Tit-for-Tat logic) | `Enabled` |
| **⭐ Organic Niche Star** | Discovers trending repos in your topics and leaves stars | `Enabled` |
| **👤 Follow Repo Owner** | Also follows the author of starred repos for organic engagement | `Enabled` |
| **🧹 Unfollow Non-Followers** | Safely unfollows non-followers at 1–2 per cycle (micro-dosing) | `Disabled` |
| **💖 Auto-Support Projects** | Auto-stars the developer's public repos for ecosystem support | `Enabled` |
| **Target Topics** | GitHub topic tags to search (comma-separated: `delphi, mcp, python-agent`) | `delphi, mcp...` |
| **Min ★ / Max ★** | Star range to avoid spam/low-quality repos | `5` – `150` |
| **Per Cycle Limit** | Max repos to star per cycle (anti-ban) | `2` |
| **Interval (min)** | How often the engine wakes to seek engagement | `60` |

---

## ⚖️ License & Terms

- **MIT License** — Free to run, host, modify, and distribute for personal or commercial workflows
- **Demo/Showcase** — This is an AI-native coding demo. Production use is not recommended
- **No Warranty** — Authors/maintainers are not liable for any misuse, ToS violations, or account restrictions. Use entirely at your own risk