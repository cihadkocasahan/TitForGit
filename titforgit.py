#!/usr/bin/env python3
"""
TitForGit - Autonomous Reciprocal Engagement Engine
Game Theory (Tit-for-Tat) applied to GitHub community growth.
Star for Star. Follow for Follow.

Features:
- Pure Python Standard Library (0 external pip dependencies)
- Dual Auth: Direct PAT token OR GitHub Device Flow (Web UI code login)
- Lightweight Web Dashboard & Setup Wizard (stdlib http.server)
- Smart Follow-Back (micro-dosed)
- Live Telegram Activity Radar
- Organic Niche Discovery (Jitter-spaced rule-based engagement)
"""

import os
import sys
import json
import time
import random
import threading
import urllib.request
import urllib.error
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

DATA_DIR = os.getenv("TITFORGIT_DATA_DIR", "/data" if os.path.exists("/data") else ".")
STATE_FILE = os.path.join(DATA_DIR, "titforgit_state.json")
CONFIG_FILE = os.path.join(DATA_DIR, "titforgit_config.json")

# Standard GitHub Device Flow Client ID (Official Public GitHub CLI Client ID)
GITHUB_DEVICE_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "178c6fc778ccc68e1d6a")

class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TitForGit-Autonomous-Engine/1.0"
        }

    def _request(self, endpoint: str, method: str = "GET", data: dict | None = None):
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}{endpoint}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status in (200, 201):
                    return json.loads(resp.read().decode("utf-8"))
                return {"status": resp.status}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"[!] GitHub API HTTP {e.code}: {e.reason} ({url})")
            return None
        except Exception as e:
            print(f"[!] GitHub API Error: {e} ({url})")
            return None

    def get_authenticated_user(self):
        return self._request("/user")

    def get_user_events(self, username: str) -> list[dict]:
        res = self._request(f"/users/{username}/events?per_page=30")
        return res if isinstance(res, list) else []

    def get_followers(self, username: str) -> list[dict]:
        res = self._request(f"/users/{username}/followers?per_page=100")
        return res if isinstance(res, list) else []

    def get_following(self, username: str) -> list[dict]:
        res = self._request(f"/users/{username}/following?per_page=100")
        return res if isinstance(res, list) else []

    def follow_user(self, target_user: str) -> bool:
        res = self._request(f"/user/following/{target_user}", method="PUT")
        return res is not None

    def star_repo(self, repo_full_name: str) -> bool:
        res = self._request(f"/user/starred/{repo_full_name}", method="PUT")
        return res is not None

    def search_repositories(self, query: str, limit: int = 10):
        encoded = urllib.parse.quote(query)
        res = self._request(f"/search/repositories?q={encoded}&sort=updated&order=desc&per_page={limit}")
        return (res or {}).get("items", [])


class GitHubDeviceAuth:
    """Manages passwordless browser login via GitHub Device Flow"""
    @staticmethod
    def start_flow(client_id: str = GITHUB_DEVICE_CLIENT_ID):
        url = "https://github.com/login/device/code"
        data = urllib.parse.urlencode({
            "client_id": client_id,
            "scope": "user:follow public_repo"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[!] Device flow başlatma hatası: {e}")
            return None

    @staticmethod
    def poll_token(device_code: str, client_id: str = GITHUB_DEVICE_CLIENT_ID):
        url = "https://github.com/login/oauth/access_token"
        data = urllib.parse.urlencode({
            "client_id": client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res
        except Exception as e:
            return {"error": str(e)}


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = str(chat_id)

    def send_message(self, text: str):
        if not self.bot_token or not self.chat_id:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception as e:
            print(f"[!] Telegram bildirim hatası: {e}")


class TitForGitEngine:
    def __init__(self, config: dict):
        self.config = config
        self.gh = GitHubClient(config.get("github_token", ""))
        self.notifier = TelegramNotifier(
            config.get("telegram_bot_token", ""),
            config.get("telegram_chat_id", "")
        )
        self.state = self._load_state()
        self.authenticated_user_cache = None
        self._refresh_user_cache()

    def _refresh_user_cache(self):
        if self.config.get("github_token"):
            try:
                self.authenticated_user_cache = self.gh.get_authenticated_user()
            except Exception:
                self.authenticated_user_cache = None
        else:
            self.authenticated_user_cache = None

    def update_config(self, new_config: dict):
        self.config.update(new_config)
        self.gh = GitHubClient(self.config.get("github_token", ""))
        self.notifier = TelegramNotifier(
            self.config.get("telegram_bot_token", ""),
            self.config.get("telegram_chat_id", "")
        )
        self._refresh_user_cache()

    def _load_state(self) -> dict:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "processed_events": [],
            "followed_users": [],
            "starred_repos": [],
            "last_run": None,
            "is_paused": False,
            "logs": []
        }

    def _save_state(self):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[!] State kaydetme hatası: {e}")

    def log(self, text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {text}"
        print(entry)
        self.state.setdefault("logs", []).append(entry)
        self.state["logs"] = self.state["logs"][-200:]

    def run_cycle(self, force: bool = False):
        if not force and self.state.get("is_paused", False):
            return

        if not self.config.get("github_token"):
            self.log("Beklemede: GitHub bağlantısı henüz yapılmadı.")
            return

        user_info = self.gh.get_authenticated_user()
        if not user_info or "login" not in user_info:
            self.log("HATA: GitHub token geçersiz veya yetkisiz.")
            return

        username = user_info["login"]
        self.log(f"TitForGit devrede: @{username}")
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Activity Radar (Gelen Star, Fork, Takip Bildirimleri)
        self._check_radar_events(username)

        # 2. Smart Follow-Back (Seni takip edeni geri takip et)
        if self.config.get("auto_follow_back", True):
            self._process_follow_back(username)

        # 3. Niche Engagement (Kural tabanlı organik büyüme)
        if self.config.get("niche_discovery_enabled", False):
            self._process_niche_discovery()

        self.state["last_run"] = now_str
        self._save_state()
        self.log("Döngü tamamlandı.")

    def _check_radar_events(self, username: str):
        events = self.gh.get_user_events(username)
        processed = set(self.state.get("processed_events", []))
        new_processed = []

        for ev in events:
            if not isinstance(ev, dict):
                continue
            ev_id = ev.get("id")
            if not ev_id or ev_id in processed:
                continue

            ev_type = ev.get("type")
            actor = ev.get("actor", {}).get("login", "Bilinmeyen")
            repo_name = ev.get("repo", {}).get("name", "")

            msg = None
            if ev_type == "WatchEvent" and ev.get("payload", {}).get("action") == "started":
                msg = f"⭐ <b>Yeni Star!</b>\n👤 <b>{actor}</b> -> <code>{repo_name}</code> projenize star verdi."
                self.log(f"Yeni Star: @{actor} -> {repo_name}")
            elif ev_type == "ForkEvent":
                fork_repo = ev.get("payload", {}).get("forkee", {}).get("full_name", "")
                msg = f"🍴 <b>Yeni Fork!</b>\n👤 <b>{actor}</b>, <code>{repo_name}</code> projesini çatalladı."
                self.log(f"Yeni Fork: @{actor} -> {repo_name}")
            elif ev_type == "IssuesEvent" and ev.get("payload", {}).get("action") == "opened":
                issue_title = ev.get("payload", {}).get("issue", {}).get("title", "")
                msg = f"📌 <b>Yeni Issue!</b>\n👤 <b>{actor}</b> -> <code>{repo_name}</code>\nBaşlık: <i>{issue_title}</i>"
                self.log(f"Yeni Issue: @{actor} -> {repo_name}")

            if msg:
                self.notifier.send_message(msg)

            new_processed.append(ev_id)

        self.state["processed_events"] = (new_processed + list(processed))[:200]

    def _process_follow_back(self, username: str):
        followers = self.gh.get_followers(username)
        following_list = {u["login"] for u in self.gh.get_following(username)}
        
        limit = self.config.get("max_follow_back_per_cycle", 2)
        done = 0

        for f in followers:
            f_login = f["login"]
            if f_login not in following_list and f_login not in self.state.get("followed_users", []):
                delay = random.uniform(5.0, 15.0)
                time.sleep(delay)
                if self.gh.follow_user(f_login):
                    self.log(f"Geri takip yapıldı: @{f_login}")
                    self.state.setdefault("followed_users", []).append(f_login)
                    self.notifier.send_message(f"🤝 <b>Geri Takip (Follow-Back)</b>\n👤 <b>{f_login}</b> sizi takip ettiği için geri takibe alındı.")
                    done += 1
                    if done >= limit:
                        break

    def _process_niche_discovery(self):
        topics = self.config.get("target_topics", [])
        if not topics:
            return

        selected_topic = random.choice(topics)
        min_stars = self.config.get("min_stars", 5)
        max_stars = self.config.get("max_stars", 150)
        query = f"topic:{selected_topic} stars:{min_stars}..{max_stars} archived:false"
        
        repos = self.gh.search_repositories(query, limit=5)
        starred = set(self.state.get("starred_repos", []))

        daily_limit = self.config.get("daily_star_limit", 3)
        count = 0

        for r in repos:
            full_name = r["full_name"]
            owner = r["owner"]["login"]
            if full_name in starred:
                continue

            delay = random.uniform(15.0, 35.0)
            self.log(f"Jitter bekleyişi ({delay:.1f}s) -> {full_name}")
            time.sleep(delay)

            if self.gh.star_repo(full_name):
                self.log(f"Niş Star bırakıldı: {full_name}")
                self.state.setdefault("starred_repos", []).append(full_name)
                
                if self.config.get("follow_target_owner", False):
                    self.gh.follow_user(owner)
                    self.state.setdefault("followed_users", []).append(owner)

                self.notifier.send_message(
                    f"🎯 <b>Organik Niş Etkileşimi (TitForGit)</b>\n"
                    f"📦 Repo: <code>{full_name}</code> (★ {r['stargazers_count']})\n"
                    f"🏷 Konu: <code>{selected_topic}</code>\n"
                    f"👤 Geliştirici: <b>{owner}</b>"
                )
                count += 1
                if count >= daily_limit:
                    break


# ────────────────────────────────────────────────────────────────
# Hafif Web Arayüzü & Device Auth Sunucusu (Zero-Pip Stdlib)
# ────────────────────────────────────────────────────────────────

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TitForGit Control Deck</title>
  <style>
    :root {
      --bg: #090d13; --panel: #161b22; --border: #30363d;
      --accent: #238636; --accent-hover: #2ea043; --text: #c9d1d9;
      --heading: #f0f6fc; --highlight: #58a6ff; --danger: #da3633;
      --warning: #d29922;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 20px; line-height: 1.4; height: 100vh; overflow: hidden; }
    
    .layout { display: flex; gap: 20px; height: calc(100vh - 40px); max-width: 1300px; margin: 0 auto; }
    @media (max-width: 860px) { body { height: auto; overflow: auto; } .layout { flex-direction: column; height: auto; } }

    /* SOL PANEL: AYARLAR (380px Dikey) */
    .sidebar { width: 400px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; padding-right: 4px; }
    
    /* ORTA/SAĞ PANEL: CANLI LOGLAR VE BAŞLIK */
    .main-view { flex-grow: 1; display: flex; flex-direction: column; gap: 16px; min-width: 0; }
    
    .card { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
    .card-title { font-size: 14px; font-weight: 600; color: var(--heading); margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; }
    
    .header-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; }
    .brand { font-size: 20px; font-weight: 700; color: var(--heading); display: flex; align-items: center; gap: 8px; }
    .badge { background: #1f6feb26; color: var(--highlight); font-size: 11px; padding: 3px 8px; border-radius: 12px; border: 1px solid #1f6feb66; }
    
    .btn-group { display: flex; gap: 10px; }
    .btn {
      background: var(--accent); color: #fff; border: none; border-radius: 6px; padding: 8px 14px;
      font-size: 13px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
    }
    .btn:hover { background: var(--accent-hover); }
    .btn-secondary { background: #21262d; border: 1px solid var(--border); color: var(--text); }
    .btn-secondary:hover { background: #30363d; color: var(--heading); }
    /* Modern Canlı Switch Toggle */
    .switch-wrap { display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 600; cursor: pointer; user-select: none; }
    .switch { position: relative; display: inline-block; width: 44px; height: 24px; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
      background-color: #30363d; transition: .25s; border-radius: 24px; border: 1px solid var(--border);
    }
    .slider:before {
      position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px;
      background-color: #8b949e; transition: .25s; border-radius: 50%;
    }
    input:checked + .slider { background-color: #238636; border-color: #3fb95066; }
    input:checked + .slider:before { transform: translateX(20px); background-color: #fff; }

    label { display: block; font-size: 12px; font-weight: 500; margin-bottom: 4px; color: var(--text); }
    input[type="text"], input[type="password"] {
      width: 100%; background: #0d1117; border: 1px solid var(--border); border-radius: 6px;
      padding: 7px 10px; color: var(--heading); font-size: 13px; margin-bottom: 10px;
    }
    input:focus { outline: none; border-color: var(--highlight); }

    .toggle-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; font-size: 13px; }
    
    .auth-box { background: #0d1117; border: 1px dashed var(--border); border-radius: 6px; padding: 12px; text-align: center; margin-bottom: 12px; }
    .code-display { font-family: monospace; font-size: 22px; font-weight: 700; color: #3fb950; letter-spacing: 3px; margin: 8px 0; }

    /* GENİŞ CANLI LOG ALANI */
    .log-card { flex-grow: 1; display: flex; flex-direction: column; min-height: 300px; }
    .log-terminal {
      flex-grow: 1; background: #06090f; border: 1px solid var(--border); border-radius: 6px;
      padding: 14px; overflow-y: auto; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      font-size: 12px; line-height: 1.6; color: #8b949e;
    }
    .log-entry { margin-bottom: 4px; word-break: break-all; }
    .log-entry.star { color: #f2cc60; }
    .log-entry.follow { color: #58a6ff; }
    .log-entry.success { color: #3fb950; }

    .toast {
      position: fixed; bottom: 20px; right: 20px; background: #238636; color: #fff;
      padding: 10px 18px; border-radius: 6px; font-size: 13px; font-weight: 600;
      box-shadow: 0 8px 24px rgba(0,0,0,0.6); opacity: 0; transform: translateY(15px);
      transition: all 0.25s ease; pointer-events: none; z-index: 1000;
    }
    .toast.show { opacity: 1; transform: translateY(0); pointer-events: auto; }
    .toast.error { background: #da3633; }
    .info-tip {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.1);
      color: var(--text);
      font-size: 10px;
      cursor: help;
      margin-left: 6px;
      position: relative;
    }
    .info-tip:hover {
      background: var(--accent);
      color: #fff;
    }
    .info-tip:hover::after {
      content: attr(data-tooltip);
      position: absolute;
      left: 20px;
      top: -6px;
      background: #161b22;
      border: 1px solid var(--border);
      color: var(--heading);
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 11px;
      white-space: normal;
      width: 220px;
      line-height: 1.4;
      z-index: 100;
      box-shadow: 0 4px 12px rgba(0,0,0,0.5);
      pointer-events: none;
    }
  </style>
</head>
<body>
  <div id="toast" class="toast">✓ İşlem başarılı</div>
  
  <div class="layout">
    <!-- SOL: DİKEY AYARLAR PANELİ -->
    <div class="sidebar">
      <!-- 1. GİRİŞ KARTI (STATE-AWARE: LOGGED IN VS LOGGED OUT) -->
      <div class="card" id="authCard">
        <div class="card-title">🔐 1. GitHub Bağlantısı</div>
        
        <!-- DURUM A: GİRİŞ YAPILMIŞ (LOGGED IN) -->
        <div id="loggedInState" style="display: none;">
          <div style="display: flex; align-items: center; gap: 12px; background: #0d1117; padding: 12px; border-radius: 6px; border: 1px solid var(--border); margin-bottom: 12px;">
            <img id="userAvatar" src="" style="width: 40px; height: 40px; border-radius: 50%; border: 1px solid var(--border);" />
            <div style="flex-grow: 1; min-width: 0;">
              <div style="font-size: 11px; color: #3fb950; font-weight: 600;">✓ BAĞLI HESAP</div>
              <div id="accountLogin" style="font-size: 14px; font-weight: 700; color: var(--heading);">@user</div>
            </div>
          </div>
          <button class="btn btn-secondary" style="width: 100%; justify-content: center; color: var(--danger); border-color: #da363344;" onclick="logoutGitHub()">Bağlantıyı Kes</button>
        </div>

        <!-- DURUM B: GİRİŞ YAPILMAMIŞ (LOGGED OUT) -->
        <div id="loggedOutState">
          <div class="auth-box">
            <div style="font-size: 12px; font-weight: 500;">Tarayıcı ile Tek Tıkla Bağlan</div>
            <button class="btn btn-secondary" style="margin-top: 8px; width: 100%; justify-content: center;" onclick="startDeviceFlow()">Cihaz Kodu Üret</button>
            <div id="flowArea" style="display: none; margin-top: 10px;">
              <div class="code-display" id="userCode">----</div>
              <a id="authLink" href="#" target="_blank" class="btn" style="width: 100%; justify-content: center; margin-top: 4px;">GitHub'da Aç & Onayla</a>
              <div id="pollStatus" style="font-size: 11px; color: var(--highlight); margin-top: 6px;">Onay bekleniyor...</div>
            </div>
          </div>
          <label>Veya PAT Token Yapıştır</label>
          <input type="password" id="ghToken" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" />
        </div>
      </div>

      <!-- 2. BÜYÜME VE HEDEFLER -->
      <div class="card">
        <div class="card-title">🎯 2. Tit-for-Tat Kuralları</div>
        <div class="toggle-row">
          <span>🤝 Smart Follow-Back <span class="info-tip" data-tooltip="Sizi takip eden geliştiricileri otomatik olarak geri takip eder.">?</span></span>
          <input type="checkbox" id="autoFollow" checked />
        </div>
        <div class="toggle-row">
          <span>🎯 Organik Niş Keşif (Star) <span class="info-tip" data-tooltip="Belirlediğiniz konulardaki yükselen repoları keşfedip yıldız bırakır.">?</span></span>
          <input type="checkbox" id="nicheEnabled" checked />
        </div>
        <div class="toggle-row">
          <span>👤 Repo Sahibini Takip Et <span class="info-tip" data-tooltip="Keşfedilip yıldız verilen projenin yazarını da takibe alır.">?</span></span>
          <input type="checkbox" id="followOwner" checked />
        </div>
        <label style="margin-top: 8px;">Hedef Konular (Topics) <span class="info-tip" data-tooltip="Aranacak GitHub topic etiketleri. Virgülle ayırarak yazın.">?</span></label>
        <input type="text" id="targetTopics" value="delphi, mcp, python-agent" />
        <div style="display: flex; gap: 8px;">
          <div><label>Min ★ <span class="info-tip" data-tooltip="Çok çöp repolara düşmemek için alt sınır.">?</span></label><input type="text" id="minStars" value="5" /></div>
          <div><label>Max ★ <span class="info-tip" data-tooltip="Büyük repolar yerine sizi fark edecek niş repolar için üst sınır.">?</span></label><input type="text" id="maxStars" value="150" /></div>
          <div><label>Döngü Başı <span class="info-tip" data-tooltip="Her çalışma turunda en fazla kaç repoya star atılacağı (anti-ban limiti).">?</span></label><input type="text" id="dailyLimit" value="2" /></div>
        </div>
        <label style="margin-top: 4px;">Çalışma Aralığı (Dakika) <span class="info-tip" data-tooltip="Motorun kaç dakikada bir uyanıp yeni etkileşim arayacağı.">?</span></label>
        <input type="text" id="intervalMinutes" value="60" placeholder="Örn: 60 (varsayılan: 1 saat)" />
      </div>

      <!-- 3. TELEGRAM RADAR & KAYDET -->
      <div class="card">
        <div class="card-title">📡 3. Telegram Canlı Radar <span class="info-tip" data-tooltip="Gelen yıldız, takip ve fork olaylarını anında Telegram'a iletir. Boş bırakırsanız sadece yerel log tutar.">?</span></div>
        <input type="text" id="tgBotToken" placeholder="Bot Token (Opsiyonel @BotFather)" />
        <input type="text" id="tgChatId" placeholder="Chat ID (Opsiyonel)" />
        <button class="btn" style="width: 100%; justify-content: center; margin-top: 4px;" onclick="saveConfig()">💾 Ayarları Kaydet</button>
      </div>
    </div>

    <!-- ORTA / SAĞ: BAŞLIK VE GENİŞ LOG EKRANI -->
    <div class="main-view">
      <div class="card header-bar">
        <div class="brand">
          ⚡ TitForGit <span class="badge">v1.0.0 Self-Hosted</span>
        </div>
        <div>
          <!-- Sade Canlı Switch Toggle (Tek Kontrol) -->
          <label class="switch-wrap">
            <span id="switchLabel" style="color: #3fb950;">Açık</span>
            <div class="switch">
              <input type="checkbox" id="patrolSwitch" checked onchange="togglePatrolSwitch(this.checked)">
              <span class="slider"></span>
            </div>
          </label>
        </div>
      </div>

      <div class="card log-card">
        <div class="card-title">
          <span>📋 TitForGit Canlı Akış & Radar</span>
          <div style="display: flex; align-items: center; gap: 12px;">
            <!-- Canlı Filtre Arama Kutusu -->
            <input type="text" id="logFilter" placeholder="🔍 Loglarda ara (star, follow, saat...)" 
                   style="margin-bottom: 0; padding: 4px 10px; font-size: 11px; width: 220px;" oninput="applyLogFilter()" />
            <!-- Auto-scroll Switch (Varsayılan Kapalı) -->
            <label style="display: flex; align-items: center; gap: 5px; font-size: 11px; cursor: pointer; user-select: none; color: var(--text);">
              <input type="checkbox" id="autoScroll" />
              <span>Oto-Kaydır</span>
            </label>
            <span id="patrolBadge" style="font-size: 11px; color: #3fb950;">● Motor Aktif</span>
          </div>
        </div>
        <div class="log-terminal" id="logBox">
          <div class="log-entry">[*] TitForGit Konsolu hazır.</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let pollInterval = null;
    let isPaused = false;
    let allLogs = [];

    function showToast(msg, isError = false) {
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.className = isError ? 'toast show error' : 'toast show';
      setTimeout(() => { t.className = 'toast'; }, 3500);
    }

    async function loadConfig() {
      const res = await fetch('/api/config');
      const cfg = await res.json();
      if (cfg.github_token) document.getElementById('ghToken').value = cfg.github_token;
      if (cfg.telegram_bot_token) document.getElementById('tgBotToken').value = cfg.telegram_bot_token;
      if (cfg.telegram_chat_id) document.getElementById('tgChatId').value = cfg.telegram_chat_id;
      document.getElementById('autoFollow').checked = cfg.auto_follow_back !== false;
      document.getElementById('nicheEnabled').checked = !!cfg.niche_discovery_enabled;
      document.getElementById('followOwner').checked = !!cfg.follow_target_owner;
      if (cfg.target_topics) document.getElementById('targetTopics').value = cfg.target_topics.join(', ');
      if (cfg.interval_minutes) document.getElementById('intervalMinutes').value = cfg.interval_minutes;
      
      await checkStatus();
      refreshLogs();
    }

    async function checkStatus() {
      const sRes = await fetch('/api/status');
      const sData = await sRes.json();
      updateStatusUI(sData.is_paused);
      updateAuthUI(sData);
    }

    function updateAuthUI(data) {
      const loggedInDiv = document.getElementById('loggedInState');
      const loggedOutDiv = document.getElementById('loggedOutState');
      if (data.logged_in && data.username) {
        loggedInDiv.style.display = 'block';
        loggedOutDiv.style.display = 'none';
        document.getElementById('accountLogin').innerText = '@' + data.username;
        if (data.avatar_url) document.getElementById('userAvatar').src = data.avatar_url;
      } else {
        loggedInDiv.style.display = 'none';
        loggedOutDiv.style.display = 'block';
      }
    }

    async function logoutGitHub() {
      await fetch('/api/logout', { method: 'POST' });
      document.getElementById('ghToken').value = '';
      showToast('Oturum kapatıldı.');
      await checkStatus();
      refreshLogs();
    }

    function updateStatusUI(paused) {
      isPaused = paused;
      const sw = document.getElementById('patrolSwitch');
      const lbl = document.getElementById('switchLabel');
      const badge = document.getElementById('patrolBadge');
      
      const mins = document.getElementById('intervalMinutes').value || '60';
      sw.checked = !isPaused;
      if (isPaused) {
        lbl.innerText = 'Kapalı';
        lbl.style.color = '#8b949e';
        badge.innerText = '○ Kapalı';
        badge.style.color = '#8b949e';
      } else {
        lbl.innerText = 'Açık';
        lbl.style.color = '#3fb950';
        badge.innerText = `● Çalışıyor (${mins} dk aralık)`;
        badge.style.color = '#3fb950';
      }
    }

    async function togglePatrolSwitch(isActive) {
      const res = await fetch('/api/toggle', { method: 'POST' });
      const data = await res.json();
      updateStatusUI(data.is_paused);
      showToast(data.is_paused ? '○ TitForGit durduruldu' : '● TitForGit başlatıldı');
      refreshLogs();
    }

    async function saveConfig() {
      const payload = {
        github_token: document.getElementById('ghToken').value.trim(),
        telegram_bot_token: document.getElementById('tgBotToken').value.trim(),
        telegram_chat_id: document.getElementById('tgChatId').value.trim(),
        auto_follow_back: document.getElementById('autoFollow').checked,
        niche_discovery_enabled: document.getElementById('nicheEnabled').checked,
        follow_target_owner: document.getElementById('followOwner').checked,
        target_topics: document.getElementById('targetTopics').value.split(',').map(s => s.trim()).filter(Boolean),
        min_stars: parseInt(document.getElementById('minStars').value) || 5,
        max_stars: parseInt(document.getElementById('maxStars').value) || 150,
        daily_star_limit: parseInt(document.getElementById('dailyLimit').value) || 2,
        interval_minutes: parseInt(document.getElementById('intervalMinutes').value) || 60
      };
      await fetch('/api/config', { method: 'POST', body: JSON.stringify(payload) });
      showToast('✓ Ayarlar kaydedildi!');
      await checkStatus();
      refreshLogs();
    }

    async function startDeviceFlow() {
      const res = await fetch('/api/device/start', { method: 'POST' });
      const data = await res.json();
      if (!data.user_code) { showToast('Hata: Cihaz kodu alınamadı.', true); return; }
      document.getElementById('userCode').innerText = data.user_code;
      document.getElementById('authLink').href = data.verification_uri;
      document.getElementById('flowArea').style.display = 'block';

      let pollDelay = (data.interval || 5) * 1000;
      const pollFn = async () => {
        const pRes = await fetch(`/api/device/poll?device_code=${data.device_code}`);
        const pData = await pRes.json();
        if (pData.access_token) {
          document.getElementById('ghToken').value = pData.access_token;
          document.getElementById('pollStatus').innerText = '✓ Bağlandı!';
          document.getElementById('pollStatus').style.color = '#3fb950';
          await saveConfig();
          await checkStatus();
        } else if (pData.error === 'slow_down') {
          pollDelay += 5000;
          setTimeout(pollFn, pollDelay);
        } else if (pData.error === 'authorization_pending') {
          setTimeout(pollFn, pollDelay);
        } else {
          document.getElementById('pollStatus').innerText = 'Hata: ' + pData.error;
        }
      };
      setTimeout(pollFn, pollDelay);
    }

    async function triggerRun() {
      await fetch('/api/run', { method: 'POST' });
      showToast('🚀 Devriye döngüsü başlatıldı!');
      setTimeout(refreshLogs, 1500);
    }

    async function refreshLogs() {
      const res = await fetch('/api/logs');
      const data = await res.json();
      allLogs = data.logs || [];
      applyLogFilter();
    }

    function applyLogFilter() {
      const filter = (document.getElementById('logFilter').value || '').toLowerCase();
      const filtered = allLogs.filter(l => l.toLowerCase().includes(filter));
      const box = document.getElementById('logBox');
      
      // Kullanıcı yukarıyı okuyorsa (en altta değilse) kaydırmayı zorlama
      const isAtBottom = (box.scrollHeight - box.scrollTop - box.clientHeight) < 40;
      
      box.innerHTML = filtered.map(l => {
        let cls = 'log-entry';
        if (l.includes('Star')) cls += ' star';
        else if (l.includes('takip')) cls += ' follow';
        else if (l.includes('tamamlandı') || l.includes('devrede') || l.includes('aktif')) cls += ' success';
        return `<div class="${cls}">${l}</div>`;
      }).join('');

      if (document.getElementById('autoScroll').checked && isAtBottom) {
        box.scrollTop = box.scrollHeight;
      }
    }

    setInterval(refreshLogs, 4000);
    window.onload = async () => {
      await loadConfig();
      const box = document.getElementById('logBox');
      box.scrollTop = box.scrollHeight;
    };
  </script>
</body>
</html>
"""

class WebServerHandler(BaseHTTPRequestHandler):
    engine: TitForGitEngine = None  # type: ignore

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
        elif parsed.path == "/api/config":
            self._send_json(self.engine.config)
        elif parsed.path == "/api/status":
            user_data = self.engine.authenticated_user_cache
            self._send_json({
                "is_paused": bool(self.engine.state.get("is_paused", False)),
                "last_run": self.engine.state.get("last_run"),
                "logged_in": bool(user_data and "login" in user_data),
                "username": user_data.get("login") if user_data else None,
                "avatar_url": user_data.get("avatar_url") if user_data else None
            })
        elif parsed.path == "/api/logs":
            self._send_json({"logs": self.engine.state.get("logs", [])})
        elif parsed.path == "/api/device/poll":
            qs = urllib.parse.parse_qs(parsed.query)
            code = qs.get("device_code", [""])[0]
            res = GitHubDeviceAuth.poll_token(code)
            self._send_json(res)
        else:
            self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        if self.path == "/api/config":
            try:
                new_cfg = json.loads(body.decode("utf-8"))
                self.engine.update_config(new_cfg)
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.engine.config, f, indent=2, ensure_ascii=False)
                self._send_json({"status": "ok"})
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
        elif self.path == "/api/device/start":
            res = GitHubDeviceAuth.start_flow()
            self._send_json(res or {"error": "Device flow failed"})
        elif self.path == "/api/run":
            threading.Thread(target=lambda: self.engine.run_cycle(force=True)).start()
            self._send_json({"status": "started"})
        elif self.path == "/api/toggle":
            current = self.engine.state.get("is_paused", False)
            self.engine.state["is_paused"] = not current
            self.engine._save_state()
            state_text = "DURDURULDU" if self.engine.state["is_paused"] else "BAŞLATILDI"
            self.engine.log(f"TitForGit {state_text}.")
            # Açıldığında hemen bir döngü tetikle
            if not self.engine.state["is_paused"]:
                threading.Thread(target=lambda: self.engine.run_cycle(force=True)).start()
            self._send_json({"is_paused": self.engine.state["is_paused"]})
        elif self.path == "/api/logout":
            self.engine.config["github_token"] = ""
            self.engine.update_config(self.engine.config)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.engine.config, f, indent=2, ensure_ascii=False)
            self.engine.log("GitHub oturumu kapatıldı (Token temizlendi).")
            self._send_json({"status": "logged_out"})
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass # Sessiz HTTP logları


def load_config() -> dict:
    config = {
        "github_token": os.getenv("GITHUB_TOKEN", ""),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "auto_follow_back": os.getenv("AUTO_FOLLOW_BACK", "true").lower() == "true",
        "niche_discovery_enabled": os.getenv("NICHE_DISCOVERY_ENABLED", "true").lower() == "true",
        "target_topics": [t.strip() for t in os.getenv("TARGET_TOPICS", "delphi,mcp,python-agent").split(",") if t.strip()],
        "min_stars": int(os.getenv("MIN_STARS", "5")),
        "max_stars": int(os.getenv("MAX_STARS", "150")),
        "daily_star_limit": int(os.getenv("DAILY_STAR_LIMIT", "2")),
        "follow_target_owner": os.getenv("FOLLOW_TARGET_OWNER", "true").lower() == "true",
        "max_follow_back_per_cycle": int(os.getenv("MAX_FOLLOW_BACK_PER_CYCLE", "2")),
        "web_port": int(os.getenv("PORT", "8080"))
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_cfg = json.load(f)
                config.update(file_cfg)
        except Exception:
            pass
    return config


if __name__ == "__main__":
    cfg = load_config()
    engine = TitForGitEngine(cfg)

    run_mode = os.getenv("RUN_MODE", "server").lower()

    if run_mode == "cron":
        # Tek seferlik GitHub Actions modu
        engine.run_cycle()
        sys.exit(0)

    # Arka plan periyodik döngü iş parçacığı
    def background_worker():
        # Başlangıçta hemen bir döngü koş
        time.sleep(2)
        try:
            engine.run_cycle()
        except Exception as e:
            engine.log(f"Worker hatası: {e}")
            
        while True:
            interval_mins = int(engine.config.get("interval_minutes", 60))
            interval_secs = max(60, interval_mins * 60)
            time.sleep(interval_secs)
            try:
                engine.run_cycle()
            except Exception as e:
                engine.log(f"Worker hatası: {e}")

    t = threading.Thread(target=background_worker, daemon=True)
    t.start()

    # Web Dashboard Sunucusu (Zero-dependency stdlib)
    port = cfg.get("web_port", 8080)
    WebServerHandler.engine = engine
    server = HTTPServer(("0.0.0.0", port), WebServerHandler)
    engine.log(f"TitForGit Web Arayüzü devrede: port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
