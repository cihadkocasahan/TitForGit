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

## 📸 Adım Adım Kurulum ve Çalışma Rehberi (Visual Walkthrough)

### Adım 1: TitForGit Web Kontrol Masası
Docker konteyneri ayağa kalktığında `http://localhost:8080` üzerinden kontrol paneline erişin:

![TitForGit Dashboard](docs/images/step1_dashboard.png)

---

### Adım 2: Tek Tıkla Cihaz Yetkilendirmesi (Device Flow)
Token kopyala-yapıştır yapmadan oturum açmak için **"Cihaz Kodu Üret"** butonuna basın. Sistem size 8 haneli tek kullanımlık bir kod üretir:

![Device Code Generation](docs/images/step2_device_code.png)

---

### Adım 3: GitHub Üzerinden Onaylama
**"GitHub'da Aç & Onayla"** bağlantısına tıklayın (veya doğrudan `https://github.com/login/device` adresine gidin), kodu girip onaylayın. Sistem token'ı GitHub'dan otomatik olarak çeker ve güvenli yerel veritabanına kaydeder:

![GitHub Device Authorization](docs/images/step3_github_login.png)

---

### Adım 4: Canlı Çalışma & Aktif Devriye Paneli
Yetkilendirme tamamlandığında sistem arka planda periyodik olarak çalışır, GitHub aktivitelerini anlık yakalar ve belirlediğiniz kurallara göre organik büyüme sağlar.

Tüm hassas kimlik bilgileri (GitHub Token, Telegram Bot Token ve Chat ID) istemci tarafında maskelenmiş olarak görüntülenir:

![TitForGit Active Patrol Dashboard](docs/images/step4_active_dashboard.png)

- **Canlı Devriye Logları:** Son döngüde yakalanan yeni star'lar, forker'lar ve organik niş tarama adımları saniye saniye takip edilir.
- **Micro-Dosing & Anti-Ban Koruması:** GitHub limitlerini aşmamak için her işlem arasında 15-35 saniyelik insansı jitter gecikmeleri uygulanır.

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
Ideal for home labs, VPS, Raspberry Pi, or local machines.

1. Clone repository:
   ```bash
   git clone https://github.com/your-username/titforgit.git
   cd titforgit
   ```

2. Start the container:
   ```bash
   docker compose up -d
   ```

3. Open **`http://localhost:8080`** in browser:
   - Use **Browser Device Flow** button link GitHub account in 5 seconds.
   - Or paste PAT token, set Telegram bot, and configure growth rules.

---

## 📖 Kullanım Kılavuzu ve Kurallar (Usage & Rules)

| Kural / Parametre | Açıklama | Varsayılan |
| :--- | :--- | :--- |
| **👉 Karşılık Dürtmesi (Follow-Back)** | Sizi takip eden geliştiricileri otomatik olarak geri takip eder. Tit-for-Tat mantığıyla çalışır. | `Açık` |
| **⭐ Organik Niş Keşif (Star)** | Belirlediğiniz konulardaki (`topics`) yükselen repoları keşfeder ve yıldız bırakır. | `Açık` |
| **👤 Repo Sahibini Takip Et** | Keşfedilip yıldız verilen projenin yazarını da takibe alarak organik etkileşimi artırır. | `Açık` |
| **🧹 Karşılıksız Takipleri Bırak** | Sizi takip etmeyen kişileri döngü başı 1-2 kişi olacak şekilde güvenli mikro-dozajla takipten çıkarır. | `Kapalı` |
| **💖 Projeleri Otomatik Destekle** | Açık kaynak ekosistemi kapsamında geliştiricinin (`@cihadkocasahan`) açık repolarını otomatik starlar. | `Açık` |
| **Hedef Konular (Topics)** | Aranacak GitHub konu etiketleri (virgülle ayrılmış: örn. `delphi, mcp, python-agent`). | `delphi, mcp...` |
| **Min ★ / Max ★** | Spam veya çöp repolardan kaçınmak ve etkileşim olasılığı yüksek niş projeleri hedeflemek için yıldız aralığı. | `5` - `150` |
| **Döngü Başı (Per Cycle)** | Her çalışma turunda en fazla kaç repoya star atılacağı (anti-ban limiti). | `2` |
| **Aralık (Dk)** | Motorun kaç dakikada bir uyanıp yeni etkileşim arayacağı. | `60` |

---

## ⚖️ Commercial Use, Fair Use & Disclaimer

- **Commercial & Personal Use:** Licensed under the MIT License. You are free to run, host, modify, and distribute this software for personal or commercial workflows.
- **Fair Use & Anti-Ban:** TitForGit operates strictly within GitHub's API rate limits. It incorporates random micro-jitter delays (15–35s) and strict batch micro-dosing (1–2 actions per cycle) designed to prevent aggressive spamming or bot behavior.
- **Disclaimer:** This tool is designed for reciprocal developer engagement and repository discovery. The authors and maintainers take no responsibility for misuse, violation of third-party Terms of Service, or any account limitations resulting from improper rate configuration. Use responsibly.
