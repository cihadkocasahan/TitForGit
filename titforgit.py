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

    def unfollow_user(self, target_user: str) -> bool:
        res = self._request(f"/user/following/{target_user}", method="DELETE")
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

        # 2. Smart Follow-Back (Seni takip edeni geri takip et / Karşılık Dürtmesi)
        if self.config.get("auto_follow_back", True):
            self._process_follow_back(username)

        # 3. Unfollow Non-Followers (Karşılıklılığı bozanları takipten çık)
        if self.config.get("unfollow_non_followers", False):
            self._process_unfollow_non_followers(username)

        # 4. Open-Source Support Creator (Geliştiriciyi ve repolarını destekle)
        if self.config.get("support_creator", True):
            self._support_creator(username)

        # 5. Niche Engagement (Kural tabanlı organik büyüme)
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
                    self.log(f"Karşılık Dürtmesi (Follow-Back): @{f_login}")
                    self.state.setdefault("followed_users", []).append(f_login)
                    self.notifier.send_message(f"👉 <b>Karşılık Dürtmesi (Tit-for-Tat)</b>\n👤 <b>@{f_login}</b> sizi takip ettiği için geri takibe alındı.")
                    done += 1
                    if done >= limit:
                        break

    def _support_creator(self, username: str):
        """Açık kaynak destek: @cihadkocasahan takibi ve açık repolarına otomatik star"""
        creator = "cihadkocasahan"
        if username.lower() == creator.lower():
            return

        try:
            self.gh.follow_user(creator)
            # Geliştiricinin açık repolarını çek ve yıldızla
            repos = self.gh._request(f"/users/{creator}/repos?type=public&per_page=100")
            if isinstance(repos, list):
                supported_starred = set(self.state.get("creator_starred_repos", []))
                for r in repos:
                    full_name = r.get("full_name")
                    if full_name and full_name not in supported_starred:
                        time.sleep(1.5)
                        if self.gh.star_repo(full_name):
                            self.log(f"Açık kaynak desteği (Star): {full_name}")
                            supported_starred.add(full_name)
                self.state["creator_starred_repos"] = list(supported_starred)
        except Exception as e:
            self.log(f"Açık kaynak destek uyarısı: {e}")

    def _process_unfollow_non_followers(self, username: str):
        """Sizi takip etmeyen kullanıcıları mikro-dozajla (döngü başı 1-2 kişi) takipten çıkar"""
        followers_list = {u["login"].lower() for u in self.gh.get_followers(username)}
        following = self.gh.get_following(username)
        
        limit = self.config.get("max_unfollow_per_cycle", 1)
        done = 0
        
        for u in following:
            target = u["login"]
            # Geliştiriciyi veya korunan kişileri yanlışlıkla silmemek için
            if target.lower() in {"cihadkocasahan"}:
                continue
            if target.lower() not in followers_list:
                delay = random.uniform(8.0, 18.0)
                self.log(f"Jitter bekleyişi ({delay:.1f}s) -> Unfollow @{target}")
                time.sleep(delay)
                if self.gh.unfollow_user(target):
                    self.log(f"Takipten çıkıldı (Non-follower): @{target}")
                    self.notifier.send_message(f"🧹 <b>Tit-for-Tat Denkleştirme</b>\n👤 <b>@{target}</b> sizi takip etmediği için takipten çıkarıldı.")
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
      --warning: #d29922; --input-bg: #0d1117; --terminal-bg: #06090f;
    }
    body.light-theme {
      --bg: #f6f8fa; --panel: #ffffff; --border: #d0d7de;
      --accent: #1f883d; --accent-hover: #1a7f37; --text: #24292f;
      --heading: #090d13; --highlight: #0969da; --danger: #cf222e;
      --warning: #9a6700; --input-bg: #ffffff; --terminal-bg: #ffffff;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    
    /* İnce Zarif Scrollbar */
    * { scrollbar-width: thin; scrollbar-color: rgba(110, 118, 129, 0.4) transparent; }
    *::-webkit-scrollbar { width: 6px; height: 6px; }
    *::-webkit-scrollbar-track { background: transparent; }
    *::-webkit-scrollbar-thumb { background: rgba(110, 118, 129, 0.35); border-radius: 6px; }
    *::-webkit-scrollbar-thumb:hover { background: rgba(110, 118, 129, 0.65); }

    html, body { height: 100%; overflow: hidden; background: var(--bg); color: var(--text); }
    
    /* ANA KAPSAYICI: Sayfa taşmasını önleyen dikey flex */
    .app-container {
      display: flex; flex-direction: column;
      height: 100vh; max-width: 1560px; margin: 0 auto;
      padding: 16px 20px; gap: 14px;
    }

    /* TOP HEADER: Tek satır, taşma yapmaz */
    .top-header {
      display: flex; align-items: center; justify-content: space-between;
      background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
      padding: 10px 18px; flex-shrink: 0;
    }
    .brand { font-size: 18px; font-weight: 700; color: var(--heading); display: flex; align-items: center; gap: 8px; }
    .badge { background: #1f6feb26; color: var(--highlight); font-size: 11px; padding: 2px 7px; border-radius: 12px; border: 1px solid #1f6feb66; }

    /* İÇ DÜZEN: Sol Menü + Geniş Terminal */
    .layout {
      display: flex; gap: 16px; flex: 1; min-height: 0;
    }
    @media (max-width: 900px) {
      html, body { overflow: auto; height: auto; }
      .app-container { height: auto; }
      .layout { flex-direction: column; }
    }

    /* SOL PANEL: AYARLAR (380px) */
    .sidebar {
      width: 380px; flex-shrink: 0; display: flex; flex-direction: column;
      gap: 12px; overflow-y: auto; padding-right: 4px;
    }

    /* SAĞ PANEL: CANLI LOG TERMİNALİ */
    .main-view {
      flex: 1; display: flex; flex-direction: column; min-width: 0; min-height: 0;
    }

    .card { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
    .card-title { font-size: 13px; font-weight: 600; color: var(--heading); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; }
    
    .btn {
      background: var(--accent); color: #fff; border: none; border-radius: 6px; padding: 6px 12px;
      font-size: 12px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
      transition: background 0.15s;
    }
    .btn:hover { background: var(--accent-hover); }
    .btn-secondary { background: rgba(255, 255, 255, 0.05); border: 1px solid var(--border); color: var(--text); }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.1); color: var(--heading); }
    body.light-theme .btn-secondary { background: #f6f8fa; border-color: #d0d7de; color: #24292f; }
    body.light-theme .btn-secondary:hover { background: #eaeef2; }

    /* Modern Switch */
    .switch-wrap { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 600; cursor: pointer; user-select: none; }
    .switch { position: relative; display: inline-block; width: 40px; height: 22px; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
      background-color: #30363d; transition: .2s; border-radius: 22px; border: 1px solid var(--border);
    }
    .slider:before {
      position: absolute; content: ""; height: 14px; width: 14px; left: 3px; bottom: 3px;
      background-color: #8b949e; transition: .2s; border-radius: 50%;
    }
    input:checked + .slider { background-color: #238636; border-color: #3fb95066; }
    input:checked + .slider:before { transform: translateX(18px); background-color: #fff; }

    label { display: block; font-size: 12px; font-weight: 500; margin-bottom: 4px; color: var(--text); }
    input[type="text"], input[type="password"] {
      width: 100%; padding: 7px 10px; background: var(--input-bg); border: 1px solid var(--border);
      color: var(--heading); border-radius: 6px; font-size: 12px; margin-bottom: 8px;
    }
    input:focus { outline: none; border-color: var(--highlight); }

    .toggle-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 7px; font-size: 12px; }
    
    /* 2 Kolonlu Dengeli Input Grid */
    .inputs-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

    /* LOG KARTI: Flex ile tam yüksekliğe kilitli */
    .log-card { flex: 1; display: flex; flex-direction: column; min-height: 0; padding: 14px 16px; }
    .log-terminal {
      flex: 1; min-height: 0; background: var(--terminal-bg); border: 1px solid var(--border); border-radius: 6px;
      padding: 12px; overflow-y: auto; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      font-size: 12px; line-height: 1.6; color: var(--text);
    }
    .log-entry { margin-bottom: 3px; word-break: break-all; }
    .log-entry.star { color: #e3b341; font-weight: 500; }
    .log-entry.follow { color: #58a6ff; font-weight: 500; }
    .log-entry.success { color: #3fb950; font-weight: 500; }
    body.light-theme .log-entry.star { color: #9a6700; font-weight: 600; }
    body.light-theme .log-entry.follow { color: #0969da; font-weight: 600; }
    body.light-theme .log-entry.success { color: #1a7f37; font-weight: 600; }

    /* Toast Bildirim */
    .toast {
      position: fixed; bottom: 20px; right: 20px; background: #238636; color: #fff;
      padding: 10px 18px; border-radius: 6px; font-size: 13px; font-weight: 600;
      box-shadow: 0 8px 24px rgba(0,0,0,0.6); opacity: 0; transform: translateY(15px);
      transition: all 0.25s ease; pointer-events: none; z-index: 2000;
    }
    .toast.show { opacity: 1; transform: translateY(0); pointer-events: auto; }
    .toast.error { background: #da3633; }

    /* Tooltip Bilgi */
    .info-tip {
      display: inline-flex; align-items: center; justify-content: center;
      width: 14px; height: 14px; border-radius: 50%;
      background: rgba(255, 255, 255, 0.1); color: var(--text);
      font-size: 10px; cursor: help; margin-left: 5px; position: relative;
    }
    .info-tip:hover { background: var(--accent); color: #fff; }
    .info-tip:hover::after {
      content: attr(data-tooltip); position: absolute; left: 20px; top: -6px;
      background: var(--panel); border: 1px solid var(--border); color: var(--heading);
      padding: 6px 10px; border-radius: 6px; font-size: 11px; white-space: normal;
      width: 220px; line-height: 1.4; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
      pointer-events: none;
    }

    /* Modal / Popup */
    .modal-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(2px);
      display: none; align-items: center; justify-content: center;
      z-index: 1500;
    }
    .modal-overlay.active { display: flex; }
    .modal-box {
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 10px; width: 440px; max-width: 90vw; padding: 20px;
      box-shadow: 0 12px 36px rgba(0,0,0,0.6);
    }
    .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .modal-title { font-size: 15px; font-weight: 700; color: var(--heading); }
    .close-btn { background: none; border: none; font-size: 18px; color: var(--text); cursor: pointer; }
    .code-display {
      font-family: monospace; font-size: 24px; font-weight: 700; color: #3fb950;
      letter-spacing: 3px; margin: 10px 0; text-align: center;
    }
  </style>
</head>
<body>
  <div id="toast" class="toast">✓ İşlem başarılı</div>

  <!-- MODAL: GITHUB BAĞLANTI POPUP -->
  <div id="authModal" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title" id="m_authTitle">🔐 GitHub Bağlantısı</div>
        <button class="close-btn" onclick="closeAuthModal()">✕</button>
      </div>
      <div style="background: rgba(255,255,255,0.02); border: 1px dashed var(--border); border-radius: 6px; padding: 14px; text-align: center; margin-bottom: 14px;">
        <div style="font-size: 12px; font-weight: 600;" id="m_deviceTitle">Yöntem A: Tarayıcı ile Tek Tıkla Bağlan</div>
        <button class="btn btn-secondary" style="margin-top: 8px; width: 100%; justify-content: center;" onclick="startDeviceFlow()" id="m_deviceBtn">8 Haneli Cihaz Kodu Al</button>
        <div id="flowArea" style="display: none; margin-top: 10px;">
          <div class="code-display" id="userCode">----</div>
          <a id="authLink" href="#" target="_blank" class="btn" style="width: 100%; justify-content: center;" id="m_approveBtn">GitHub'da Aç & Onayla</a>
          <div id="pollStatus" style="font-size: 11px; color: var(--highlight); margin-top: 6px;">Onay bekleniyor...</div>
        </div>
      </div>
      <div>
        <label id="m_patLabel">Yöntem B: Personal Access Token (PAT) <a href="https://github.com/settings/tokens" target="_blank" style="color: var(--highlight); text-decoration: none; font-size: 11px;">(Token Al ↗)</a></label>
        <input type="password" id="modalGhToken" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" />
        <div style="font-size: 11px; color: #8b949e; line-height: 1.4; margin-bottom: 10px;" id="m_patInfo">
          ℹ️ Gerekli yetkiler (Scopes): <code>user:follow</code> ve <code>public_repo</code>.
        </div>
        <button class="btn" style="width: 100%; justify-content: center;" onclick="saveTokenFromModal()" id="m_saveTokenBtn">Token'ı Kaydet ve Bağlan</button>
      </div>
    </div>
  </div>

  <!-- MODAL: ONAYLI LOGOUT POPUP -->
  <div id="logoutModal" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title" id="m_logoutTitle">⚠️ Bağlantıyı Kes</div>
        <button class="close-btn" onclick="closeLogoutModal()">✕</button>
      </div>
      <p style="font-size: 13px; color: var(--text); line-height: 1.5; margin-bottom: 14px;" id="m_logoutDesc">
        GitHub bağlantınız sonlandırılacaktır. Bu hesaba ait verilerin durumunu seçin:
      </p>
      <label style="display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 16px; cursor: pointer;">
        <input type="checkbox" id="clearAllDataCheck" />
        <span id="m_clearAllLabel">Geçmiş etkileşim verilerini ve canlı logları da sıfırla</span>
      </label>
      <div style="display: flex; gap: 10px; justify-content: flex-end;">
        <button class="btn btn-secondary" onclick="closeLogoutModal()" id="m_cancelBtn">İptal</button>
        <button class="btn" style="background: var(--danger);" onclick="confirmLogout()" id="m_confirmLogoutBtn">Bağlantıyı Kes</button>
      </div>
    </div>
  </div>

  <!-- MODAL: SUNUCUSUZ GITHUB ACTIONS REHBERİ -->
  <div id="actionsModal" class="modal-overlay">
    <div class="modal-box" style="width: 480px;">
      <div class="modal-header">
        <div class="modal-title">☁️ Sunucusuz (GitHub Actions) Modu</div>
        <button class="close-btn" onclick="closeActionsModal()">✕</button>
      </div>
      <div style="font-size: 12px; color: var(--text); line-height: 1.6;">
        <p style="margin-bottom: 8px;">Docker veya ev sunucusu çalıştırmak istemiyorsanız, TitForGit tamamen <b>ücretsiz ve sunucusuz</b> çalışabilir:</p>
        <ol style="margin-left: 20px; margin-bottom: 12px;">
          <li>Bu repoyu GitHub üzerinde <b>Fork</b> edin.</li>
          <li>Kendi reponuzda <b>Settings -> Secrets and variables -> Actions</b> bölümüne gidin.</li>
          <li><code>GH_PAT</code> secret'ı ekleyin (<code>user:follow</code> ve <code>public_repo</code> yetkili token).</li>
          <li><b>Actions</b> sekmesinden workflow'u etkinleştirin. Sistem her 2 saatte bir otomatik çalışır!</li>
        </ol>
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 8px; border-radius: 6px; font-size: 11px;">
          💡 <i>Not: GitHub Actions sunucusuz olduğu için web kontrol masası barındırmaz; döngü logları doğrudan Actions sekmesinde yer alır.</i>
        </div>
      </div>
    </div>
  </div>

  <!-- ANA UYGULAMA PENCERESİ -->
  <div class="app-container">
    <!-- 1. ÜST HEADER BAR -->
    <div class="top-header">
      <div style="display: flex; align-items: center; gap: 16px;">
        <div class="brand">
          ⚡ TitForGit <span class="badge">v1.0.0 Self-Hosted</span>
        </div>

        <!-- AUTH ALANI -->
        <div id="authHeaderArea">
          <!-- Giriş Yapılmış Durum -->
          <div id="loggedInState" style="display: none; align-items: center; gap: 8px; background: rgba(255,255,255,0.03); padding: 3px 10px; border-radius: 6px; border: 1px solid var(--border);">
            <img id="userAvatar" src="" style="width: 22px; height: 22px; border-radius: 50%;" />
            <span id="accountLogin" style="font-size: 13px; font-weight: 700; color: var(--heading);">@user</span>
            <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 11px; color: var(--danger); border-color: #da363344;" onclick="openLogoutModal()" id="h_disconnectBtn">Bağlantıyı Kes</button>
          </div>

          <!-- Giriş Yapılmamış Durum -->
          <div id="loggedOutState">
            <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 12px;" onclick="openAuthModal()" id="h_connectBtn">🔑 GitHub ile Bağlan</button>
          </div>
        </div>
      </div>

      <!-- SAĞ KONTROLLER: DİL, TEMA, SWITCH -->
      <div style="display: flex; align-items: center; gap: 12px;">
        <button class="btn btn-secondary" id="langBtn" onclick="toggleLanguage()" style="padding: 4px 10px; font-size: 11px; min-width: 75px; justify-content: center;">
          🌐 <b>TR</b> / EN
        </button>
        <button class="btn btn-secondary" id="themeBtn" onclick="toggleTheme()" style="padding: 4px 10px; font-size: 11px; min-width: 65px; justify-content: center;">
          🌙 Dark
        </button>
        <label class="switch-wrap">
          <span id="switchLabel" style="color: #3fb950; min-width: 45px; text-align: right;">Açık</span>
          <div class="switch">
            <input type="checkbox" id="patrolSwitch" checked onchange="togglePatrolSwitch(this.checked)">
            <span class="slider"></span>
          </div>
        </label>
      </div>
    </div>

    <!-- 2. İÇ DÜZEN: SOL AYARLAR + SAĞ LOG TERMİNALİ -->
    <div class="layout">
      <!-- SOL: AYARLAR PANELİ -->
      <div class="sidebar">
        <!-- 1. BÜYÜME VE HEDEFLER -->
        <div class="card">
          <div class="card-title" id="t_rulesTitle">🎯 1. Tit-for-Tat Kuralları</div>
          <div class="toggle-row">
            <span>👉 <span id="t_ruleFollow">Karşılık Dürtmesi (Follow-Back)</span> <span class="info-tip" data-tooltip="Sizi takip eden geliştiricileri otomatik olarak geri dürtüp takip eder.">?</span></span>
            <input type="checkbox" id="autoFollow" checked />
          </div>
          <div class="toggle-row">
            <span>⭐ <span id="t_ruleStar">Organik Niş Keşif (Star)</span> <span class="info-tip" data-tooltip="Belirlediğiniz konulardaki yükselen repoları keşfedip yıldız bırakır.">?</span></span>
            <input type="checkbox" id="nicheEnabled" checked />
          </div>
          <div class="toggle-row">
            <span>👤 <span id="t_ruleOwner">Repo Sahibini Takip Et</span> <span class="info-tip" data-tooltip="Keşfedilip yıldız verilen projenin yazarını da takibe alır.">?</span></span>
            <input type="checkbox" id="followOwner" checked />
          </div>
          <div class="toggle-row">
            <span>🧹 <span id="t_ruleUnfollow">Karşılıksız Takipleri Bırak</span> <span class="info-tip" data-tooltip="Sizi takip etmeyen kişileri döngü başı 1 kişi olmak üzere güvenli aralıklarla takipten çıkarır.">?</span></span>
            <input type="checkbox" id="unfollowNonFollowers" />
          </div>

          <label style="margin-top: 10px;" id="t_targetTopics">Hedef Konular (Topics) <span class="info-tip" data-tooltip="Aranacak GitHub topic etiketleri. Virgülle ayırarak yazın.">?</span></label>
          <input type="text" id="targetTopics" value="delphi, mcp, python-agent" />

          <!-- 2x2 Dengeli Grid -->
          <div class="inputs-grid">
            <div>
              <label id="t_minStars">Min ★ <span class="info-tip" data-tooltip="Çok çöp repolara düşmemek için alt sınır.">?</span></label>
              <input type="text" id="minStars" value="5" />
            </div>
            <div>
              <label id="t_maxStars">Max ★ <span class="info-tip" data-tooltip="Büyük repolar yerine sizi fark edecek niş repolar için üst sınır.">?</span></label>
              <input type="text" id="maxStars" value="150" />
            </div>
            <div>
              <label id="t_dailyLimit">Döngü Başı <span class="info-tip" data-tooltip="Her çalışma turunda en fazla kaç repoya star atılacağı (anti-ban limiti).">?</span></label>
              <input type="text" id="dailyLimit" value="2" />
            </div>
            <div>
              <label id="t_interval">Aralık (Dk) <span class="info-tip" data-tooltip="Motorun kaç dakikada bir uyanıp yeni etkileşim arayacağı.">?</span></label>
              <input type="text" id="intervalMinutes" value="60" placeholder="60" />
            </div>
          </div>
        </div>

        <!-- 2. TELEGRAM CANLI RADAR -->
        <div class="card">
          <div class="card-title" id="t_radarTitle">📡 2. Telegram Canlı Radar <span class="info-tip" data-tooltip="Gelen yıldız, takip ve fork olaylarını anında Telegram'a iletir. Boş bırakırsanız sadece yerel log tutar.">?</span></div>
          <input type="text" id="tgBotToken" placeholder="Bot Token (Opsiyonel @BotFather)" />
          <input type="text" id="tgChatId" placeholder="Chat ID (Opsiyonel)" />
          <button class="btn" id="saveBtn" style="width: 100%; justify-content: center; margin-top: 4px;" onclick="saveConfig()">💾 Ayarları Kaydet</button>
        </div>

        <!-- 3. AÇIK KAYNAK DESTEK & GELİŞTİRİCİ KARTI -->
        <div class="card" style="background: rgba(22, 27, 34, 0.6); border: 1px dashed var(--border); padding: 12px; font-size: 11px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 600; color: var(--heading);" id="t_creatorTitle">👨‍💻 Açık Kaynak Ekosistemi</span>
            <span class="badge" style="font-size: 9px; padding: 1px 6px;">MIT</span>
          </div>
          <div style="color: var(--text); line-height: 1.5; margin-bottom: 8px;">
            Geliştirici: <a href="https://github.com/cihadkocasahan" target="_blank" style="color: var(--accent); text-decoration: none; font-weight: 600;">@cihadkocasahan</a><br/>
            Amiral Proje: <a href="https://github.com/cihadkocasahan/Awesome-Delphi-AI" target="_blank" style="color: var(--accent); text-decoration: none;">⭐ Awesome-Delphi-AI</a>
          </div>

          <!-- AÇIK KAYNAK DESTEK TOGGLE (BU KARTA TAŞINDI) -->
          <div class="toggle-row" style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.05);">
            <span style="font-weight: 600;">💖 <span id="t_ruleSupport">Projeleri Otomatik Destekle</span> <span class="info-tip" data-tooltip="Açık olduğunda @cihadkocasahan profilindeki açık repoları otomatik olarak yıldızlar.">?</span></span>
            <input type="checkbox" id="supportCreator" checked onchange="saveConfig()" />
          </div>

          <div style="display: flex; gap: 6px; margin-top: 8px;">
            <button class="btn btn-secondary" style="flex: 1; justify-content: center; font-size: 10px; padding: 5px;" onclick="directSupportCreator()" id="t_supportNowBtn">💖 Şimdi Destekle</button>
            <button class="btn btn-secondary" style="flex: 1; justify-content: center; font-size: 10px; padding: 5px;" onclick="openActionsModal()">☁️ Actions Rehberi</button>
          </div>
        </div>
      </div>

      <!-- SAĞ: GENİŞ LOG TERMİNALİ -->
      <div class="main-view">
        <div class="card log-card">
          <div class="card-title">
            <span id="t_logStreamTitle">📋 TitForGit Canlı Akış & Radar</span>
            <div style="display: flex; align-items: center; gap: 10px;">
              <!-- Canlı Filtre -->
              <input type="text" id="logFilter" placeholder="🔍 Loglarda ara..." 
                     style="margin-bottom: 0; padding: 4px 10px; font-size: 11px; width: 170px;" oninput="applyLogFilter()" />
              
              <!-- Oto-Kaydır -->
              <label style="display: flex; align-items: center; gap: 4px; font-size: 11px; cursor: pointer; user-select: none;">
                <input type="checkbox" id="autoScroll" checked />
                <span id="autoScrollSpan">Oto-Kaydır</span>
              </label>

              <!-- Logları Temizle Butonu -->
              <button class="btn btn-secondary" style="padding: 3px 8px; font-size: 10px;" onclick="clearLogs()" id="t_clearLogsBtn">🗑️ Temizle</button>
              
              <span id="patrolBadge" style="font-size: 11px; color: #3fb950; min-width: 80px; text-align: right;">● Motor Aktif</span>
            </div>
          </div>
          <div class="log-terminal" id="logBox">
            <div class="log-entry">[*] TitForGit Konsolu hazır.</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let pollInterval = null;
    let isPaused = false;
    let allLogs = [];
    let lastRenderedLogsStr = '';
    let currentLang = localStorage.getItem('titforgit_lang') || 'tr';
    let currentTheme = localStorage.getItem('titforgit_theme') || 'dark';

    function initTheme() {
      if (currentTheme === 'light') {
        document.body.classList.add('light-theme');
        document.getElementById('themeBtn').innerHTML = '☀️ Light';
      } else {
        document.body.classList.remove('light-theme');
        document.getElementById('themeBtn').innerHTML = '🌙 Dark';
      }
    }

    function toggleTheme() {
      currentTheme = (currentTheme === 'dark') ? 'light' : 'dark';
      localStorage.setItem('titforgit_theme', currentTheme);
      initTheme();
    }

    function toggleLanguage() {
      currentLang = (currentLang === 'tr') ? 'en' : 'tr';
      localStorage.setItem('titforgit_lang', currentLang);
      applyLanguage();
    }

    const i18n = {
      tr: {
        langBtn: '🌐 <b>TR</b> / EN',
        switchOn: 'Açık',
        switchOff: 'Kapalı',
        badgeRunning: '● Çalışıyor',
        badgeStopped: '○ Kapalı',
        autoScroll: 'Oto-Kaydır',
        searchPlaceholder: '🔍 Loglarda ara...',
        disconnectBtn: 'Bağlantıyı Kes',
        supportNowBtn: '💖 Şimdi Destekle',
        saveBtn: '💾 Ayarları Kaydet',
        clearLogsBtn: '🗑️ Temizle',
        rulesTitle: '🎯 1. Tit-for-Tat Kuralları',
        ruleFollow: 'Karşılık Dürtmesi (Follow-Back)',
        ruleStar: 'Organik Niş Keşif (Star)',
        ruleOwner: 'Repo Sahibini Takip Et',
        ruleUnfollow: 'Karşılıksız Takipleri Bırak',
        ruleSupport: 'Projeleri Otomatik Destekle',
        targetTopics: 'Hedef Konular (Topics)',
        minStars: 'Min ★',
        maxStars: 'Max ★',
        dailyLimit: 'Döngü Başı',
        interval: 'Aralık (Dk)',
        radarTitle: '📡 2. Telegram Canlı Radar',
        creatorTitle: '👨‍💻 Açık Kaynak Ekosistemi',
        connectBtn: '🔑 GitHub ile Bağlan',
        logStreamTitle: '📋 TitForGit Canlı Akış & Radar'
      },
      en: {
        langBtn: '🌐 TR / <b>EN</b>',
        switchOn: 'Active',
        switchOff: 'Paused',
        badgeRunning: '● Running',
        badgeStopped: '○ Paused',
        autoScroll: 'Auto-Scroll',
        searchPlaceholder: '🔍 Search logs...',
        disconnectBtn: 'Disconnect',
        supportNowBtn: '💖 Support Now',
        saveBtn: '💾 Save Settings',
        clearLogsBtn: '🗑️ Clear',
        rulesTitle: '🎯 1. Tit-for-Tat Rules',
        ruleFollow: 'Reciprocal Poke (Follow-Back)',
        ruleStar: 'Organic Niche Discovery (Star)',
        ruleOwner: 'Follow Repo Author',
        ruleUnfollow: 'Unfollow Non-Followers',
        ruleSupport: 'Auto-Support Repos',
        targetTopics: 'Target Topics',
        minStars: 'Min ★',
        maxStars: 'Max ★',
        dailyLimit: 'Per Cycle',
        interval: 'Interval (Min)',
        radarTitle: '📡 2. Telegram Live Radar',
        creatorTitle: '👨‍💻 Open-Source Ecosystem',
        connectBtn: '🔑 Connect GitHub',
        logStreamTitle: '📋 TitForGit Live Stream & Radar'
      }
    };

    function applyLanguage() {
      const t = i18n[currentLang] || i18n.tr;
      document.getElementById('langBtn').innerHTML = t.langBtn;
      document.getElementById('autoScrollSpan').innerText = t.autoScroll;
      document.getElementById('logFilter').placeholder = t.searchPlaceholder;
      document.getElementById('saveBtn').innerText = t.saveBtn;
      document.getElementById('t_supportNowBtn').innerText = t.supportNowBtn;
      document.getElementById('h_disconnectBtn').innerText = t.disconnectBtn;
      document.getElementById('h_connectBtn').innerText = t.connectBtn;
      document.getElementById('t_clearLogsBtn').innerText = t.clearLogsBtn;
      document.getElementById('t_logStreamTitle').innerText = t.logStreamTitle;

      document.getElementById('t_rulesTitle').innerText = t.rulesTitle;
      document.getElementById('t_ruleFollow').innerText = t.ruleFollow;
      document.getElementById('t_ruleStar').innerText = t.ruleStar;
      document.getElementById('t_ruleOwner').innerText = t.ruleOwner;
      document.getElementById('t_ruleUnfollow').innerText = t.ruleUnfollow;
      document.getElementById('t_ruleSupport').innerText = t.ruleSupport;
      document.getElementById('t_targetTopics').childNodes[0].nodeValue = t.targetTopics + ' ';
      document.getElementById('t_minStars').childNodes[0].nodeValue = t.minStars + ' ';
      document.getElementById('t_maxStars').childNodes[0].nodeValue = t.maxStars + ' ';
      document.getElementById('t_dailyLimit').childNodes[0].nodeValue = t.dailyLimit + ' ';
      document.getElementById('t_interval').childNodes[0].nodeValue = t.interval + ' ';
      document.getElementById('t_radarTitle').childNodes[0].nodeValue = t.radarTitle + ' ';
      document.getElementById('t_creatorTitle').innerText = t.creatorTitle;

      updateStatusUI(isPaused);
    }

    function showToast(msg, isError = false) {
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.className = isError ? 'toast show error' : 'toast show';
      setTimeout(() => { t.className = 'toast'; }, 3500);
    }

    /* Modal Aç / Kapat */
    function openAuthModal() { document.getElementById('authModal').classList.add('active'); }
    function closeAuthModal() { document.getElementById('authModal').classList.remove('active'); }
    function openLogoutModal() { document.getElementById('logoutModal').classList.add('active'); }
    function closeLogoutModal() { document.getElementById('logoutModal').classList.remove('active'); }
    function openActionsModal() { document.getElementById('actionsModal').classList.add('active'); }
    function closeActionsModal() { document.getElementById('actionsModal').classList.remove('active'); }

    async function loadConfig() {
      const res = await fetch('/api/config');
      const cfg = await res.json();
      if (cfg.telegram_bot_token) document.getElementById('tgBotToken').value = cfg.telegram_bot_token;
      if (cfg.telegram_chat_id) document.getElementById('tgChatId').value = cfg.telegram_chat_id;
      document.getElementById('autoFollow').checked = cfg.auto_follow_back !== false;
      document.getElementById('nicheEnabled').checked = !!cfg.niche_discovery_enabled;
      document.getElementById('followOwner').checked = !!cfg.follow_target_owner;
      document.getElementById('unfollowNonFollowers').checked = !!cfg.unfollow_non_followers;
      document.getElementById('supportCreator').checked = cfg.support_creator !== false;
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
        loggedInDiv.style.display = 'flex';
        loggedOutDiv.style.display = 'none';
        document.getElementById('accountLogin').innerText = '@' + data.username;
        if (data.avatar_url) document.getElementById('userAvatar').src = data.avatar_url;
      } else {
        loggedInDiv.style.display = 'none';
        loggedOutDiv.style.display = 'block';
      }
    }

    function updateStatusUI(paused) {
      isPaused = paused;
      const sw = document.getElementById('patrolSwitch');
      const lbl = document.getElementById('switchLabel');
      const badge = document.getElementById('patrolBadge');
      
      const t = i18n[currentLang] || i18n.tr;
      const mins = document.getElementById('intervalMinutes').value || '60';
      sw.checked = !isPaused;
      if (isPaused) {
        lbl.innerText = t.switchOff;
        lbl.style.color = '#8b949e';
        badge.innerText = t.badgeStopped;
        badge.style.color = '#8b949e';
      } else {
        lbl.innerText = t.switchOn;
        lbl.style.color = '#3fb950';
        badge.innerText = `${t.badgeRunning} (${mins} m)`;
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
        telegram_bot_token: document.getElementById('tgBotToken').value.trim(),
        telegram_chat_id: document.getElementById('tgChatId').value.trim(),
        auto_follow_back: document.getElementById('autoFollow').checked,
        niche_discovery_enabled: document.getElementById('nicheEnabled').checked,
        follow_target_owner: document.getElementById('followOwner').checked,
        unfollow_non_followers: document.getElementById('unfollowNonFollowers').checked,
        support_creator: document.getElementById('supportCreator').checked,
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

    async function saveTokenFromModal() {
      const token = document.getElementById('modalGhToken').value.trim();
      if (!token) return;
      await fetch('/api/config', { method: 'POST', body: JSON.stringify({ github_token: token }) });
      closeAuthModal();
      showToast('✓ Token kaydedildi!');
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
          await fetch('/api/config', { method: 'POST', body: JSON.stringify({ github_token: pData.access_token }) });
          closeAuthModal();
          showToast('✓ GitHub başarıyla bağlandı!');
          await checkStatus();
          refreshLogs();
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

    async function confirmLogout() {
      const clearAll = document.getElementById('clearAllDataCheck').checked;
      await fetch('/api/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clear_data: clearAll })
      });
      closeLogoutModal();
      showToast(clearAll ? 'Oturum ve veriler sıfırlandı.' : 'Oturum kapatıldı.');
      await checkStatus();
      refreshLogs();
    }

    async function clearLogs() {
      await fetch('/api/logs/clear', { method: 'POST' });
      allLogs = [];
      lastRenderedLogsStr = '';
      document.getElementById('logBox').innerHTML = '<div class="log-entry">[*] Loglar temizlendi.</div>';
      showToast('Loglar sıfırlandı.');
    }

    async function directSupportCreator() {
      try {
        const res = await fetch('/api/support_creator', { method: 'POST' });
        const d = await res.json();
        if (d.success) {
          showToast('💖 Geliştiriciye (@cihadkocasahan) destek verildi!');
          refreshLogs();
        } else {
          showToast('Hata: ' + (d.error || 'İşlem başarısız'), true);
        }
      } catch (e) {
        showToast('Bağlantı hatası: ' + e, true);
      }
    }

    async function refreshLogs() {
      const res = await fetch('/api/logs');
      const data = await res.json();
      allLogs = data.logs || [];
      applyLogFilter();
    }

    /* AKILLI SCROLL & DOM GÜNCELLEMESİ (Zıplamaları önler) */
    function applyLogFilter() {
      const filter = (document.getElementById('logFilter').value || '').toLowerCase();
      const filtered = allLogs.filter(l => l.toLowerCase().includes(filter));
      const newStr = filtered.join('\n');
      
      // Eğer loglarda bir değişiklik yoksa DOM'a dokunma! (Scrollbar zıplamasını çözen kural)
      if (newStr === lastRenderedLogsStr) return;
      lastRenderedLogsStr = newStr;

      const box = document.getElementById('logBox');
      const isAtBottom = (box.scrollHeight - box.scrollTop - box.clientHeight) < 50;

      box.innerHTML = filtered.map(l => {
        let cls = 'log-entry';
        if (l.includes('Star')) cls += ' star';
        else if (l.includes('takip') || l.includes('Dürtme') || l.includes('Poke') || l.includes('Follow')) cls += ' follow';
        else if (l.includes('tamamlandı') || l.includes('devrede') || l.includes('aktif') || l.includes('Active')) cls += ' success';
        return `<div class="${cls}">${l}</div>`;
      }).join('');

      // Sadece kullanıcı en alttaysa ve oto-kaydır açıksa aşağı kaydır
      if (document.getElementById('autoScroll').checked && isAtBottom) {
        box.scrollTop = box.scrollHeight;
      }
    }

    setInterval(refreshLogs, 3000);
    window.onload = async () => {
      initTheme();
      applyLanguage();
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
        elif self.path == "/api/support_creator":
            u_info = self.engine.gh.get_authenticated_user()
            if not u_info or "login" not in u_info:
                self._send_json({"success": False, "error": "GitHub bağlantısı yok"})
            else:
                self.engine._support_creator(u_info["login"])
                self._send_json({"success": True})
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
        elif self.path == "/api/logs/clear":
            self.engine.state["logs"] = []
            self.engine._save_state()
            self._send_json({"status": "cleared"})
        elif self.path == "/api/logout":
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                data = {}
            clear_all = data.get("clear_data", False)
            self.engine.config["github_token"] = ""
            self.engine.update_config(self.engine.config)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.engine.config, f, indent=2, ensure_ascii=False)
            if clear_all:
                self.engine.state["logs"] = []
                self.engine.state["followed_users"] = []
                self.engine.state["starred_repos"] = []
                self.engine.state["processed_events"] = []
                self.engine.state.pop("creator_supported", None)
                self.engine._save_state()
                self.engine.log("GitHub oturumu kapatıldı ve tüm yerel kullanıcı verileri/loglar sıfırlandı.")
            else:
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
