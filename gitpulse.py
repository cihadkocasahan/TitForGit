#!/usr/bin/env python3
"""
GitPulse - Core Engine
Autonomous GitHub Community & Growth Engine.
Zero external dependencies (Pure Python Standard Library).
Supports both local Docker loop and GitHub Actions single-shot execution.
"""

import os
import sys
import json
import time
import random
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

STATE_FILE = os.getenv("GITPULSE_STATE_FILE", "gitpulse_state.json")

class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitPulse-Autonomous-Engine/1.0"
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

    def get_user_repos(self, username: str):
        return self._request(f"/users/{username}/repos?per_page=100&sort=pushed") or []

    def get_user_events(self, username: str):
        return self._request(f"/users/{username}/events?per_page=30") or []

    def get_followers(self, username: str) -> list[dict]:
        res = self._request(f"/users/{username}/followers?per_page=100")
        return res if isinstance(res, list) else []

    def get_following(self, username: str) -> list[dict]:
        res = self._request(f"/users/{username}/following?per_page=100")
        return res if isinstance(res, list) else []

    def is_following(self, target_user: str) -> bool:
        res = self._request(f"/user/following/{target_user}")
        return res is not None

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


class GitPulseEngine:
    def __init__(self, config: dict):
        self.config = config
        self.gh = GitHubClient(config["github_token"])
        self.notifier = TelegramNotifier(
            config.get("telegram_bot_token", ""),
            config.get("telegram_chat_id", "")
        )
        self.state = self._load_state()

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
            "last_run": None
        }

    def _save_state(self):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[!] State kaydetme hatası: {e}")

    def run_cycle(self):
        user_info = self.gh.get_authenticated_user()
        if not user_info or "login" not in user_info:
            print("[x] GitHub token geçersiz veya yetkisiz.")
            return

        username = user_info["login"]
        print(f"[*] GitPulse çalışıyor: @{username}")
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
        print("[✓] Döngü tamamlandı.")

    def _check_radar_events(self, username: str):
        raw_events = self.gh.get_user_events(username)
        events = raw_events if isinstance(raw_events, list) else []
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
                msg = f"⭐ <b>Yeni GitHub Star!</b>\n👤 <b>{actor}</b> kullanıcısı <code>{repo_name}</code> reposuna star verdi."
            elif ev_type == "ForkEvent":
                fork_repo = ev.get("payload", {}).get("forkee", {}).get("full_name", "")
                msg = f"🍴 <b>Yeni Fork!</b>\n👤 <b>{actor}</b>, <code>{repo_name}</code> reposunu çatalladı: <code>{fork_repo}</code>"
            elif ev_type == "IssuesEvent" and ev.get("payload", {}).get("action") == "opened":
                issue_title = ev.get("payload", {}).get("issue", {}).get("title", "")
                msg = f"📌 <b>Yeni Issue!</b>\n👤 <b>{actor}</b> -> <code>{repo_name}</code>\nBaşlık: <i>{issue_title}</i>"

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
                    print(f"[+] Geri takip edildi: {f_login}")
                    self.state.setdefault("followed_users", []).append(f_login)
                    self.notifier.send_message(f"🤝 <b>Geri Takip Yapıldı</b>\n👤 <b>{f_login}</b> sizi takip ettiği için otomatik geri takibe alındı.")
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
            print(f"[*] Jitter gecikmesi ({delay:.1f}s)...")
            time.sleep(delay)

            if self.gh.star_repo(full_name):
                print(f"[★] Star bırakıldı: {full_name}")
                self.state.setdefault("starred_repos", []).append(full_name)
                
                # Opsiyonel geliştirici takibi
                if self.config.get("follow_target_owner", False):
                    self.gh.follow_user(owner)
                    self.state.setdefault("followed_users", []).append(owner)

                self.notifier.send_message(
                    f"🎯 <b>Organik Keşif Etkileşimi</b>\n"
                    f"📦 Repo: <code>{full_name}</code> (★ {r['stargazers_count']})\n"
                    f"🏷 Konu: <code>{selected_topic}</code>\n"
                    f"👤 Geliştirici: <b>{owner}</b>"
                )
                count += 1
                if count >= daily_limit:
                    break


def load_config() -> dict:
    config = {
        "github_token": os.getenv("GITHUB_TOKEN", ""),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "auto_follow_back": os.getenv("AUTO_FOLLOW_BACK", "true").lower() == "true",
        "niche_discovery_enabled": os.getenv("NICHE_DISCOVERY_ENABLED", "false").lower() == "true",
        "target_topics": [t.strip() for t in os.getenv("TARGET_TOPICS", "").split(",") if t.strip()],
        "min_stars": int(os.getenv("MIN_STARS", "5")),
        "max_stars": int(os.getenv("MAX_STARS", "150")),
        "daily_star_limit": int(os.getenv("DAILY_STAR_LIMIT", "3")),
        "follow_target_owner": os.getenv("FOLLOW_TARGET_OWNER", "false").lower() == "true",
        "max_follow_back_per_cycle": int(os.getenv("MAX_FOLLOW_BACK_PER_CYCLE", "2"))
    }
    config_file = os.getenv("CONFIG_FILE", "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_cfg = json.load(f)
                config.update(file_cfg)
        except Exception as e:
            print(f"[!] config.json okunamadı: {e}")
    return config


if __name__ == "__main__":
    cfg = load_config()
    if not cfg["github_token"]:
        print("[x] HATA: GITHUB_TOKEN tanımlı değil (.env, config.json veya environment).")
        sys.exit(1)

    engine = GitPulseEngine(cfg)

    # Sürekli daemon modu mu yoksa tek seferlik cron işi mi?
    run_mode = os.getenv("RUN_MODE", "cron").lower()
    if run_mode == "daemon":
        interval = int(os.getenv("INTERVAL_SECONDS", "3600"))
        print(f"[*] GitPulse Daemon modunda başlatıldı (Aralık: {interval}s)")
        while True:
            try:
                engine.run_cycle()
            except Exception as e:
                print(f"[!] Döngü hatası: {e}")
            time.sleep(interval)
    else:
        # Tek seferlik çalıştır ve çık (GitHub Actions / Cron modu)
        engine.run_cycle()
