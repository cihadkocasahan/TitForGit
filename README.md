# ⚡ TitForGit

### Autonomous Reciprocal GitHub Engagement Engine
**Game Theory (Tit-for-Tat) for GitHub: Star for Star, Follow for Follow.**
*Zero-Server GitHub Actions + Ultra-Lightweight (~20 MB) Self-Hosted Docker*

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Serverless-2088FF?logo=github-actions&logoColor=white)](#-method-1-serverless-github-actions-no-server-needed)
[![Docker](https://img.shields.io/badge/Docker-~20_MB-2496ED?logo=docker&logoColor=white)](#-method-2-self-hosted-docker-with-control-deck)
[![Python 3.11](https://img.shields.io/badge/Python-3.11_Stdlib-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Stop paying $30/month for closed-source GitHub growth services. Grow organically, safely, and transparently.*

---

## 💡 What is TitForGit?

**TitForGit** is an autonomous, open-source developer engagement engine based on the mathematical principle of **Tit-for-Tat**:
> *Cooperate when others cooperate. Star for Star. Follow for Follow.*

- **🤝 Smart Follow-Back:** Automatically follows back users who follow you using micro-dosing (1-2 users per cycle) to protect your account.
- **📡 Live Activity Radar:** Real-time Telegram alerts for incoming stars, forks, follows, and new issues.
- **🎯 Organic Niche Engagement:** Discovers rising repositories in your target topics (e.g., `fastapi`, `delphi`, `mcp`) and leaves stars with human-like jitter delays (15–35s).
- **🔐 Dual-Mode Authentication:**
  - **Browser Device Flow:** Click a button in the web UI, enter a one-time 8-character code on GitHub, and authenticate without touching tokens.
  - **Direct PAT:** Paste a Personal Access Token directly.
- **🪶 Zero External Dependencies:** Built entirely with Python's standard library. Zero pip packages, zero attack surface, ~20 MB Docker image.

---

## 🚀 Deployment Options

### 🌟 Method 1: Serverless GitHub Actions (No Server Needed)
Runs directly inside your own GitHub fork using GitHub's free scheduled runners.

1. **Fork** this repository.
2. Go to **Settings -> Secrets and variables -> Actions** in your forked repository.
3. Add repository secrets:
   - `GH_PAT`: Your GitHub Personal Access Token (`user:follow` & `public_repo` scopes).
   - `TELEGRAM_BOT_TOKEN`: (Optional) Your Telegram bot token from `@BotFather`.
   - `TELEGRAM_CHAT_ID`: (Optional) Your Telegram numeric Chat ID.
4. Go to the **Actions** tab and enable workflows. TitForGit runs automatically every 2 hours and commits state sync back to your repo!

---

### 🐳 Method 2: Self-Hosted Docker with Control Deck (~20 MB)
Ideal for home labs (Proxmox, Raspberry Pi, VPS, or desktop).

1. Clone repository:
   ```bash
   git clone http://192.168.1.25/ckocasahan/titforgit.git
   cd titforgit
   ```

2. Start the container:
   ```bash
   docker compose up -d
   ```

3. Open **`http://localhost:8080`** in your browser:
   - Use the **Browser Device Flow** button to link your GitHub account in 5 seconds.
   - Or paste your PAT token, set your Telegram bot, and configure your growth rules.
