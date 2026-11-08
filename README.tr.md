# ⚡ TitForGit [![Awesome](https://awesome.re/badge.svg)](https://awesome.re) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<a href="README.md"><img src="https://flagcdn.com/20x15/gb.png" width="20" height="15" alt="English"> **English**</a> &nbsp;·&nbsp; <a href="README.tr.md"><img src="https://flagcdn.com/20x15/tr.png" width="20" height="15" alt="Türkçe"> **Türkçe**</a>

### AI-Native Kodlama Demo & Eğitim Projesi

TitForGit, GitHub etkileşimi için **Tit-for-Tat** (Yıldız'a Yıldız, Takip'e Takip) prensibine dayanan açık kaynak bir Python uygulamasıdır. Tamamen Python standart kütüphanesiyle yazılmıştır — sıfır harici bağımlılık — ve ~20 MB'lık hafif bir Docker imajı olarak paketlenmiştir.

**Bu proje AI-native kodlama demosu/vitrin amaçlıdır; ticari bir büyüme hizmeti DEĞİLDİR.**

| | |
|---|---|
| [![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Serverless-2088FF?logo=github-actions&logoColor=white)](#-yöntem-1-sunucusuz-github-actions) | [![Docker](https://img.shields.io/badge/Docker-~20_MB-2496ED?logo=docker&logoColor=white)](#-yöntem-2-docker-ile-kendi-sunucunuzda) |
| [![Python 3.11](https://img.shields.io/badge/Python-3.11_Stdlib-3776AB?logo=python&logoColor=white)](https://python.org) | [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) |

---

## ⚠️ Sorumluluk Reddi & GitHub Politikaları

TitForGit bir eğitim amaçlı AI-native kodlama demosudur, ticari bir otomasyon veya büyüme servisi **değildir**.

- **GitHub Şartları:** Bu araç GitHub API hız limitlerine uymak için mikro gecikmeler içerir, ancak GitHub [Kabul Edilebilir Kullanım Politikaları](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) ve otomasyon kurallarına uyum kullanıcının sorumluluğundadır. Kullanım, hesap kısıtlamalarına veya askıya alınmasına neden olabilir.
- **Sorumluluk:** Yazarlar ve bakımcılar kötüye kullanım, üçüncü taraf ToS ihlalleri veya yanlış yapılandırmadan kaynaklanan hesap kısıtlamaları için hiçbir sorumluluk kabul etmez. Riski size aittir.
- **Kullanım:** Yalnızca kendi GitHub hesabınızda test edin. Başka kullanıcılar veya organizasyonlar adına otomasyon çalıştırmayın.

---

## 🚀 Hızlı Başlangıç (Kurulum)

### Yöntem 1: Sunucusuz GitHub Actions

GitHub'ın ücretsiz zamanlanmış runner'larıyla kendi fork'unuzda çalışır.

1. **Fork'layın** — Bu depoyu fork'layın
2. **Secrets ekleyin** — Fork'unuzda **Settings → Secrets and variables → Actions**
   - `GH_PAT` — GitHub Kişisel Erişim Belirteci (`user:follow` & `public_repo` kapsamları)
   - `TELEGRAM_BOT_TOKEN` — (İsteğe bağlı) `@BotFather`'dan alın
   - `TELEGRAM_CHAT_ID` — (İsteğe bağlı) Sayısal Telegram Sohbet ID'niz
3. **Etkinleştirin** — **Actions** sekmesinde workflow'ları etkinleştirin. TitForGit her 2 saatte otomatik çalışır ve durumu repo'nuza commit eder.

### Yöntem 2: Docker ile Kendi Sunucunuzda (~20 MB)

Homelab, VPS, Raspberry Pi veya yerel makineler için idealdir.

```bash
# 1. Klonla
git clone https://github.com/your-username/titforgit.git
cd titforgit

# 2. Container'ı başlat
docker compose up -d

# 3. Tarayıcıda http://localhost:8080 adresini aç
#    - "Cihaz Kodu Üret" ile GitHub'ı 5 saniyede bağla
#    - Veya PAT token yapıştır, Telegram bot ayarla, büyüme kurallarını belirle
```

---

## ✨ Özellikler

- **🤝 Akıllı Geri-Takip** — Sizi takip eden kullanıcıları mikro-dozajla (döngü başına 1–2 kullanıcı) otomatik takip eder, hesabınızı korur
- **📡 Canlı Aktivite Radarı** — Gelen yıldızlar, fork'lar, takipler ve yeni issue'lar için gerçek zamanlı Telegram bildirimleri
- **🎯 Organik Niş Keşfi** — Hedef konularınızdaki (ör. `fastapi`, `delphi`, `mcp`) trend depoları keşfeder ve insan benzeri rastgele gecikmelerle (15–35s) yıldızlar
- **🔐 Çift Modlu Kimlik Doğrulama**
  - **Tarayıcı Cihaz Akışı** — Web arayüzünde butona tıkla, GitHub'da 8 karakterlik tek seferlik kodu gir, token'lara dokunmadan oturum aç
  - **Doğrudan PAT** — Kişisel Erişim Belirtecini doğrudan yapıştır
- **🪶 Sıfır Bağımlılık** — Saf Python stdlib, sıfır pip paketi, ~20 MB Docker imajı
- **🛡️ Anti-Ban Koruması** — Mikro-dozaj (döngü başına 1–2 işlem) + işlemler arası rastgele gecikme (15–35s)

---

## 📸 Görsel Rehber

### TitForGit Kontrol Paneli

Container'ı başlatın ve `http://localhost:8080` adresinden kontrol paneline erişin:

![TitForGit Dashboard](docs/images/step1_dashboard.png)

**Akış Özeti:**
1. **Dashboard'u Aç** → `http://localhost:8080`
2. **Cihaz Kodu Üret** → "Cihaz Kodu Üret" butonuna tıkla → 8 karakterlik kod al
3. **GitHub'da Yetkilendir** → `https://github.com/login/device` adresine git → Kodu gir → Onayla
4. **Yapılandır & Çalıştır** → Konuları, kuralları, Telegram'ı ayarla → Motor otomatik çalışır

---

## 📖 Kullanım Kuralları & Yapılandırma

| Kural / Parametre | Açıklama | Varsayılan |
| :--- | :--- | :--- |
| **👉 Geri-Takip** | Sizi takip eden geliştiricileri otomatik takip eder (Tit-for-Tat mantığı) | `Açık` |
| **⭐ Organik Niş Yıldızı** | Konularınızdaki trend depoları keşfeder ve yıldız bırakır | `Açık` |
| **👤 Repo Sahibini Takip Et** | Yıldızlanan depoların yazarını da organik etkileşim için takip eder | `Açık` |
| **🧹 Takipsizleri Bırak** | Sizi takip etmeyenleri döngü başına 1–2 kişi ile güvenli şekilde bırakır | `Kapalı` |
| **💖 Projelere Otomatik Destek** | Geliştiricinin açık depolarını ekosistem desteği için otomatik yıldızlar | `Açık` |
| **Hedef Konular** | Aranacak GitHub konu etiketleri (virgülle ayrılmış: `delphi, mcp, python-agent`) | `delphi, mcp...` |
| **Min ★ / Max ★** | Spam/düşük kaliteli depolardan kaçınmak için yıldız aralığı | `5` – `150` |
| **Döngü Başına Limit** | Döngü başına yıldızlanacak maksimum depo sayısı (anti-ban) | `2` |
| **Aralık (dk)** | Motorun etkileşim arayışı için uyanma sıklığı | `60` |

---

## ⚖️ Lisans & Şartlar

- **MIT Lisansı** — Kişisel veya ticari iş akışları için çalıştırma, barındırma, değiştirme ve dağıtma serbestîsi
- **Demo/Vitrin** — AI-native kodlama demosudur. Üretim ortamında kullanımı tavsiye edilmez
- **Garanti Yoktur** — Yazarlar/bakımcılar herhangi bir kötüye kullanım, ToS ihlali veya hesap kısıtlamasından sorumlu değildir. Tamamen kendi riskinizle kullanın
