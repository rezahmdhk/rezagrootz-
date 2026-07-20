[file name]: main.py
[file content begin]
import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    Message, CallbackQuery, ChatMemberUpdated
)
import time
import random
import re
import json
import threading
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import hashlib
import os
import string
import asyncio
import aiohttp
from urllib.parse import urlparse

# ========== تنظیمات ==========
BOT_TOKEN = "8810741889:AAF9h94CG7dmkvJRd3SHNH1npwezAi2wQ1A"
ADMIN_IDS = [8916314219]
bot = telebot.TeleBot(BOT_TOKEN)

# ========== لاگینگ ==========
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ========== دیتابیس SQLite ==========
class Database:
    def __init__(self, db_file='bot_data.db'):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                settings TEXT,
                rules TEXT,
                welcome_text TEXT,
                welcome_photo TEXT,
                created_at INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                level INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                muted_until INTEGER DEFAULT 0,
                banned_until INTEGER DEFAULT 0,
                verified INTEGER DEFAULT 0,
                join_date INTEGER DEFAULT 0,
                last_activity INTEGER DEFAULT 0,
                referral_code TEXT,
                referred_by INTEGER,
                referral_count INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                strike_count INTEGER DEFAULT 0,
                warnings_data TEXT,
                achievements TEXT,
                notes TEXT,
                is_admin INTEGER DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                last_daily INTEGER DEFAULT 0,
                twofa_code TEXT,
                twofa_expiry INTEGER DEFAULT 0,
                is_2fa_verified INTEGER DEFAULT 0,
                afk_status TEXT DEFAULT '',
                afk_time INTEGER DEFAULT 0,
                is_afk INTEGER DEFAULT 0,
                afk_reply_count INTEGER DEFAULT 0,
                last_voice INTEGER DEFAULT 0,
                voice_xp INTEGER DEFAULT 0,
                total_voice_time INTEGER DEFAULT 0,
                warning_points INTEGER DEFAULT 0,
                is_trusted INTEGER DEFAULT 0,
                trust_score INTEGER DEFAULT 50
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                time INTEGER,
                admin_id INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                subject TEXT,
                status TEXT DEFAULT 'open',
                time INTEGER,
                messages TEXT,
                assigned_admin INTEGER,
                priority TEXT DEFAULT 'normal'
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS captcha (
                user_id INTEGER PRIMARY KEY,
                group_id INTEGER,
                answer INTEGER,
                attempts INTEGER DEFAULT 0,
                time INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                reported_user_id INTEGER,
                reporter_user_id INTEGER,
                reason TEXT,
                time INTEGER,
                status TEXT DEFAULT 'pending',
                evidence TEXT DEFAULT ''
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                time INTEGER,
                UNIQUE(group_id, user_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                time INTEGER,
                UNIQUE(group_id, user_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                trigger TEXT,
                response TEXT,
                type TEXT DEFAULT 'text',
                is_regex INTEGER DEFAULT 0,
                cooldown INTEGER DEFAULT 0,
                last_used INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                message TEXT,
                time INTEGER,
                status TEXT DEFAULT 'pending'
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                question TEXT,
                options TEXT,
                votes TEXT,
                time INTEGER,
                status TEXT DEFAULT 'active',
                is_anonymous INTEGER DEFAULT 1,
                multiple_choice INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                name TEXT,
                description TEXT,
                start_time INTEGER,
                end_time INTEGER,
                participants TEXT,
                winner_id INTEGER,
                status TEXT DEFAULT 'active',
                prize TEXT DEFAULT '',
                max_participants INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_rewards (
                user_id INTEGER,
                date TEXT,
                claimed INTEGER DEFAULT 0,
                bonus_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS economy (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                last_work INTEGER DEFAULT 0,
                last_rob INTEGER DEFAULT 0,
                job TEXT DEFAULT 'بی‌کار',
                job_level INTEGER DEFAULT 1,
                total_earned INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                name TEXT,
                price INTEGER,
                description TEXT,
                stock INTEGER DEFAULT -1,
                category TEXT DEFAULT 'general'
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_inventory (
                user_id INTEGER,
                item_id INTEGER,
                quantity INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, item_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS marriages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                married_date INTEGER,
                status TEXT DEFAULT 'active',
                love_score INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS family (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                child_id INTEGER,
                relationship TEXT DEFAULT 'father',
                status TEXT DEFAULT 'active'
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                name TEXT,
                description TEXT,
                date INTEGER,
                creator_id INTEGER,
                status TEXT DEFAULT 'upcoming'
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                context TEXT,
                last_updated INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_statistics (
                group_id INTEGER,
                date TEXT,
                active_users INTEGER DEFAULT 0,
                messages_count INTEGER DEFAULT 0,
                PRIMARY KEY (group_id, date)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_badges (
                user_id INTEGER,
                badge_id TEXT,
                earned_date INTEGER,
                PRIMARY KEY (user_id, badge_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS word_filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                word TEXT,
                action TEXT DEFAULT 'delete',
                UNIQUE(group_id, word)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                role TEXT DEFAULT 'member',
                color TEXT DEFAULT '#000000',
                permissions TEXT,
                UNIQUE(group_id, user_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                message TEXT,
                scheduled_time INTEGER,
                status TEXT DEFAULT 'pending',
                is_recurring INTEGER DEFAULT 0,
                interval_type TEXT DEFAULT 'daily'
            )
        ''')
        self.conn.commit()
    
    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor
    
    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()
    
    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def close(self):
        self.conn.close()

db = Database()

# ========== دیتابیس فوق‌پیشرفته ==========
class UltraDatabase:
    def __init__(self):
        self.db = db
        self.default_settings = {
            "welcome": "👋 به گروه خوش آمدید {user_name}! لطفاً قوانین را رعایت کنید.",
            "welcome_enabled": True,
            "welcome_photo": None,
            "captcha": True,
            "captcha_timeout": 60,
            "captcha_max_attempts": 3,
            "auto_delete": True,
            "auto_delete_seconds": 43200,
            "anti_spam": True,
            "spam_threshold": 3,
            "spam_action": "mute",
            "spam_duration": 300,
            "anti_raid": True,
            "raid_threshold": 5,
            "raid_action": "kick",
            "anti_mentions": True,
            "mention_limit": 3,
            "anti_caps": True,
            "caps_limit": 70,
            "anti_emoji": True,
            "emoji_limit": 5,
            "anti_newlines": True,
            "newline_limit": 5,
            "anti_forward": True,
            "forward_limit": 3,
            "anti_link": True,
            "anti_link_action": "warn",
            "anti_link_whitelist": ["youtube.com", "youtu.be", "instagram.com", "telegram.me"],
            "anti_bad_words": True,
            "anti_bad_words_action": "mute",
            "anti_bad_words_duration": 600,
            "anti_advertising": True,
            "anti_advertising_action": "kick",
            "anti_bot": True,
            "anti_bot_action": "ban",
            "anti_commands": True,
            "anti_commands_list": ["/ban", "/kick", "/mute", "/warn", "/add", "/delete"],
            "group_lock": False,
            "leveling": True,
            "level_message": "🎉 {user_name} به سطح {level} رسید!",
            "rules": "📋 قوانین گروه:\n1. احترام به یکدیگر\n2. بدون اسپم و تبلیغات\n3. رعایت ادب و اخلاق\n4. بدون ارسال محتوای نامناسب\n5. همراهی با مدیریت",
            "warn_limit": 3,
            "warn_action": "mute",
            "warn_duration": 3600,
            "max_warn_reset": 86400,
            "silent_mode": False,
            "button_access_locked": True,
            "anti_spam_bayesian": True,
            "spam_probability_threshold": 0.6,
            "anti_porn": True,
            "anti_violence": True,
            "anti_drugs": True,
            "anti_hate": True,
            "anti_phishing": True,
            "anti_malware": True,
            "anti_terrorism": True,
            "anti_child_abuse": True,
            "anti_crypto": True,
            "anti_gambling": True,
            "anti_url_shortener": True,
            "anti_phone": True,
            "anti_email": True,
            "auto_ban_on_three_warnings": True,
            "two_factor_auth": False,
            "daily_reward": True,
            "daily_reward_amount": 10,
            "auto_backup": True,
            "backup_interval": 86400,
            "scan_media": True,
            "malicious_domains": ["bit.ly", "tinyurl", "goo.gl", "ow.ly", "is.gd", "buff.ly", "adf.ly", "shorte.st", "cutt.ly", "rebrand.ly", "short.link"],
            "sensitivity_level": "normal",
            "duplicate_message_detection": True,
            "duplicate_time_window": 10,
            "duplicate_threshold": 2,
            "auto_report_to_admins": True,
            "afk_enabled": True,
            "voice_xp_enabled": True,
            "trust_system_enabled": True,
            "trust_threshold": 30,
            "word_filter_enabled": True,
            "smart_reply_enabled": True,
            "smart_reply_confidence": 0.7,
            "economy_enabled": True,
            "marriage_enabled": True,
            "family_enabled": True,
            "group_events_enabled": True,
            "scheduled_messages_enabled": True,
            "badge_system_enabled": True,
            "role_system_enabled": True,
            "ai_assistant_enabled": True,
            "ai_api_key": "",
            "auto_moderation_level": "medium",
            "toxicity_filter_enabled": True,
            "toxicity_threshold": 0.6,
            "language_filter_enabled": True,
            "allowed_languages": ["fa", "en"],
            "spam_detection_ml": True,
            "user_trust_minimum": 10,
            "auto_role_assign": True,
            "new_user_role": "member",
            "daily_bonus_multiplier": 1.0,
            "weekend_bonus": True,
            "voice_chat_reward": 5,
            "max_voice_xp_per_day": 100,
            "referral_reward": 50,
            "referral_required": 1,
            "economy_work_cooldown": 3600,
            "economy_rob_cooldown": 7200,
            "marriage_cooldown": 86400,
            "divorce_cost": 100,
            "max_family_members": 10,
            "event_reminder_time": 3600,
            "ai_conversation_timeout": 300,
            "auto_cleanup_interval": 3600,
            "max_group_stats_days": 30,
            "achievement_notification": True,
            "level_up_animation": True,
            "custom_commands_enabled": True,
            "dynamic_welcome": True,
            "welcome_variants": [],
            "goodbye_enabled": True,
            "goodbye_message": "👋 {user_name} از گروه خارج شد. خوشحال بودیم که بودی!",
            "anti_ghost_ping": True,
            "ghost_ping_action": "warn",
            "anti_web3_scam": True,
            "anti_fake_telegram": True,
            "anti_self_destruct": True,
            "anti_voice_scam": True,
            "proactive_security": True,
            "instant_ban_on_suspicious": True,
            "deep_link_analysis": True,
            "behavioral_analysis": True,
            "anomaly_detection": True,
            "pattern_recognition": True,
            "ai_content_analysis": True,
            "sentiment_analysis": True,
            "community_health_monitor": True,
            "auto_healing": True,
            "performance_optimizer": True
        }
        self.captcha = {}
        self.join_times = defaultdict(list)
        self.tickets = defaultdict(list)
        self.stats = defaultdict(int)
        self.polls = {}
        self.user_messages = defaultdict(lambda: deque(maxlen=50))
        self.user_last_messages = defaultdict(lambda: deque(maxlen=10))
        self.media_cache = {}
        self.scheduled_messages = {}
        self.ai_conversations = defaultdict(lambda: deque(maxlen=20))
        self.user_behavior = defaultdict(lambda: {"last_join": 0, "join_count": 0, "message_patterns": [], "suspicious_actions": 0})
        self._load_stats()
        self._start_backup_scheduler()
        self._start_cleanup_scheduler()
        self._start_scheduled_messages_scheduler()
    
    def _load_stats(self):
        rows = db.fetch_all("SELECT key, value FROM stats")
        for key, value in rows:
            self.stats[key] = value
    
    def _save_stats(self):
        for key, value in self.stats.items():
            db.execute("INSERT OR REPLACE INTO stats (key, value) VALUES (?, ?)", (key, value))
    
    def _start_backup_scheduler(self):
        def backup_loop():
            while True:
                time.sleep(86400)
                self.create_backup()
        threading.Thread(target=backup_loop, daemon=True).start()
    
    def _start_cleanup_scheduler(self):
        def cleanup_loop():
            while True:
                time.sleep(3600)
                self.cleanup_old_data()
        threading.Thread(target=cleanup_loop, daemon=True).start()
    
    def _start_scheduled_messages_scheduler(self):
        def scheduled_loop():
            while True:
                time.sleep(60)
                self.process_scheduled_messages()
        threading.Thread(target=scheduled_loop, daemon=True).start()
    
    def create_backup(self):
        try:
            data = {
                "stats": dict(self.stats),
                "timestamp": int(time.time()),
                "groups": db.fetch_all("SELECT * FROM groups"),
                "users": db.fetch_all("SELECT * FROM users"),
                "warnings": db.fetch_all("SELECT * FROM warnings"),
                "tickets": db.fetch_all("SELECT * FROM tickets"),
                "reports": db.fetch_all("SELECT * FROM reports"),
                "blacklist": db.fetch_all("SELECT * FROM blacklist"),
                "whitelist": db.fetch_all("SELECT * FROM whitelist"),
                "auto_replies": db.fetch_all("SELECT * FROM auto_replies"),
                "reminders": db.fetch_all("SELECT * FROM reminders"),
                "polls": db.fetch_all("SELECT * FROM polls"),
                "contests": db.fetch_all("SELECT * FROM contests"),
                "economy": db.fetch_all("SELECT * FROM economy"),
                "shop_items": db.fetch_all("SELECT * FROM shop_items"),
                "user_inventory": db.fetch_all("SELECT * FROM user_inventory"),
                "marriages": db.fetch_all("SELECT * FROM marriages"),
                "family": db.fetch_all("SELECT * FROM family"),
                "group_events": db.fetch_all("SELECT * FROM group_events"),
                "word_filters": db.fetch_all("SELECT * FROM word_filters"),
                "group_roles": db.fetch_all("SELECT * FROM group_roles"),
                "user_badges": db.fetch_all("SELECT * FROM user_badges")
            }
            with open(f"backup_{int(time.time())}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("بکاپ خودکار با موفقیت ایجاد شد.")
            for admin in ADMIN_IDS:
                try:
                    bot.send_message(admin, "✅ بکاپ خودکار روزانه با موفقیت انجام شد.")
                except:
                    pass
        except Exception as e:
            logger.error(f"خطا در بکاپ خودکار: {e}")
    
    def cleanup_old_data(self):
        try:
            now = int(time.time())
            db.execute("DELETE FROM captcha WHERE time < ?", (now - 300,))
            db.execute("DELETE FROM tickets WHERE status = 'closed' AND time < ?", (now - 604800,))
            db.execute("DELETE FROM group_statistics WHERE date < date('now', '-30 days')")
            db.execute("DELETE FROM reminders WHERE status = 'done' AND time < ?", (now - 86400,))
            logger.info("پاکسازی خودکار داده‌های قدیمی انجام شد.")
        except Exception as e:
            logger.error(f"خطا در پاکسازی خودکار: {e}")
    
    def process_scheduled_messages(self):
        try:
            now = int(time.time())
            rows = db.fetch_all("SELECT * FROM scheduled_messages WHERE status = 'pending' AND scheduled_time <= ?", (now,))
            for row in rows:
                try:
                    bot.send_message(row[1], row[2])
                    if row[5] == 1:
                        interval = 86400 if row[6] == 'daily' else 3600
                        db.execute("UPDATE scheduled_messages SET scheduled_time = ? WHERE id = ?", (now + interval, row[0]))
                    else:
                        db.execute("UPDATE scheduled_messages SET status = 'done' WHERE id = ?", (row[0],))
                except Exception as e:
                    logger.error(f"خطا در ارسال پیام زمان‌بندی شده: {e}")
        except Exception as e:
            logger.error(f"خطا در پردازش پیام‌های زمان‌بندی شده: {e}")
    
    def get_group(self, group_id):
        row = db.fetch_one("SELECT settings FROM groups WHERE group_id = ?", (group_id,))
        if row:
            settings = json.loads(row[0])
            for key, value in self.default_settings.items():
                if key not in settings:
                    settings[key] = value
            return settings
        else:
            settings = self.default_settings.copy()
            db.execute("INSERT INTO groups (group_id, settings, created_at) VALUES (?, ?, ?)",
                      (group_id, json.dumps(settings), int(time.time())))
            return settings
    
    def save_group(self, group_id, settings):
        db.execute("UPDATE groups SET settings = ? WHERE group_id = ?", (json.dumps(settings), group_id))
    
    def get_user(self, user_id):
        row = db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if row:
            return {
                "user_id": row[0],
                "username": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "level": row[4],
                "xp": row[5],
                "warnings": row[6],
                "muted_until": row[7],
                "banned_until": row[8],
                "verified": row[9],
                "join_date": row[10],
                "last_activity": row[11],
                "referral_code": row[12],
                "referred_by": row[13],
                "referral_count": row[14],
                "total_messages": row[15],
                "strike_count": row[16],
                "warnings_data": json.loads(row[17]) if row[17] else {},
                "achievements": json.loads(row[18]) if row[18] else [],
                "notes": row[19] or "",
                "is_admin": row[20] or 0,
                "daily_streak": row[21] or 0,
                "last_daily": row[22] or 0,
                "twofa_code": row[23] or "",
                "twofa_expiry": row[24] or 0,
                "is_2fa_verified": row[25] or 0,
                "afk_status": row[26] or "",
                "afk_time": row[27] or 0,
                "is_afk": row[28] or 0,
                "afk_reply_count": row[29] or 0,
                "last_voice": row[30] or 0,
                "voice_xp": row[31] or 0,
                "total_voice_time": row[32] or 0,
                "warning_points": row[33] or 0,
                "is_trusted": row[34] or 0,
                "trust_score": row[35] or 50
            }
        else:
            return {
                "user_id": user_id,
                "username": None,
                "first_name": None,
                "last_name": None,
                "level": 0,
                "xp": 0,
                "warnings": 0,
                "muted_until": 0,
                "banned_until": 0,
                "verified": 0,
                "join_date": 0,
                "last_activity": 0,
                "referral_code": None,
                "referred_by": None,
                "referral_count": 0,
                "total_messages": 0,
                "strike_count": 0,
                "warnings_data": {},
                "achievements": [],
                "notes": "",
                "is_admin": 0,
                "daily_streak": 0,
                "last_daily": 0,
                "twofa_code": "",
                "twofa_expiry": 0,
                "is_2fa_verified": 0,
                "afk_status": "",
                "afk_time": 0,
                "is_afk": 0,
                "afk_reply_count": 0,
                "last_voice": 0,
                "voice_xp": 0,
                "total_voice_time": 0,
                "warning_points": 0,
                "is_trusted": 0,
                "trust_score": 50
            }
    
    def save_user(self, user_data):
        db.execute('''
            INSERT OR REPLACE INTO users (
                user_id, username, first_name, last_name, level, xp, warnings,
                muted_until, banned_until, verified, join_date, last_activity,
                referral_code, referred_by, referral_count, total_messages,
                strike_count, warnings_data, achievements, notes, is_admin,
                daily_streak, last_daily, twofa_code, twofa_expiry, is_2fa_verified,
                afk_status, afk_time, is_afk, afk_reply_count, last_voice, voice_xp,
                total_voice_time, warning_points, is_trusted, trust_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_data["user_id"],
            user_data["username"],
            user_data["first_name"],
            user_data["last_name"],
            user_data["level"],
            user_data["xp"],
            user_data["warnings"],
            user_data["muted_until"],
            user_data["banned_until"],
            user_data["verified"],
            user_data["join_date"],
            user_data["last_activity"],
            user_data["referral_code"],
            user_data["referred_by"],
            user_data["referral_count"],
            user_data["total_messages"],
            user_data["strike_count"],
            json.dumps(user_data["warnings_data"]),
            json.dumps(user_data["achievements"]),
            user_data["notes"],
            user_data["is_admin"],
            user_data["daily_streak"],
            user_data["last_daily"],
            user_data["twofa_code"],
            user_data["twofa_expiry"],
            user_data["is_2fa_verified"],
            user_data["afk_status"],
            user_data["afk_time"],
            user_data["is_afk"],
            user_data["afk_reply_count"],
            user_data["last_voice"],
            user_data["voice_xp"],
            user_data["total_voice_time"],
            user_data["warning_points"],
            user_data["is_trusted"],
            user_data["trust_score"]
        ))
    
    # ========== سیستم AFK ==========
    def set_afk(self, user_id, status):
        user = self.get_user(user_id)
        user["afk_status"] = status
        user["afk_time"] = int(time.time())
        user["is_afk"] = 1
        user["afk_reply_count"] = 0
        self.save_user(user)
    
    def remove_afk(self, user_id):
        user = self.get_user(user_id)
        user["is_afk"] = 0
        user["afk_status"] = ""
        user["afk_time"] = 0
        self.save_user(user)
    
    def is_afk(self, user_id):
        user = self.get_user(user_id)
        return user["is_afk"] == 1
    
    def get_afk_status(self, user_id):
        user = self.get_user(user_id)
        return user["afk_status"]
    
    # ========== سیستم اعتماد ==========
    def update_trust_score(self, user_id, change):
        user = self.get_user(user_id)
        user["trust_score"] = max(0, min(100, user["trust_score"] + change))
        if user["trust_score"] >= 70 and not user["is_trusted"]:
            user["is_trusted"] = 1
            self.add_achievement(user_id, "trusted_member")
        elif user["trust_score"] < 70 and user["is_trusted"]:
            user["is_trusted"] = 0
        self.save_user(user)
        return user["trust_score"]
    
    def get_trust_score(self, user_id):
        user = self.get_user(user_id)
        return user["trust_score"]
    
    # ========== سیستم اقتصاد ==========
    def get_economy(self, user_id):
        row = db.fetch_one("SELECT * FROM economy WHERE user_id = ?", (user_id,))
        if row:
            return {
                "user_id": row[0],
                "coins": row[1],
                "bank": row[2],
                "last_work": row[3],
                "last_rob": row[4],
                "job": row[5],
                "job_level": row[6],
                "total_earned": row[7],
                "total_spent": row[8]
            }
        else:
            data = {
                "user_id": user_id,
                "coins": 0,
                "bank": 0,
                "last_work": 0,
                "last_rob": 0,
                "job": "بی‌کار",
                "job_level": 1,
                "total_earned": 0,
                "total_spent": 0
            }
            db.execute('''
                INSERT INTO economy (user_id, coins, bank, last_work, last_rob, job, job_level, total_earned, total_spent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, 0, 0, 0, 0, "بی‌کار", 1, 0, 0))
            return data
    
    def add_coins(self, user_id, amount):
        eco = self.get_economy(user_id)
        eco["coins"] += amount
        eco["total_earned"] += max(0, amount)
        db.execute('''
            UPDATE economy SET coins = ?, total_earned = ? WHERE user_id = ?
        ''', (eco["coins"], eco["total_earned"], user_id))
        return eco["coins"]
    
    def remove_coins(self, user_id, amount):
        eco = self.get_economy(user_id)
        if eco["coins"] < amount:
            return False
        eco["coins"] -= amount
        eco["total_spent"] += amount
        db.execute('''
            UPDATE economy SET coins = ?, total_spent = ? WHERE user_id = ?
        ''', (eco["coins"], eco["total_spent"], user_id))
        return True
    
    def work(self, user_id):
        eco = self.get_economy(user_id)
        now = int(time.time())
        cooldown = self.default_settings.get('economy_work_cooldown', 3600)
        if now - eco["last_work"] < cooldown:
            return None
        base_earn = random.randint(10, 50) * eco["job_level"]
        bonus = random.randint(0, 20)
        earn = base_earn + bonus
        eco["coins"] += earn
        eco["total_earned"] += earn
        eco["last_work"] = now
        db.execute('''
            UPDATE economy SET coins = ?, total_earned = ?, last_work = ? WHERE user_id = ?
        ''', (eco["coins"], eco["total_earned"], now, user_id))
        return earn
    
    def rob(self, user_id, target_id):
        eco = self.get_economy(user_id)
        now = int(time.time())
        cooldown = self.default_settings.get('economy_rob_cooldown', 7200)
        if now - eco["last_rob"] < cooldown:
            return None
        target_eco = self.get_economy(target_id)
        if target_eco["coins"] < 10:
            return "poor"
        success_rate = 0.4 - (target_eco["coins"] / 1000 * 0.05)
        success_rate = max(0.1, min(0.7, success_rate))
        if random.random() < success_rate:
            stolen = min(target_eco["coins"] // 3, random.randint(10, 100))
            target_eco["coins"] -= stolen
            eco["coins"] += stolen
            eco["total_earned"] += stolen
            eco["last_rob"] = now
            db.execute('''
                UPDATE economy SET coins = ? WHERE user_id = ?
            ''', (target_eco["coins"], target_id))
            db.execute('''
                UPDATE economy SET coins = ?, total_earned = ?, last_rob = ? WHERE user_id = ?
            ''', (eco["coins"], eco["total_earned"], now, user_id))
            return stolen
        else:
            eco["last_rob"] = now
            db.execute('''
                UPDATE economy SET last_rob = ? WHERE user_id = ?
            ''', (now, user_id))
            return "failed"
    
    def get_job_list(self):
        return [
            {"name": "کارگر", "base": 15, "level_req": 1},
            {"name": "کشاورز", "base": 20, "level_req": 2},
            {"name": "معلم", "base": 25, "level_req": 3},
            {"name": "برنامه‌نویس", "base": 35, "level_req": 5},
            {"name": "مهندس", "base": 45, "level_req": 7},
            {"name": "پزشک", "base": 55, "level_req": 10},
            {"name": "استاد دانشگاه", "base": 70, "level_req": 13},
            {"name": "مدیرعامل", "base": 100, "level_req": 15}
        ]
    
    def change_job(self, user_id, job_name):
        eco = self.get_economy(user_id)
        user = self.get_user(user_id)
        jobs = self.get_job_list()
        for job in jobs:
            if job["name"] == job_name and user["level"] >= job["level_req"]:
                eco["job"] = job_name
                db.execute('''
                    UPDATE economy SET job = ? WHERE user_id = ?
                ''', (job_name, user_id))
                return True
        return False
    
    # ========== سیستم فروشگاه ==========
    def add_shop_item(self, group_id, name, price, description="", stock=-1, category="general"):
        db.execute('''
            INSERT INTO shop_items (group_id, name, price, description, stock, category)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (group_id, name, price, description, stock, category))
        return db.cursor.lastrowid
    
    def remove_shop_item(self, item_id):
        db.execute("DELETE FROM shop_items WHERE id = ?", (item_id,))
    
    def get_shop_items(self, group_id):
        return db.fetch_all("SELECT * FROM shop_items WHERE group_id = ?", (group_id,))
    
    def buy_item(self, user_id, item_id):
        item = db.fetch_one("SELECT * FROM shop_items WHERE id = ?", (item_id,))
        if not item:
            return "not_found"
        if item[3] == 0:
            return "out_of_stock"
        eco = self.get_economy(user_id)
        if eco["coins"] < item[2]:
            return "insufficient"
        if not self.remove_coins(user_id, item[2]):
            return "error"
        inv = db.fetch_one("SELECT * FROM user_inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        if inv:
            db.execute('''
                UPDATE user_inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_id = ?
            ''', (user_id, item_id))
        else:
            db.execute('''
                INSERT INTO user_inventory (user_id, item_id, quantity) VALUES (?, ?, ?)
            ''', (user_id, item_id, 1))
        if item[4] > 0:
            db.execute("UPDATE shop_items SET stock = stock - 1 WHERE id = ?", (item_id,))
        return "success"
    
    def get_inventory(self, user_id):
        return db.fetch_all('''
            SELECT si.*, ui.quantity FROM user_inventory ui
            JOIN shop_items si ON ui.item_id = si.id
            WHERE ui.user_id = ?
        ''', (user_id,))
    
    # ========== سیستم ازدواج ==========
    def marry(self, user1_id, user2_id):
        existing = db.fetch_one('''
            SELECT 1 FROM marriages WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'
        ''', (user1_id, user1_id))
        if existing:
            return "already_married"
        if user1_id == user2_id:
            return "self_marriage"
        db.execute('''
            INSERT INTO marriages (user1_id, user2_id, married_date, status)
            VALUES (?, ?, ?, ?)
        ''', (user1_id, user2_id, int(time.time()), "active"))
        return "success"
    
    def divorce(self, user_id):
        marriage = db.fetch_one('''
            SELECT * FROM marriages WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'
        ''', (user_id, user_id))
        if not marriage:
            return "not_married"
        cost = self.default_settings.get('divorce_cost', 100)
        eco = self.get_economy(user_id)
        if eco["coins"] < cost:
            return "insufficient"
        self.remove_coins(user_id, cost)
        db.execute("UPDATE marriages SET status = 'divorced' WHERE id = ?", (marriage[0],))
        return "success"
    
    def get_marriage(self, user_id):
        return db.fetch_one('''
            SELECT * FROM marriages WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'
        ''', (user_id, user_id))
    
    def add_love_score(self, marriage_id, amount):
        db.execute('''
            UPDATE marriages SET love_score = love_score + ? WHERE id = ?
        ''', (amount, marriage_id))
    
    # ========== سیستم خانواده ==========
    def add_family_member(self, parent_id, child_id, relationship="father"):
        existing = db.fetch_one('''
            SELECT 1 FROM family WHERE parent_id = ? AND child_id = ?
        ''', (parent_id, child_id))
        if existing:
            return False
        db.execute('''
            INSERT INTO family (parent_id, child_id, relationship, status)
            VALUES (?, ?, ?, ?)
        ''', (parent_id, child_id, relationship, "active"))
        return True
    
    def remove_family_member(self, parent_id, child_id):
        db.execute('''
            DELETE FROM family WHERE parent_id = ? AND child_id = ?
        ''', (parent_id, child_id))
    
    def get_family_members(self, user_id):
        return db.fetch_all('''
            SELECT * FROM family WHERE parent_id = ? OR child_id = ?
        ''', (user_id, user_id))
    
    # ========== سیستم رویدادهای گروه ==========
    def add_event(self, group_id, name, description, date, creator_id):
        db.execute('''
            INSERT INTO group_events (group_id, name, description, date, creator_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (group_id, name, description, date, creator_id, "upcoming"))
        return db.cursor.lastrowid
    
    def get_events(self, group_id):
        return db.fetch_all('''
            SELECT * FROM group_events WHERE group_id = ? AND status = 'upcoming'
            ORDER BY date ASC
        ''', (group_id,))
    
    def cancel_event(self, event_id):
        db.execute("UPDATE group_events SET status = 'cancelled' WHERE id = ?", (event_id,))
    
    # ========== سیستم هوش مصنوعی ==========
    async def get_ai_response(self, user_id, message):
        if not self.default_settings.get('ai_assistant_enabled', True):
            return "🤖 سیستم هوش مصنوعی غیرفعال است."
        message_lower = message.lower()
        greetings = ["سلام", "درود", "سلام علیکم", "hi", "hello"]
        if any(g in message_lower for g in greetings):
            return "👋 سلام! چطور می‌توانم کمک کنم؟"
        if "خوب" in message_lower or "حالت" in message_lower:
            return "😊 من خوبم، ممنون که پرسیدی!"
        if "ربات" in message_lower or "تو کی" in message_lower:
            return "🤖 من یک ربات هوشمند هستم که برای کمک به مدیریت گروه طراحی شده‌ام!"
        if "عشق" in message_lower or "دوست" in message_lower:
            return "💕 عشق و دوستی بهترین چیزهای دنیا هستند!"
        if "کمک" in message_lower:
            return "🆘 حتماً! برای دریافت راهنما دستور /help را بفرستید."
        responses = [
            "🤔 متوجه شدم! می‌توانید بیشتر توضیح دهید؟",
            "😊 بسیار خوب! نظر شما برای من مهم است.",
            "📝 این رو یادداشت کردم!",
            "💡 ایده‌ی جالبی است!",
            "🎯 دقیقاً! موافقم."
        ]
        return random.choice(responses)
    
    # ========== سیستم نشان‌ها ==========
    def add_achievement(self, user_id, badge_id):
        try:
            db.execute('''
                INSERT OR IGNORE INTO user_badges (user_id, badge_id, earned_date)
                VALUES (?, ?, ?)
            ''', (user_id, badge_id, int(time.time())))
        except:
            pass
    
    def get_achievements(self, user_id):
        return db.fetch_all("SELECT * FROM user_badges WHERE user_id = ?", (user_id,))
    
    def check_achievements(self, user_id):
        user = self.get_user(user_id)
        achievements = []
        if user["level"] >= 5:
            self.add_achievement(user_id, "level_5")
            achievements.append("سطح ۵")
        if user["level"] >= 10:
            self.add_achievement(user_id, "level_10")
            achievements.append("سطح ۱۰")
        if user["level"] >= 25:
            self.add_achievement(user_id, "level_25")
            achievements.append("سطح ۲۵")
        if user["level"] >= 50:
            self.add_achievement(user_id, "level_50")
            achievements.append("سطح ۵۰")
        if user["total_messages"] >= 100:
            self.add_achievement(user_id, "100_messages")
            achievements.append("۱۰۰ پیام")
        if user["total_messages"] >= 1000:
            self.add_achievement(user_id, "1000_messages")
            achievements.append("۱۰۰۰ پیام")
        if user["daily_streak"] >= 7:
            self.add_achievement(user_id, "7_day_streak")
            achievements.append("استریک ۷ روزه")
        if user["daily_streak"] >= 30:
            self.add_achievement(user_id, "30_day_streak")
            achievements.append("استریک ۳۰ روزه")
        eco = self.get_economy(user_id)
        if eco["total_earned"] >= 1000:
            self.add_achievement(user_id, "earned_1000")
            achievements.append("۱۰۰۰ سکه")
        if eco["total_earned"] >= 10000:
            self.add_achievement(user_id, "earned_10000")
            achievements.append("۱۰۰۰۰ سکه")
        return achievements
    
    # ========== سیستم فیلتر کلمات ==========
    def add_word_filter(self, group_id, word, action="delete"):
        try:
            db.execute('''
                INSERT INTO word_filters (group_id, word, action)
                VALUES (?, ?, ?)
            ''', (group_id, word, action))
            return True
        except:
            return False
    
    def remove_word_filter(self, group_id, word):
        db.execute("DELETE FROM word_filters WHERE group_id = ? AND word = ?", (group_id, word))
    
    def get_word_filters(self, group_id):
        return db.fetch_all("SELECT * FROM word_filters WHERE group_id = ?", (group_id,))
    
    def check_word_filters(self, group_id, text):
        filters = self.get_word_filters(group_id)
        text_lower = text.lower()
        for filter_row in filters:
            if filter_row[2].lower() in text_lower:
                return filter_row[3]
        return None
    
    # ========== سیستم نقش‌ها ==========
    def assign_role(self, group_id, user_id, role, color="#000000", permissions=None):
        db.execute('''
            INSERT OR REPLACE INTO group_roles (group_id, user_id, role, color, permissions)
            VALUES (?, ?, ?, ?, ?)
        ''', (group_id, user_id, role, color, json.dumps(permissions) if permissions else None))
    
    def get_role(self, group_id, user_id):
        row = db.fetch_one("SELECT * FROM group_roles WHERE group_id = ? AND user_id = ?", (group_id, user_id))
        if row:
            return {
                "role": row[3],
                "color": row[4],
                "permissions": json.loads(row[5]) if row[5] else {}
            }
        return {"role": "member", "color": "#000000", "permissions": {}}
    
    def get_role_list(self, group_id):
        return db.fetch_all("SELECT * FROM group_roles WHERE group_id = ?", (group_id,))
    
    # ========== سیستم پیام‌های زمان‌بندی شده ==========
    def add_scheduled_message(self, group_id, message, scheduled_time, is_recurring=0, interval_type="daily"):
        db.execute('''
            INSERT INTO scheduled_messages (group_id, message, scheduled_time, is_recurring, interval_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (group_id, message, scheduled_time, is_recurring, interval_type))
        return db.cursor.lastrowid
    
    # ========== امتیاز صوتی ==========
    def add_voice_xp(self, user_id, duration):
        if not self.default_settings.get('voice_xp_enabled', True):
            return 0
        user = self.get_user(user_id)
        now = int(time.time())
        if now - user["last_voice"] < 86400:
            if user["voice_xp"] >= self.default_settings.get('max_voice_xp_per_day', 100):
                return 0
        else:
            user["voice_xp"] = 0
        xp_gain = min(duration // 60, 10) * self.default_settings.get('voice_chat_reward', 5)
        xp_gain = min(xp_gain, self.default_settings.get('max_voice_xp_per_day', 100) - user["voice_xp"])
        if xp_gain > 0:
            user["voice_xp"] += xp_gain
            user["total_voice_time"] += duration
            self.add_xp(user_id, xp_gain)
            self.save_user(user)
            return xp_gain
        return 0
    
    # ========== تشخیص ناهنجاری ==========
    def analyze_behavior(self, user_id, action):
        behavior = self.user_behavior[user_id]
        behavior["suspicious_actions"] += 1
        if behavior["suspicious_actions"] > 5:
            self.update_trust_score(user_id, -10)
            if self.default_settings.get('instant_ban_on_suspicious', True):
                return "suspicious"
        return "normal"
    
    def detect_pattern(self, user_id, message):
        behavior = self.user_behavior[user_id]
        behavior["message_patterns"].append(message[:20])
        if len(behavior["message_patterns"]) > 10:
            behavior["message_patterns"].pop(0)
        if len(behavior["message_patterns"]) >= 5:
            patterns = [p for p in behavior["message_patterns"] if p]
            if len(set(patterns)) <= 2:
                self.update_trust_score(user_id, -5)
                return "pattern_detected"
        return "normal"

udb = UltraDatabase()

# ========== ابزارهای کمکی ==========
def is_admin(user_id, chat_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

def is_bot_admin(user_id):
    return user_id in ADMIN_IDS

def get_user_mention(user):
    name = user.first_name
    if user.username:
        return f"@{user.username}"
    return f"<a href='tg://user?id={user.id}'>{name}</a>"

def format_duration(seconds):
    if seconds < 60:
        return f"{seconds} ثانیه"
    elif seconds < 3600:
        return f"{seconds // 60} دقیقه"
    elif seconds < 86400:
        return f"{seconds // 3600} ساعت"
    else:
        return f"{seconds // 86400} روز"

def contains_bad_words(text):
    bad_words = ["فحش", "کیر", "کون", "کس", "گه", "گوه", "حرام", "لعنت", "جاکش", "جنده", "فاحشه", "خایه", "مادرجنده"]
    return any(w in text.lower() for w in bad_words)

def contains_ad_keywords(text):
    ad_words = ["خرید", "فروش", "قیمت", "تخفیف", "فروشگاه", "سفارش", "تبلیغات", "تبلیغ", "اسپانسر", "حامی", "کسب درآمد", "ارز دیجیتال", "بیت‌کوین", "فارکس"]
    return any(w in text.lower() for w in ad_words)

def contains_link(text):
    return re.search(r'(https?://[^\s]+)|(www\.[^\s]+)|(t\.me/[^\s]+)|(telegram\.me/[^\s]+)', text) is not None

def extract_links(text):
    return re.findall(r'(https?://[^\s]+)|(www\.[^\s]+)|(t\.me/[^\s]+)|(telegram\.me/[^\s]+)', text)

def is_forwarded(message):
    return message.forward_from is not None or message.forward_from_chat is not None

def detect_url_shortener(text):
    shorteners = ["bit.ly", "tinyurl", "shorturl", "goo.gl", "ow.ly", "is.gd", "buff.ly", "adf.ly", "shorte.st", "cutt.ly", "rebrand.ly", "short.link"]
    return any(s in text.lower() for s in shorteners)

def detect_phone(text):
    return re.search(r'(\+98|0098|0)?9\d{9}', text) is not None

def detect_email(text):
    return re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text) is not None

def detect_web3_scam(text):
    keywords = ["web3", "airdrop", "nft", "whitelist", "presale", "ico", "token", "wallet", "connect", "metamask", "trust wallet"]
    scam = any(k in text.lower() for k in keywords)
    if scam and contains_link(text):
        return True
    return False

def detect_fake_telegram(text):
    patterns = ["t.me/", "telegram.me/", "telegram.dog/", "telegra.ph/"]
    return any(p in text.lower() for p in patterns) and "admin" in text.lower()

def detect_toxic_content(text):
    toxic_words = ["کشته", "بکش", "نفرت", "کثیف", "بی‌شرف", "بدبخت", "حروم", "مردم‌کش"]
    return any(w in text.lower() for w in toxic_words)

def is_voice_call(message):
    return message.voice_chat_started is not None or message.voice_chat_scheduled is not None

# ========== کیبوردها ==========
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
        InlineKeyboardButton("📊 آمار", callback_data="stats"),
        InlineKeyboardButton("📋 قوانین", callback_data="rules"),
        InlineKeyboardButton("🏆 رنکینگ", callback_data="ranking"),
        InlineKeyboardButton("🎫 تیکت", callback_data="tickets"),
        InlineKeyboardButton("👤 پروفایل", callback_data="profile"),
        InlineKeyboardButton("🆘 راهنما", callback_data="help"),
        InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh"),
        InlineKeyboardButton("🚨 گزارش تخلف", callback_data="report"),
        InlineKeyboardButton("🔒 امنیت", callback_data="security_panel"),
        InlineKeyboardButton("📝 مدیریت", callback_data="admin_panel"),
        InlineKeyboardButton("🎁 پاداش روزانه", callback_data="daily_reward"),
        InlineKeyboardButton("🏅 مسابقات", callback_data="contests"),
        InlineKeyboardButton("👥 مدیریت ادمین‌ها", callback_data="admin_management"),
        InlineKeyboardButton("💰 اقتصاد", callback_data="economy"),
        InlineKeyboardButton("💑 ازدواج", callback_data="marriage"),
        InlineKeyboardButton("👨‍👩‍👧‍👦 خانواده", callback_data="family"),
        InlineKeyboardButton("📅 رویدادها", callback_data="events"),
        InlineKeyboardButton("🤖 هوش مصنوعی", callback_data="ai_chat"),
        InlineKeyboardButton("🎖️ نشان‌ها", callback_data="badges"),
        InlineKeyboardButton("🔰 نقش‌ها", callback_data="roles")
    )
    return keyboard

def settings_menu(group_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🔰 پایه", callback_data=f"basic_{group_id}"),
        InlineKeyboardButton("🛡️ ضد اسپم", callback_data=f"spam_{group_id}"),
        InlineKeyboardButton("🚫 محدودیت‌ها", callback_data=f"restrict_{group_id}"),
        InlineKeyboardButton("🔐 امنیت", callback_data=f"security_{group_id}"),
        InlineKeyboardButton("🎯 پیشرفته", callback_data=f"advanced_{group_id}"),
        InlineKeyboardButton("🤖 پاسخ خودکار", callback_data=f"autoreply_{group_id}"),
        InlineKeyboardButton("📝 قوانین", callback_data=f"rules_edit_{group_id}"),
        InlineKeyboardButton("📋 لیست‌ها", callback_data=f"lists_{group_id}"),
        InlineKeyboardButton("🌟 فوق‌پیشرفته", callback_data=f"ultra_{group_id}"),
        InlineKeyboardButton("🧠 هوش مصنوعی", callback_data=f"ai_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
    )
    return keyboard

def basic_settings_menu(group_id):
    settings = udb.get_group(group_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(f"{'✅' if settings['welcome_enabled'] else '❌'} پیام خوش‌آمدگویی", callback_data=f"toggle_welcome_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['captcha'] else '❌'} کپچا", callback_data=f"toggle_captcha_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['auto_delete'] else '❌'} حذف خودکار", callback_data=f"toggle_autodelete_{group_id}"),
        InlineKeyboardButton("⏱️ تنظیم زمان حذف", callback_data=f"autodel_set_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['daily_reward'] else '❌'} پاداش روزانه", callback_data=f"toggle_daily_reward_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['afk_enabled'] else '❌'} سیستم AFK", callback_data=f"toggle_afk_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['goodbye_enabled'] else '❌'} پیام خداحافظی", callback_data=f"toggle_goodbye_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def spam_settings_menu(group_id):
    settings = udb.get_group(group_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(f"{'✅' if settings['anti_spam'] else '❌'} ضد اسپم", callback_data=f"toggle_antispam_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_spam_bayesian'] else '❌'} تشخیص بیزین", callback_data=f"toggle_bayesian_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_raid'] else '❌'} ضد رید", callback_data=f"toggle_antiraid_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['duplicate_message_detection'] else '❌'} تشخیص پیام تکراری", callback_data=f"toggle_duplicate_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_ghost_ping'] else '❌'} ضد Ghost Ping", callback_data=f"toggle_ghostping_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def restrict_settings_menu(group_id):
    settings = udb.get_group(group_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(f"{'✅' if settings['anti_mentions'] else '❌'} ضد منشن", callback_data=f"toggle_mentions_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_caps'] else '❌'} ضد کپس", callback_data=f"toggle_caps_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_emoji'] else '❌'} ضد ایموجی", callback_data=f"toggle_emoji_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_newlines'] else '❌'} ضد خط جدید", callback_data=f"toggle_newlines_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_forward'] else '❌'} ضد فوروارد", callback_data=f"toggle_forward_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def security_settings_menu(group_id):
    settings = udb.get_group(group_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(f"{'✅' if settings['anti_bot'] else '❌'} ضد ربات", callback_data=f"toggle_bot_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_link'] else '❌'} ضد لینک", callback_data=f"toggle_link_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_bad_words'] else '❌'} ضد فحش", callback_data=f"toggle_badwords_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_advertising'] else '❌'} ضد تبلیغات", callback_data=f"toggle_advert_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['two_factor_auth'] else '❌'} تأیید دو مرحله‌ای", callback_data=f"toggle_2fa_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_web3_scam'] else '❌'} ضد کلاهبرداری Web3", callback_data=f"toggle_web3_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_fake_telegram'] else '❌'} ضد تلگرام جعلی", callback_data=f"toggle_faketg_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def advanced_settings_menu(group_id):
    settings = udb.get_group(group_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(f"{'✅' if settings['anti_porn'] else '❌'} ضد محتوای بزرگسالان", callback_data=f"toggle_porn_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_violence'] else '❌'} ضد خشونت", callback_data=f"toggle_violence_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_drugs'] else '❌'} ضد مواد مخدر", callback_data=f"toggle_drugs_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_hate'] else '❌'} ضد نفرت", callback_data=f"toggle_hate_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_phishing'] else '❌'} ضد فیشینگ", callback_data=f"toggle_phishing_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_malware'] else '❌'} ضد بدافزار", callback_data=f"toggle_malware_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_terrorism'] else '❌'} ضد تروریسم", callback_data=f"toggle_terrorism_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_child_abuse'] else '❌'} ضد آزار کودکان", callback_data=f"toggle_childabuse_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_crypto'] else '❌'} ضد کلاهبرداری رمزارز", callback_data=f"toggle_crypto_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_gambling'] else '❌'} ضد قمار", callback_data=f"toggle_gambling_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_url_shortener'] else '❌'} ضد لینک کوتاه", callback_data=f"toggle_shortener_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_phone'] else '❌'} ضد شماره تلفن", callback_data=f"toggle_phone_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anti_email'] else '❌'} ضد ایمیل", callback_data=f"toggle_email_{group_id}"),
        InlineKeyboardButton(f"{'🔒' if settings['group_lock'] else '🔓'} قفل گروه", callback_data=f"toggle_lock_{group_id}"),
        InlineKeyboardButton(f"{'🔇' if settings['silent_mode'] else '🔊'} حالت سکوت", callback_data=f"toggle_silent_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['leveling'] else '❌'} سیستم سطح", callback_data=f"toggle_level_{group_id}"),
        InlineKeyboardButton(f"{'🔒' if settings['button_access_locked'] else '🔓'} دسترسی دکمه‌ها", callback_data=f"toggle_button_access_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['voice_xp_enabled'] else '❌'} امتیاز مکالمه صوتی", callback_data=f"toggle_voicexp_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['trust_system_enabled'] else '❌'} سیستم اعتماد", callback_data=f"toggle_trust_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def ultra_settings_menu(group_id):
    settings = udb.get_group(group_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(f"{'✅' if settings['auto_ban_on_three_warnings'] else '❌'} بن بعد از ۳ اخطار", callback_data=f"toggle_auto_ban_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['auto_backup'] else '❌'} بکاپ خودکار", callback_data=f"toggle_autobackup_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['scan_media'] else '❌'} اسکن رسانه", callback_data=f"toggle_scanmedia_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['auto_report_to_admins'] else '❌'} گزارش خودکار به ادمین", callback_data=f"toggle_autoreport_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['word_filter_enabled'] else '❌'} فیلتر کلمات", callback_data=f"toggle_wordfilter_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['anomaly_detection'] else '❌'} تشخیص ناهنجاری", callback_data=f"toggle_anomaly_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['proactive_security'] else '❌'} امنیت پیش‌گیرانه", callback_data=f"toggle_proactive_{group_id}"),
        InlineKeyboardButton(f"{'✅' if settings['auto_healing'] else '❌'} خودترمیمی", callback_data=f"toggle_autoheal_{group_id}"),
        InlineKeyboardButton(f"📊 سطح حساسیت: {settings['sensitivity_level']}", callback_data=f"set_sensitivity_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def ai_settings_menu(group_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🧠 وضعیت هوش مصنوعی", callback_data=f"ai_status_{group_id}"),
        InlineKeyboardButton("⚙️ تنظیمات API", callback_data=f"ai_config_{group_id}"),
        InlineKeyboardButton("📊 آمار مکالمات", callback_data=f"ai_stats_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def autoreply_menu(group_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ افزودن پاسخ خودکار", callback_data=f"add_autoreply_{group_id}"),
        InlineKeyboardButton("📋 لیست پاسخ‌ها", callback_data=f"list_autoreply_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def lists_menu(group_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📋 لیست سیاه", callback_data=f"blacklist_{group_id}"),
        InlineKeyboardButton("📋 لیست سفید", callback_data=f"whitelist_{group_id}"),
        InlineKeyboardButton("📋 گزارش‌ها", callback_data=f"reports_{group_id}"),
        InlineKeyboardButton("📋 فیلتر کلمات", callback_data=f"wordfilters_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def auto_delete_menu(group_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⏱️ ۱ ساعت", callback_data=f"autodel_set_{group_id}_3600"),
        InlineKeyboardButton("⏱️ ۶ ساعت", callback_data=f"autodel_set_{group_id}_21600"),
        InlineKeyboardButton("⏱️ ۱۲ ساعت", callback_data=f"autodel_set_{group_id}_43200"),
        InlineKeyboardButton("⏱️ ۲۴ ساعت", callback_data=f"autodel_set_{group_id}_86400"),
        InlineKeyboardButton("❌ غیرفعال", callback_data=f"autodel_set_{group_id}_0"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_settings_{group_id}")
    )
    return keyboard

def contest_menu(group_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ مسابقه جدید", callback_data=f"new_contest_{group_id}"),
        InlineKeyboardButton("📋 مسابقات فعال", callback_data=f"list_contests_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
    )
    return keyboard

def admin_management_menu(group_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ افزودن ادمین", callback_data=f"add_admin_{group_id}"),
        InlineKeyboardButton("➖ حذف ادمین", callback_data=f"remove_admin_{group_id}"),
        InlineKeyboardButton("📋 لیست ادمین‌ها", callback_data=f"list_admins_{group_id}"),
        InlineKeyboardButton("📢 منشن همه", callback_data=f"mention_all_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
    )
    return keyboard

def economy_menu(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💰 موجودی", callback_data=f"eco_balance_{user_id}"),
        InlineKeyboardButton("💼 کار", callback_data=f"eco_work_{user_id}"),
        InlineKeyboardButton("🏦 بانک", callback_data=f"eco_bank_{user_id}"),
        InlineKeyboardButton("🛒 فروشگاه", callback_data=f"eco_shop_{user_id}"),
        InlineKeyboardButton("💼 شغل", callback_data=f"eco_job_{user_id}"),
        InlineKeyboardButton("🎁 هدیه", callback_data=f"eco_gift_{user_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
    )
    return keyboard

def marriage_menu(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💍 ازدواج", callback_data=f"marry_{user_id}"),
        InlineKeyboardButton("💔 طلاق", callback_data=f"divorce_{user_id}"),
        InlineKeyboardButton("💕 وضعیت ازدواج", callback_data=f"marriage_status_{user_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
    )
    return keyboard

def family_menu(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("👨‍👦 افزودن عضو", callback_data=f"family_add_{user_id}"),
        InlineKeyboardButton("👨‍👩‍👧‍👦 اعضای خانواده", callback_data=f"family_list_{user_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
    )
    return keyboard

def events_menu(group_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ رویداد جدید", callback_data=f"event_add_{group_id}"),
        InlineKeyboardButton("📋 رویدادها", callback_data=f"event_list_{group_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
    )
    return keyboard

def back_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
    return keyboard

def get_back_button(user_id, chat_id=None):
    if chat_id and chat_id != user_id:
        settings = udb.get_group(chat_id)
        if settings.get('button_access_locked', True) and not is_admin(user_id, chat_id) and not is_bot_admin(user_id):
            return None
    return back_button()

# ========== دیکشنری دستورات فارسی ==========
command_handlers = {}

def register_command(cmd):
    def decorator(func):
        command_handlers[cmd] = func
        return func
    return decorator

# ========== هندلر دستورات فارسی ==========
@bot.message_handler(func=lambda message: message.text and any(message.text.startswith(cmd) for cmd in command_handlers), content_types=['text'])
def handle_persian_commands(message):
    for cmd in command_handlers:
        if message.text.startswith(cmd):
            command_handlers[cmd](message)
            break

# ========== دستورات /start و /help ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    chat_id = message.chat.id
    if message.chat.type in ['group', 'supergroup'] and not is_admin(user.id, chat_id) and not is_bot_admin(user.id):
        bot.reply_to(message, "⛔ این دستور فقط برای ادمین‌های گروه قابل استفاده است.")
        return
    text = f"""
✨ **ربات محافظ فوق‌پیشرفته Luffy Ultra Pro V4** ✨
━━━━━━━━━━━━━━━━━━━━━━
👤 **کاربر:** {user.first_name}
🆔 **آیدی:** `{user.id}`
👑 **نقش:** {'👑 ادمین اصلی' if is_bot_admin(user.id) else '👤 کاربر'}
━━━━━━━━━━━━━━━━━━━━━━

🛡️ **قابلیت‌های بی‌نظیر جدید:**
• 🤖 هوش مصنوعی مکالمه
• 💰 اقتصاد کامل (کار، خرید، بانک)
• 💑 سیستم ازدواج و عشق
• 👨‍👩‍👧‍👦 سیستم خانواده
• 📅 رویدادهای گروه
• 🎖️ سیستم نشان‌ها و دستاوردها
• 🔰 سیستم نقش‌ها
• 😴 سیستم AFK
• 🎤 امتیاز مکالمات صوتی
• 🤝 سیستم اعتماد و امتیاز
• 🚨 تشخیص ناهنجاری رفتاری
• 🛡️ امنیت پیش‌گیرانه
• 🔄 خودترمیمی
• 🧠 تحلیل محتوای هوشمند
• 🔍 تشخیص کلاهبرداری Web3
• 🚫 ضد Ghost Ping
• 📝 فیلتر کلمات پیشرفته
• 📅 پیام‌های زمان‌بندی شده
• و ده‌ها قابلیت دیگر!

📌 برای مدیریت، بات را به گروه اضافه و ادمین کنید.
"""
    bot.reply_to(message, text, reply_markup=main_menu(), parse_mode='HTML')

@bot.message_handler(commands=['help'])
def help_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    menu = get_back_button(user_id, chat_id) if message.chat.type in ['group', 'supergroup'] else back_button()
    text = """
📋 **راهنمای کامل ربات (نسخه V4)**
━━━━━━━━━━━━━━━━━━━━━━
**دستورات عمومی (بدون اسلش):**
start - منوی اصلی
راهنما - این راهنما
قوانین - نمایش قوانین
رتبه - نمایش رتبه شما
رنکینگ - رنکینگ گروه
پروفایل - پروفایل شما
پاداش - دریافت پاداش روزانه
تیکت [موضوع] - تیکت جدید
گزارش [کاربر] [دلیل] - گزارش تخلف
یادآور [زمان] [پیام] - تنظیم یادآوری
افک [وضعیت] - تنظیم AFK
برداشتن افک - برداشتن AFK
موجودی - نمایش سکه‌ها
کار - کار کردن
خرید [آیتم] - خرید از فروشگاه
فروشگاه - لیست فروشگاه
هدیه [کاربر] [مقدار] - هدیه دادن سکه
ازدواج [کاربر] - پیشنهاد ازدواج
طلاق - طلاق گرفتن
وضعیت ازدواج - وضعیت ازدواج
خانواده - لیست اعضای خانواده
افزودن فرزند [کاربر] - افزودن فرزند
رویدادها - لیست رویدادها
نشان‌ها - نشان‌های شما
نقش من - نقش شما

**دستورات مدیریت (فقط ادمین‌ها، بدون اسلش):**
تنظیمات - تنظیمات پیشرفته
آمار - آمار گروه
بن [کاربر] - بن کاربر
آنبن [کاربر] - آن‌بن
اخراج [کاربر] - اخراج
تک [کاربر] - اخراج
میوت [کاربر] [مدت] - میوت
آنمیوت [کاربر] - رفع میوت
اخطار [کاربر] [دلیل] - اخطار
اخطارها [کاربر] - نمایش اخطارها
پاکسازی اخطارها [کاربر] - بازنشانی
پاکسازی (ریپلای) - پاکسازی پیام‌ها
سنجاق (ریپلای) - پین
برداشتن سنجاق - برداشتن پین
قفل - قفل گروه
بازکردن قفل - باز کردن قفل
بکاپ - بکاپ
سیاه [کاربر] [دلیل] - افزودن به لیست سیاه
سفید [کاربر] [دلیل] - افزودن به لیست سفید
حذف سیاه [کاربر] - حذف از لیست سیاه
حذف سفید [کاربر] - حذف از لیست سفید
نظرسنجی [سوال] | [گزینه1] | [گزینه2] ... - ایجاد نظرسنجی
بستن نظرسنجی [شناسه] - بستن نظرسنجی
مسابقه [نام] | [توضیحات] | [زمان] - ایجاد مسابقه
شرکت [شناسه] - شرکت در مسابقه
انتخاب برنده [شناسه] - انتخاب برنده مسابقه
addadmin [کاربر] - افزودن ادمین
removeadmin [کاربر] - حذف ادمین
admins - لیست ادمین‌ها
mentionall [متن] - منشن همه
setwelcome [متن] - تنظیم پیام خوش‌آمد
setwelcomephoto (ریپلای به عکس) - تنظیم عکس خوش‌آمد
setrules [متن] - تنظیم قوانین
showrules - نمایش قوانین
افزودن فیلتر [کلمه] - افزودن فیلتر کلمه
حذف فیلتر [کلمه] - حذف فیلتر کلمه
لیست فیلترها - لیست فیلترها
رویداد [نام] | [توضیحات] | [زمان] - ایجاد رویداد
لغو رویداد [شناسه] - لغو رویداد
زمان‌بندی [زمان] [پیام] - پیام زمان‌بندی شده

**نکته:** می‌توانید به پیام کاربر ریپلای کنید.
━━━━━━━━━━━━━━━━━━━━━━
"""
    bot.reply_to(message, text, reply_markup=menu, parse_mode='HTML')

# ========== دستورات جدید فوق‌پیشرفته ==========

# ===== سیستم AFK =====
@register_command("افک")
def afk_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        status = "من فعلاً در دسترس نیستم. پیام می‌دم برمی‌گردم!"
    else:
        status = " ".join(args[1:])
    udb.set_afk(user_id, status)
    bot.reply_to(message, f"✅ شما AFK شدید: {status}")

@register_command("برداشتن افک")
def remove_afk_command(message):
    user_id = message.from_user.id
    if udb.is_afk(user_id):
        udb.remove_afk(user_id)
        bot.reply_to(message, "✅ حالت AFK برداشته شد.")
    else:
        bot.reply_to(message, "❌ شما در حالت AFK نیستید.")

# ===== سیستم اقتصاد =====
@register_command("موجودی")
def balance_command(message):
    user_id = message.from_user.id
    eco = udb.get_economy(user_id)
    user = udb.get_user(user_id)
    text = f"""
💰 **موجودی شما**
━━━━━━━━━━━━━━━━━━━━━━
🪙 **سکه:** {eco['coins']:,}
🏦 **بانک:** {eco['bank']:,}
💼 **شغل:** {eco['job']}
📈 **سطح شغل:** {eco['job_level']}
💰 **کل درآمد:** {eco['total_earned']:,}
💸 **کل هزینه:** {eco['total_spent']:,}
━━━━━━━━━━━━━━━━━━━━━━
"""
    bot.reply_to(message, text, parse_mode='HTML')

@register_command("کار")
def work_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    user_id = message.from_user.id
    earn = udb.work(user_id)
    if earn is None:
        eco = udb.get_economy(user_id)
        remaining = udb.default_settings.get('economy_work_cooldown', 3600) - (int(time.time()) - eco["last_work"])
        bot.reply_to(message, f"⏳ هنوز زمان کار کردن نرسیده! {format_duration(max(0, remaining))} باقی مانده.")
    else:
        udb.add_xp(user_id, earn // 10)
        bot.reply_to(message, f"💼 شما {earn} سکه کار کردید! +{earn//10} XP")

@register_command("فروشگاه")
def shop_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    items = udb.get_shop_items(group_id)
    if not items:
        bot.reply_to(message, "🛒 فروشگاه خالی است.")
        return
    text = "🛒 **فروشگاه گروه**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for item in items:
        stock_text = f"موجودی: {item[4]}" if item[4] > 0 else "نامحدود"
        text += f"#{item[0]} - {item[1]}: {item[2]:,} سکه\n📝 {item[3]}\n{stock_text}\n\n"
    text += "برای خرید: /خرید [شناسه]"
    bot.reply_to(message, text, parse_mode='HTML')

@register_command("خرید")
def buy_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ خرید [شناسه آیتم]")
        return
    try:
        item_id = int(args[1])
        user_id = message.from_user.id
        result = udb.buy_item(user_id, item_id)
        if result == "success":
            bot.reply_to(message, "✅ خرید با موفقیت انجام شد!")
            udb.check_achievements(user_id)
        elif result == "not_found":
            bot.reply_to(message, "❌ آیتم یافت نشد.")
        elif result == "out_of_stock":
            bot.reply_to(message, "❌ این آیتم تمام شده است.")
        elif result == "insufficient":
            bot.reply_to(message, "❌ سکه کافی ندارید!")
        else:
            bot.reply_to(message, "❌ خطا در خرید.")
    except:
        bot.reply_to(message, "❌ شناسه نامعتبر.")

@register_command("هدیه")
def gift_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️ هدیه [کاربر] [مقدار]")
        return
    try:
        target = args[1]
        amount = int(args[2])
        user_id = message.from_user.id
        if amount <= 0:
            bot.reply_to(message, "❌ مقدار باید مثبت باشد.")
            return
        target_id = None
        if target.isdigit():
            target_id = int(target)
        elif target.startswith('@'):
            try:
                member = bot.get_chat_member(message.chat.id, target)
                target_id = member.user.id
            except:
                pass
        else:
            bot.reply_to(message, "❌ کاربر را مشخص کنید.")
            return
        if user_id == target_id:
            bot.reply_to(message, "❌ نمی‌توانید به خودتان هدیه دهید.")
            return
        eco = udb.get_economy(user_id)
        if eco["coins"] < amount:
            bot.reply_to(message, f"❌ شما فقط {eco['coins']} سکه دارید.")
            return
        if udb.remove_coins(user_id, amount):
            udb.add_coins(target_id, amount)
            bot.reply_to(message, f"🎁 {amount} سکه به کاربر {target} هدیه داده شد!")
            udb.update_trust_score(user_id, 2)
            udb.check_achievements(user_id)
        else:
            bot.reply_to(message, "❌ خطا در هدیه.")
    except:
        bot.reply_to(message, "❌ خطا در پردازش.")

@register_command("شغل")
def job_command(message):
    user_id = message.from_user.id
    eco = udb.get_economy(user_id)
    user = udb.get_user(user_id)
    jobs = udb.get_job_list()
    text = f"💼 **شغل‌های موجود**\n━━━━━━━━━━━━━━━━━━━━━━\nشغل فعلی: {eco['job']}\n\n"
    for job in jobs:
        status = "✅" if job["name"] == eco["job"] else " "
        req = f"(سطح {job['level_req']})" if job["level_req"] > 1 else ""
        text += f"{status} {job['name']}: {job['base']} سکه پایه {req}\n"
    text += f"\nبرای تغییر شغل: /تغییر شغل [نام شغل]"
    text += f"\nسطح شما: {user['level']}"
    bot.reply_to(message, text, parse_mode='HTML')

@register_command("تغییر شغل")
def change_job_command(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ تغییر شغل [نام شغل]")
        return
    job_name = " ".join(args[1:])
    if udb.change_job(user_id, job_name):
        bot.reply_to(message, f"✅ شغل شما به {job_name} تغییر کرد.")
    else:
        bot.reply_to(message, "❌ شغل نامعتبر است یا سطح شما کافی نیست.")

# ===== سیستم ازدواج =====
@register_command("ازدواج")
def marry_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ ازدواج [کاربر]")
        return
    user_id = message.from_user.id
    target = args[1]
    target_id = None
    if target.isdigit():
        target_id = int(target)
    elif target.startswith('@'):
        try:
            member = bot.get_chat_member(message.chat.id, target)
            target_id = member.user.id
        except:
            pass
    if not target_id:
        bot.reply_to(message, "❌ کاربر را مشخص کنید.")
        return
    if user_id == target_id:
        bot.reply_to(message, "❌ نمی‌توانید با خودتان ازدواج کنید.")
        return
    result = udb.marry(user_id, target_id)
    if result == "success":
        bot.reply_to(message, f"💍 تبریک! شما با {target} ازدواج کردید!")
        udb.add_achievement(user_id, "married")
        udb.add_achievement(target_id, "married")
    elif result == "already_married":
        bot.reply_to(message, "❌ شما یا طرف مقابل قبلاً ازدواج کرده‌اید.")
    elif result == "self_marriage":
        bot.reply_to(message, "❌ نمی‌توانید با خودتان ازدواج کنید.")
    else:
        bot.reply_to(message, "❌ خطا در ازدواج.")

@register_command("طلاق")
def divorce_command(message):
    user_id = message.from_user.id
    result = udb.divorce(user_id)
    if result == "success":
        bot.reply_to(message, "💔 طلاق با موفقیت انجام شد.")
    elif result == "not_married":
        bot.reply_to(message, "❌ شما ازدواج نکرده‌اید.")
    elif result == "insufficient":
        bot.reply_to(message, f"❌ برای طلاق باید {udb.default_settings.get('divorce_cost', 100)} سکه داشته باشید.")
    else:
        bot.reply_to(message, "❌ خطا در طلاق.")

@register_command("وضعیت ازدواج")
def marriage_status_command(message):
    user_id = message.from_user.id
    marriage = udb.get_marriage(user_id)
    if marriage:
        other_id = marriage[1] if marriage[1] != user_id else marriage[2]
        try:
            user = bot.get_chat_member(message.chat.id, other_id).user
            name = user.first_name
        except:
            name = f"ID: {other_id}"
        date = datetime.fromtimestamp(marriage[3]).strftime('%Y-%m-%d')
        text = f"""
💕 **وضعیت ازدواج**
━━━━━━━━━━━━━━━━━━━━━━
💑 **همسر:** {name}
📅 **تاریخ ازدواج:** {date}
💖 **امتیاز عشق:** {marriage[5]}
━━━━━━━━━━━━━━━━━━━━━━
"""
        bot.reply_to(message, text, parse_mode='HTML')
    else:
        bot.reply_to(message, "❌ شما ازدواج نکرده‌اید.")

# ===== سیستم خانواده =====
@register_command("خانواده")
def family_command(message):
    user_id = message.from_user.id
    members = udb.get_family_members(user_id)
    if not members:
        bot.reply_to(message, "❌ شما عضو هیچ خانواده‌ای نیستید.")
        return
    text = "👨‍👩‍👧‍👦 **خانواده شما**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for member in members:
        if member[1] == user_id:
            child_id = member[2]
            relation = member[3]
            try:
                user = bot.get_chat_member(message.chat.id, child_id).user
                name = user.first_name
            except:
                name = f"ID: {child_id}"
            text += f"👶 فرزند {relation}: {name}\n"
        elif member[2] == user_id:
            parent_id = member[1]
            relation = member[3]
            try:
                user = bot.get_chat_member(message.chat.id, parent_id).user
                name = user.first_name
            except:
                name = f"ID: {parent_id}"
            text += f"👨‍👦 والد {relation}: {name}\n"
    bot.reply_to(message, text, parse_mode='HTML')

@register_command("افزودن فرزند")
def add_child_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ افزودن فرزند [کاربر]")
        return
    user_id = message.from_user.id
    target = args[1]
    target_id = None
    if target.isdigit():
        target_id = int(target)
    elif target.startswith('@'):
        try:
            member = bot.get_chat_member(message.chat.id, target)
            target_id = member.user.id
        except:
            pass
    if not target_id:
        bot.reply_to(message, "❌ کاربر را مشخص کنید.")
        return
    if udb.add_family_member(user_id, target_id):
        bot.reply_to(message, f"✅ {target} به عنوان فرزند شما اضافه شد.")
        udb.add_achievement(user_id, "has_child")
    else:
        bot.reply_to(message, "❌ این کاربر قبلاً فرزند شماست.")

# ===== سیستم رویدادها =====
@register_command("رویدادها")
def events_list_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    events = udb.get_events(group_id)
    if not events:
        bot.reply_to(message, "📭 هیچ رویدادی وجود ندارد.")
        return
    text = "📅 **رویدادهای گروه**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for event in events:
        date = datetime.fromtimestamp(event[3]).strftime('%Y-%m-%d %H:%M')
        text += f"#{event[0]} - {event[1]}\n📝 {event[2]}\n📅 {date}\n\n"
    bot.reply_to(message, text, parse_mode='HTML')

@register_command("رویداد")
def add_event_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    if not is_admin(message.from_user.id, group_id) and not is_bot_admin(message.from_user.id):
        bot.reply_to(message, "⛔ شما ادمین گروه نیستید!")
        return
    args = message.text.split('|')
    if len(args) < 3:
        bot.reply_to(message, "⚠️ رویداد [نام] | [توضیحات] | [زمان به ثانیه از حالا]")
        return
    name = args[0].strip().replace("رویداد", "").strip()
    desc = args[1].strip()
    try:
        delay = int(args[2].strip())
        event_date = int(time.time()) + delay
    except:
        bot.reply_to(message, "❌ زمان نامعتبر.")
        return
    event_id = udb.add_event(group_id, name, desc, event_date, message.from_user.id)
    bot.reply_to(message, f"✅ رویداد با شناسه {event_id} ایجاد شد.")

@register_command("لغو رویداد")
def cancel_event_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    if not is_admin(message.from_user.id, group_id) and not is_bot_admin(message.from_user.id):
        bot.reply_to(message, "⛔ شما ادمین گروه نیستید!")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ لغو رویداد [شناسه]")
        return
    try:
        event_id = int(args[1])
        udb.cancel_event(event_id)
        bot.reply_to(message, f"✅ رویداد {event_id} لغو شد.")
    except:
        bot.reply_to(message, "❌ شناسه نامعتبر.")

# ===== سیستم فیلتر کلمات =====
@register_command("افزودن فیلتر")
def add_filter_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    if not is_admin(message.from_user.id, group_id) and not is_bot_admin(message.from_user.id):
        bot.reply_to(message, "⛔ شما ادمین گروه نیستید!")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ افزودن فیلتر [کلمه]")
        return
    word = args[1]
    if udb.add_word_filter(group_id, word):
        bot.reply_to(message, f"✅ کلمه '{word}' به فیلترها اضافه شد.")
    else:
        bot.reply_to(message, "❌ این کلمه قبلاً در فیلترها وجود دارد.")

@register_command("حذف فیلتر")
def remove_filter_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    if not is_admin(message.from_user.id, group_id) and not is_bot_admin(message.from_user.id):
        bot.reply_to(message, "⛔ شما ادمین گروه نیستید!")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ حذف فیلتر [کلمه]")
        return
    word = args[1]
    udb.remove_word_filter(group_id, word)
    bot.reply_to(message, f"✅ کلمه '{word}' از فیلترها حذف شد.")

@register_command("لیست فیلترها")
def list_filters_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    filters = udb.get_word_filters(group_id)
    if not filters:
        bot.reply_to(message, "📭 هیچ فیلتری وجود ندارد.")
        return
    text = "📋 **فیلترهای کلمات**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for f in filters:
        text += f"• {f[2]} (فعل: {f[3]})\n"
    bot.reply_to(message, text, parse_mode='HTML')

# ===== سیستم نشان‌ها =====
@register_command("نشان‌ها")
def badges_command(message):
    user_id = message.from_user.id
    badges = udb.get_achievements(user_id)
    if not badges:
        bot.reply_to(message, "🎖️ شما هیچ نشان‌ای ندارید.")
        return
    text = "🎖️ **نشان‌های شما**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    badge_names = {
        "level_5": "⭐ سطح ۵",
        "level_10": "⭐ سطح ۱۰",
        "level_25": "⭐ سطح ۲۵",
        "level_50": "⭐ سطح ۵۰",
        "100_messages": "📨 ۱۰۰ پیام",
        "1000_messages": "📨 ۱۰۰۰ پیام",
        "7_day_streak": "🔥 استریک ۷ روزه",
        "30_day_streak": "🔥 استریک ۳۰ روزه",
        "earned_1000": "💰 ۱۰۰۰ سکه",
        "earned_10000": "💰 ۱۰۰۰۰ سکه",
        "married": "💍 ازدواج",
        "has_child": "👨‍👦 داشتن فرزند",
        "trusted_member": "🤝 عضو مورد اعتماد"
    }
    for badge in badges:
        name = badge_names.get(badge[1], badge[1])
        date = datetime.fromtimestamp(badge[2]).strftime('%Y-%m-%d')
        text += f"• {name} ({date})\n"
    bot.reply_to(message, text, parse_mode='HTML')

# ===== سیستم نقش‌ها =====
@register_command("نقش من")
def my_role_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    user_id = message.from_user.id
    role = udb.get_role(group_id, user_id)
    text = f"""
🔰 **نقش شما**
━━━━━━━━━━━━━━━━━━━━━━
👤 **نقش:** {role['role']}
🎨 **رنگ:** {role['color']}
━━━━━━━━━━━━━━━━━━━━━━
"""
    bot.reply_to(message, text, parse_mode='HTML')

@register_command("نقش‌ها")
def roles_list_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    if not is_admin(message.from_user.id, group_id) and not is_bot_admin(message.from_user.id):
        bot.reply_to(message, "⛔ شما ادمین گروه نیستید!")
        return
    roles = udb.get_role_list(group_id)
    if not roles:
        bot.reply_to(message, "📭 هیچ نقشی تعریف نشده است.")
        return
    text = "🔰 **نقش‌های گروه**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for role in roles:
        try:
            user = bot.get_chat_member(group_id, role[2]).user
            name = user.first_name
        except:
            name = f"ID: {role[2]}"
        text += f"• {role[3]} - {name}\n"
    bot.reply_to(message, text, parse_mode='HTML')

@register_command("نقش")
def assign_role_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    if not is_admin(message.from_user.id, group_id) and not is_bot_admin(message.from_user.id):
        bot.reply_to(message, "⛔ شما ادمین گروه نیستید!")
        return
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️ نقش [کاربر] [نقش]")
        return
    target = args[1]
    role_name = args[2]
    target_id = None
    if target.isdigit():
        target_id = int(target)
    elif target.startswith('@'):
        try:
            member = bot.get_chat_member(group_id, target)
            target_id = member.user.id
        except:
            pass
    if not target_id:
        bot.reply_to(message, "❌ کاربر را مشخص کنید.")
        return
    udb.assign_role(group_id, target_id, role_name)
    bot.reply_to(message, f"✅ نقش {role_name} به کاربر {target} اختصاص داده شد.")

# ===== سیستم هوش مصنوعی =====
@register_command("هوش مصنوعی")
def ai_chat_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ هوش مصنوعی [سوال یا پیام]")
        return
    question = " ".join(args[1:])
    response = asyncio.run(udb.get_ai_response(user_id, question))
    bot.reply_to(message, response)

# ===== سیستم زمان‌بندی =====
@register_command("زمان‌بندی")
def schedule_message_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    if not is_admin(message.from_user.id, group_id) and not is_bot_admin(message.from_user.id):
        bot.reply_to(message, "⛔ شما ادمین گروه نیستید!")
        return
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️ زمان‌بندی [زمان به ثانیه] [پیام]")
        return
    try:
        delay = int(args[1])
        msg = " ".join(args[2:])
        scheduled_time = int(time.time()) + delay
        udb.add_scheduled_message(group_id, msg, scheduled_time)
        bot.reply_to(message, f"✅ پیام در {format_duration(delay)} ارسال خواهد شد.")
    except:
        bot.reply_to(message, "❌ زمان نامعتبر.")

# ===== سایر دستورات مدیریت =====
@register_command("تنظیمات")
def settings_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    if not is_admin(message.from_user.id, group_id) and not is_bot_admin(message.from_user.id):
        bot.reply_to(message, "⛔ شما ادمین گروه نیستید!")
        return
    bot.reply_to(message, "⚙️ **تنظیمات پیشرفته گروه:**", reply_markup=settings_menu(group_id), parse_mode='HTML')

@register_command("آمار")
def stats_command(message):
    if not message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "❌ این دستور فقط در گروه قابل استفاده است.")
        return
    group_id = message.chat.id
    if not is_admin(message.from_user.id, group_id) and not is_bot_admin(message.from_user.id):
        bot.reply_to(message, "⛔ شما ادمین گروه نیستید!")
        return
    try:
        members = bot.get_chat_members_count(group_id)
    except:
        members = "نامشخص"
    total_warns = udb.stats.get('total_warns', 0)
    total_muted = sum(1 for user in [udb.get_user(uid) for uid in set([row[0] for row in db.fetch_all("SELECT user_id FROM users")])] if udb.is_muted(user["user_id"]))
    text = f"""
📊 **آمار پیشرفته گروه**
━━━━━━━━━━━━━━━━━━━━━━
👥 **تعداد اعضا:** {members}
📨 **پیام‌ها:** {udb.stats.get('total_messages', 0):,}
🚫 **اخراجی‌ها:** {udb.stats.get('total_kicks', 0):,}
🔨 **بن‌ها:** {udb.stats.get('total_bans', 0):,}
🔇 **میوت‌ها:** {udb.stats.get('total_mutes', 0):,}
⚠️ **اخطارها:** {udb.stats.get('total_warns', 0):,}
🔐 **کپچا موفق:** {udb.stats.get('captcha_passed', 0):,}
❌ **کپچا ناموفق:** {udb.stats.get('captcha_failed', 0):,}
🔇 **میوت:** {total_muted}
🎫 **تیکت‌ها:** {len(udb.tickets.get(group_id, []))}
📋 **گزارش‌ها:** {len(udb.get_reports(group_id))}
🏅 **مسابقات فعال:** {len(db.fetch_all("SELECT id FROM contests WHERE group_id = ? AND status = 'active'", (group_id,)))}
💰 **اقتصاد:** {len(db.fetch_all("SELECT * FROM economy"))} کاربر
💑 **ازدواج:** {len(db.fetch_all("SELECT * FROM marriages WHERE status = 'active'"))}
━━━━━━━━━━━━━━━━━━━━━━
"""
    bot.reply_to(message, text, reply_markup=back_button(), parse_mode='HTML')

# ========== مدیریت اعضای جدید ==========
@bot.chat_member_handler()
def handle_new_member(chat_member_update: ChatMemberUpdated):
    chat = chat_member_update.chat
    if chat.type not in ['group', 'supergroup']:
        return
    group_id = chat.id
    new = chat_member_update.new_chat_member
    old = chat_member_update.old_chat_member
    
    if new.status == "member" and old.status in ["left", "kicked"]:
        user = new.user
        if user.is_bot:
            settings = udb.get_group(group_id)
            if settings.get('anti_bot', True):
                try:
                    bot.ban_chat_member(group_id, user.id)
                    udb.stats["total_bans"] += 1
                    udb._save_stats()
                    bot.send_message(group_id, f"🤖 ربات {user.first_name} شناسایی و بن شد.")
                except:
                    pass
            return
        
        user_id = user.id
        settings = udb.get_group(group_id)
        user_data = udb.get_user(user_id)
        user_data["join_date"] = int(time.time())
        user_data["first_name"] = user.first_name
        user_data["username"] = user.username
        udb.save_user(user_data)
        
        if settings.get('anomaly_detection', True):
            behavior = udb.user_behavior[user_id]
            behavior["last_join"] = int(time.time())
            behavior["join_count"] += 1
            if behavior["join_count"] > 3 and settings.get('instant_ban_on_suspicious', True):
                try:
                    bot.ban_chat_member(group_id, user_id)
                    bot.send_message(group_id, f"🚨 کاربر {user.first_name} به دلیل فعالیت مشکوک بن شد.")
                except:
                    pass
                return
        
        if settings.get('anti_raid', True):
            join_count = len(udb.join_times[group_id])
            udb.join_times[group_id].append(time.time())
            now = time.time()
            udb.join_times[group_id] = [t for t in udb.join_times[group_id] if now - t < 10]
            if len(udb.join_times[group_id]) >= settings.get('raid_threshold', 5):
                action = settings.get('raid_action', 'kick')
                try:
                    if action == "kick":
                        bot.ban_chat_member(group_id, user_id)
                        bot.unban_chat_member(group_id, user_id)
                        udb.stats["total_kicks"] += 1
                    elif action == "ban":
                        bot.ban_chat_member(group_id, user_id)
                        udb.stats["total_bans"] += 1
                    udb._save_stats()
                except:
                    pass
                return
        
        if settings.get('captcha', True):
            num1 = random.randint(1, 15)
            num2 = random.randint(1, 15)
            answer = num1 + num2
            udb.save_captcha(user_id, group_id, answer)
            
            bot.send_message(
                group_id,
                f"🔐 {get_user_mention(user)}، لطفاً برای اثبات اینکه ربات نیستی، پاسخ این معادله را بفرست:\n\n{num1} + {num2} = ?\n\n⏳ شما {settings.get('captcha_timeout', 60)} ثانیه فرصت دارید.",
                parse_mode='HTML'
            )
            
            def captcha_timeout():
                captcha_data = udb.get_captcha(user_id)
                if captcha_data and captcha_data["group_id"] == group_id:
                    try:
                        bot.ban_chat_member(group_id, user_id)
                        bot.unban_chat_member(group_id, user_id)
                        udb.stats["captcha_failed"] += 1
                        udb._save_stats()
                        bot.send_message(group_id, f"⏰ {get_user_mention(user)} زمان کپچا تمام شد، اخراج شد.", parse_mode='HTML')
                    except:
                        pass
                    udb.delete_captcha(user_id)
            
            threading.Timer(settings.get('captcha_timeout', 60), captcha_timeout).start()
        
        if settings.get('two_factor_auth', False):
            code = udb.generate_2fa_code(user_id)
            try:
                bot.send_message(user_id, f"🔑 کد تأیید دو مرحله‌ای شما: {code}\nاین کد را در گروه وارد کنید تا تأیید شوید.")
                bot.send_message(group_id, f"🔐 {get_user_mention(user)} یک کد تأیید به پیوی شما ارسال شد. لطفاً آن را در گروه وارد کنید.", parse_mode='HTML')
            except:
                bot.send_message(group_id, f"⚠️ {get_user_mention(user)} نمی‌توانم به شما پیام خصوصی بفرستم. لطفاً ربات را استارت کنید.", parse_mode='HTML')
        
        if settings.get('welcome_enabled', True):
            welcome_text = settings.get('welcome', '👋 به گروه خوش آمدید {user_name}!').replace("{user_name}", user.first_name)
            welcome_photo = settings.get('welcome_photo')
            if welcome_photo:
                try:
                    bot.send_photo(group_id, welcome_photo, caption=welcome_text, parse_mode='HTML')
                except:
                    bot.send_message(group_id, welcome_text, parse_mode='HTML')
            else:
                bot.send_message(group_id, welcome_text, parse_mode='HTML')

# ========== پاسخ به کپچا و 2FA ==========
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and message.text and message.text.lstrip('-').isdigit())
def captcha_or_2fa_answer(message):
    user_id = message.from_user.id
    group_id = message.chat.id
    
    captcha_data = udb.get_captcha(user_id)
    if captcha_data and captcha_data["group_id"] == group_id:
        if int(message.text) == captcha_data["answer"]:
            udb.delete_captcha(user_id)
            udb.stats["captcha_passed"] += 1
            udb._save_stats()
            udb.verify_user(user_id)
            udb.update_trust_score(user_id, 5)
            bot.reply_to(message, "✅ کپچا صحیح بود! خوش آمدید.")
            udb.check_achievements(user_id)
        else:
            attempts = udb.increment_captcha_attempts(user_id)
            settings = udb.get_group(group_id)
            max_attempts = settings.get('captcha_max_attempts', 3)
            if attempts >= max_attempts:
                try:
                    bot.ban_chat_member(group_id, user_id)
                    bot.unban_chat_member(group_id, user_id)
                    udb.stats["captcha_failed"] += 1
                    udb._save_stats()
                    udb.update_trust_score(user_id, -20)
                    bot.reply_to(message, f"❌ تعداد تلاش‌های شما بیش از حد مجاز بود، اخراج شدید.")
                except:
                    pass
                udb.delete_captcha(user_id)
            else:
                bot.reply_to(message, f"❌ پاسخ نادرست! تلاش {attempts}/{max_attempts}")
        return
    
    user = udb.get_user(user_id)
    if user["is_2fa_verified"] == 0 and user["twofa_code"]:
        if udb.verify_2fa(user_id, message.text):
            bot.reply_to(message, "✅ تأیید دو مرحله‌ای با موفقیت انجام شد. خوش آمدید!")
            udb.verify_user(user_id)
            udb.update_trust_score(user_id, 10)
        else:
            bot.reply_to(message, "❌ کد تأیید نامعتبر است. دوباره تلاش کنید.")

# ========== مدیریت پیام‌ها ==========
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'animation', 'poll', 'dice', 'contact', 'location', 'venue', 'voice_chat_started', 'voice_chat_scheduled'])
def handle_message(message):
    if not message.chat.type in ['group', 'supergroup']:
        return
    
    group_id = message.chat.id
    user = message.from_user
    user_id = user.id
    
    if message.text and any(message.text.startswith(cmd) for cmd in command_handlers):
        return
    
    if is_admin(user_id, group_id) or user.is_bot:
        return
    
    settings = udb.get_group(group_id)
    
    # بررسی AFK
    if settings.get('afk_enabled', True):
        if message.reply_to_message and message.reply_to_message.from_user:
            replied_user = message.reply_to_message.from_user.id
            if udb.is_afk(replied_user):
                status = udb.get_afk_status(replied_user)
                bot.reply_to(message, f"🔇 کاربر مورد نظر AFK است: {status}")
    
    if udb.is_blacklisted(group_id, user_id):
        try:
            bot.ban_chat_member(group_id, user_id)
            bot.send_message(group_id, f"🚫 {get_user_mention(user)} در لیست سیاه است و بن شد.", parse_mode='HTML')
        except:
            pass
        return
    
    if udb.is_whitelisted(group_id, user_id):
        return
    
    if settings.get('silent_mode', False):
        try:
            bot.delete_message(group_id, message.message_id)
            bot.send_message(group_id, f"🔇 {get_user_mention(user)} گروه در حالت سکوت است. فقط ادمین‌ها می‌توانند پیام بفرستند.", parse_mode='HTML')
        except:
            pass
        return
    
    if settings.get('group_lock', False):
        try:
            bot.delete_message(group_id, message.message_id)
            bot.send_message(group_id, f"🔒 {get_user_mention(user)} گروه قفل است!", parse_mode='HTML')
        except:
            pass
        return
    
    if udb.is_muted(user_id):
        try:
            bot.delete_message(group_id, message.message_id)
            remaining = udb.get_mute_remaining(user_id)
            bot.send_message(group_id, f"🔇 {get_user_mention(user)} شما میوت هستید! ({format_duration(remaining)} باقی مانده)", parse_mode='HTML')
        except:
            pass
        return
    
    if udb.is_temp_banned(user_id):
        try:
            bot.delete_message(group_id, message.message_id)
            bot.send_message(group_id, f"🔨 {get_user_mention(user)} شما بن موقت هستید!", parse_mode='HTML')
        except:
            pass
        return
    
    # تشخیص ناهنجاری
    if settings.get('anomaly_detection', True):
        result = udb.analyze_behavior(user_id, "message")
        if result == "suspicious" and settings.get('instant_ban_on_suspicious', True):
            try:
                bot.ban_chat_member(group_id, user_id)
                bot.send_message(group_id, f"🚨 {get_user_mention(user)} به دلیل رفتار مشکوک بن شد.", parse_mode='HTML')
            except:
                pass
            return
    
    # تشخیص الگو
    if settings.get('pattern_recognition', True) and message.text:
        pattern = udb.detect_pattern(user_id, message.text)
        if pattern == "pattern_detected":
            bot.send_message(group_id, f"⚠️ {get_user_mention(user)} الگوی پیام تکراری شناسایی شد.", parse_mode='HTML')
    
    # فیلتر کلمات
    if settings.get('word_filter_enabled', True) and message.text:
        action = udb.check_word_filters(group_id, message.text)
        if action:
            try:
                bot.delete_message(group_id, message.message_id)
                if action == "delete":
                    bot.send_message(group_id, f"⚠️ {get_user_mention(user)} پیام شما حاوی کلمه ممنوعه است.", parse_mode='HTML')
                elif action == "mute":
                    udb.set_mute(user_id, 300)
                    bot.send_message(group_id, f"🔇 {get_user_mention(user)} به دلیل کلمه ممنوعه میوت شد.", parse_mode='HTML')
                elif action == "ban":
                    bot.ban_chat_member(group_id, user_id)
                    bot.send_message(group_id, f"🔨 {get_user_mention(user)} به دلیل کلمه ممنوعه بن شد.", parse_mode='HTML')
                udb.update_trust_score(user_id, -5)
            except:
                pass
            return
    
    # تشخیص کلاهبرداری Web3
    if settings.get('anti_web3_scam', True) and message.text and detect_web3_scam(message.text):
        try:
            bot.delete_message(group_id, message.message_id)
            bot.ban_chat_member(group_id, user_id)
            bot.send_message(group_id, f"🚨 {get_user_mention(user)} کلاهبرداری Web3 شناسایی شد! بن شد.", parse_mode='HTML')
            udb.update_trust_score(user_id, -30)
        except:
            pass
        return
    
    # تشخیص تلگرام جعلی
    if settings.get('anti_fake_telegram', True) and message.text and detect_fake_telegram(message.text):
        try:
            bot.delete_message(group_id, message.message_id)
            bot.ban_chat_member(group_id, user_id)
            bot.send_message(group_id, f"🚨 {get_user_mention(user)} لینک تلگرام جعلی شناسایی شد! بن شد.", parse_mode='HTML')
            udb.update_trust_score(user_id, -30)
        except:
            pass
        return
    
    # تشخیص محتوای سمی
    if settings.get('toxicity_filter_enabled', True) and message.text and detect_toxic_content(message.text):
        try:
            bot.delete_message(group_id, message.message_id)
            udb.set_mute(user_id, 600)
            bot.send_message(group_id, f"⚠️ {get_user_mention(user)} محتوای سمی شناسایی شد. میوت شدید.", parse_mode='HTML')
            udb.update_trust_score(user_id, -10)
        except:
            pass
        return
    
    # ضد Ghost Ping
    if settings.get('anti_ghost_ping', True) and message.text:
        if "@" in message.text and not any(u.username in message.text for u in bot.get_chat_members(group_id)):
            try:
                bot.delete_message(group_id, message.message_id)
                action = settings.get('ghost_ping_action', 'warn')
                if action == "warn":
                    udb.add_warning(group_id, user_id, "Ghost Ping")
                elif action == "mute":
                    udb.set_mute(user_id, 300)
                bot.send_message(group_id, f"⚠️ {get_user_mention(user)} Ghost Ping ممنوع!", parse_mode='HTML')
            except:
                pass
            return
    
    # امتیاز مکالمه صوتی
    if settings.get('voice_xp_enabled', True) and is_voice_call(message):
        xp = udb.add_voice_xp(user_id, 60)
        if xp > 0:
            bot.send_message(group_id, f"🎤 {get_user_mention(user)} +{xp} XP از مکالمه صوتی!", parse_mode='HTML')
    
    # اسپم
    if settings.get('anti_spam', True) and message.text:
        udb.add_message(user_id, message.text)
        count = udb.get_message_count(user_id, 1)
        threshold = settings.get('spam_threshold', 3)
        if count >= threshold:
            action = settings.get('spam_action', 'mute')
            try:
                bot.delete_message(group_id, message.message_id)
                if action == "mute":
                    duration = settings.get('spam_duration', 300)
                    udb.set_mute(user_id, duration)
                    udb.stats["total_mutes"] += 1
                    bot.send_message(group_id, f"🔇 {get_user_mention(user)} به دلیل اسپم به مدت {format_duration(duration)} میوت شد.", parse_mode='HTML')
                elif action == "kick":
                    bot.ban_chat_member(group_id, user_id)
                    bot.unban_chat_member(group_id, user_id)
                    udb.stats["total_kicks"] += 1
                    bot.send_message(group_id, f"👢 {get_user_mention(user)} به دلیل اسپم اخراج شد.", parse_mode='HTML')
                elif action == "ban":
                    bot.ban_chat_member(group_id, user_id)
                    udb.stats["total_bans"] += 1
                    bot.send_message(group_id, f"🔨 {get_user_mention(user)} به دلیل اسپم بن شد.", parse_mode='HTML')
                udb._save_stats()
                udb.update_trust_score(user_id, -5)
            except:
                pass
            return
    
    # بیزین اسپم
    if settings.get('anti_spam_bayesian', True) and message.text:
        prob = udb.bayesian_spam_probability(message.text)
        if prob > settings.get('spam_probability_threshold', 0.6):
            try:
                bot.delete_message(group_id, message.message_id)
                bot.send_message(group_id, f"🔇 {get_user_mention(user)} پیام شما به عنوان اسپم شناسایی شد.", parse_mode='HTML')
                udb.set_mute(user_id, 300)
                udb.stats["total_mutes"] += 1
                udb._save_stats()
                udb.update_trust_score(user_id, -5)
            except:
                pass
            return
    
    # تشخیص پیام تکراری
    if settings.get('duplicate_message_detection', True) and message.text:
        if udb.is_duplicate_message(user_id, message.text):
            try:
                bot.delete_message(group_id, message.message_id)
                bot.send_message(group_id, f"⚠️ {get_user_mention(user)} لطفاً پیام تکراری نفرستید!", parse_mode='HTML')
                udb.set_mute(user_id, 60)
                udb.stats["total_mutes"] += 1
                udb._save_stats()
                udb.update_trust_score(user_id, -3)
            except:
                pass
            return
    
    # ضد لینک
    if settings.get('anti_link', True) and message.text and contains_link(message.text):
        links = extract_links(message.text)
        whitelist = settings.get('anti_link_whitelist', [])
        is_whitelisted = any(any(w in link for w in whitelist) for link in links)
        is_malicious = any(udb.is_malicious_domain(link) for link in links)
        
        if not is_whitelisted:
            try:
                bot.delete_message(group_id, message.message_id)
                if is_malicious:
                    bot.send_message(group_id, f"⛔ {get_user_mention(user)} لینک مخرب شناسایی شد! شما بن شدید.", parse_mode='HTML')
                    bot.ban_chat_member(group_id, user_id)
                    udb.stats["total_bans"] += 1
                    udb._save_stats()
                    udb.update_trust_score(user_id, -20)
                else:
                    action = settings.get('anti_link_action', 'warn')
                    if action == "warn":
                        count = udb.add_warning(group_id, user_id, "ارسال لینک ممنوع")
                        bot.send_message(group_id, f"⚠️ {get_user_mention(user)} لطفاً لینک نفرستید! (اخطار {count})", parse_mode='HTML')
                    elif action == "mute":
                        udb.set_mute(user_id, 300)
                        udb.stats["total_mutes"] += 1
                        bot.send_message(group_id, f"🔇 {get_user_mention(user)} به دلیل ارسال لینک میوت شد.", parse_mode='HTML')
                    elif action == "kick":
                        bot.ban_chat_member(group_id, user_id)
                        bot.unban_chat_member(group_id, user_id)
                        udb.stats["total_kicks"] += 1
                        bot.send_message(group_id, f"👢 {get_user_mention(user)} به دلیل ارسال لینک اخراج شد.", parse_mode='HTML')
                    elif action == "ban":
                        bot.ban_chat_member(group_id, user_id)
                        udb.stats["total_bans"] += 1
                        bot.send_message(group_id, f"🔨 {get_user_mention(user)} به دلیل ارسال لینک بن شد.", parse_mode='HTML')
                    udb._save_stats()
                    udb.update_trust_score(user_id, -5)
            except:
                pass
            return
    
    # ضد فحش
    if settings.get('anti_bad_words', True) and message.text and contains_bad_words(message.text):
        try:
            bot.delete_message(group_id, message.message_id)
            action = settings.get('anti_bad_words_action', 'mute')
            if action == "mute":
                duration = settings.get('anti_bad_words_duration', 600)
                udb.set_mute(user_id, duration)
                udb.stats["total_mutes"] += 1
                bot.send_message(group_id, f"🔇 {get_user_mention(user)} به دلیل استفاده از الفاظ نامناسب میوت شد.", parse_mode='HTML')
            elif action == "kick":
                bot.ban_chat_member(group_id, user_id)
                bot.unban_chat_member(group_id, user_id)
                udb.stats["total_kicks"] += 1
                bot.send_message(group_id, f"👢 {get_user_mention(user)} به دلیل فحش اخراج شد.", parse_mode='HTML')
            elif action == "ban":
                bot.ban_chat_member(group_id, user_id)
                udb.stats["total_bans"] += 1
                bot.send_message(group_id, f"🔨 {get_user_mention(user)} به دلیل فحش بن شد.", parse_mode='HTML')
            else:
                count = udb.add_warning(group_id, user_id, "فحش و الفاظ نامناسب")
                bot.send_message(group_id, f"⚠️ {get_user_mention(user)} لطفاً از الفاظ مناسب استفاده کنید! (اخطار {count})", parse_mode='HTML')
            udb._save_stats()
            udb.update_trust_score(user_id, -10)
        except:
            pass
        return
    
    # ضد تبلیغات
    if settings.get('anti_advertising', True) and message.text and contains_ad_keywords(message.text):
        try:
            bot.delete_message(group_id, message.message_id)
            action = settings.get('anti_advertising_action', 'kick')
            if action == "kick":
                bot.ban_chat_member(group_id, user_id)
                bot.unban_chat_member(group_id, user_id)
                udb.stats["total_kicks"] += 1
                bot.send_message(group_id, f"👢 {get_user_mention(user)} به دلیل تبلیغات اخراج شد.", parse_mode='HTML')
            elif action == "ban":
                bot.ban_chat_member(group_id, user_id)
                udb.stats["total_bans"] += 1
                bot.send_message(group_id, f"🔨 {get_user_mention(user)} به دلیل تبلیغات بن شد.", parse_mode='HTML')
            else:
                count = udb.add_warning(group_id, user_id, "تبلیغات")
                bot.send_message(group_id, f"⚠️ {get_user_mention(user)} لطفاً تبلیغ نفرستید! (اخطار {count})", parse_mode='HTML')
            udb._save_stats()
            udb.update_trust_score(user_id, -5)
        except:
            pass
        return
    
    # محتوای حساس
    content_violations = []
    if settings.get('anti_porn', True) and message.text and udb.detect_porn(message.text):
        content_violations.append("محتوای بزرگسالان")
    if settings.get('anti_violence', True) and message.text and udb.detect_violence(message.text):
        content_violations.append("خشونت")
    if settings.get('anti_drugs', True) and message.text and udb.detect_drugs(message.text):
        content_violations.append("مواد مخدر")
    if settings.get('anti_hate', True) and message.text and udb.detect_hate(message.text):
        content_violations.append("نفرت")
    if settings.get('anti_phishing', True) and message.text and udb.detect_phishing(message.text):
        content_violations.append("فیشینگ")
    if settings.get('anti_malware', True) and message.text and udb.detect_malware(message.text):
        content_violations.append("بدافزار")
    if settings.get('anti_terrorism', True) and message.text and udb.detect_terrorism(message.text):
        content_violations.append("تروریسم")
    if settings.get('anti_child_abuse', True) and message.text and udb.detect_child_abuse(message.text):
        content_violations.append("آزار کودکان")
    if settings.get('anti_crypto', True) and message.text and udb.detect_crypto_scam(message.text):
        content_violations.append("کلاهبرداری رمزارز")
    if settings.get('anti_gambling', True) and message.text and udb.detect_gambling(message.text):
        content_violations.append("قمار")
    
    if content_violations:
        try:
            bot.delete_message(group_id, message.message_id)
            bot.send_message(group_id, f"⛔ {get_user_mention(user)} پیام شما حاوی محتوای ممنوعه است: {', '.join(content_violations)}", parse_mode='HTML')
            udb.set_mute(user_id, 600)
            udb.stats["total_mutes"] += 1
            udb._save_stats()
            udb.update_trust_score(user_id, -15)
            udb.add_warning(group_id, user_id, f"محتوای ممنوعه: {', '.join(content_violations)}")
        except:
            pass
        return
    
    # پاسخ خودکار
    if message.text:
        auto_reply = udb.get_auto_reply(group_id, message.text.lower())
        if auto_reply:
            bot.send_message(group_id, auto_reply[3])
    
    # سیستم سطح
    if settings.get('leveling', True):
        if udb.add_xp(user_id, 1):
            level = udb.get_level(user_id)
            level_message = settings.get('level_message', '🎉 {user_name} به سطح {level} رسید!').replace("{user_name}", user.first_name).replace("{level}", str(level))
            bot.send_message(group_id, level_message, parse_mode='HTML')
            udb.check_achievements(user_id)
    
    # سیستم اعتماد
    if settings.get('trust_system_enabled', True):
        udb.update_trust_score(user_id, 1)
    
    # حذف خودکار
    if settings.get('auto_delete', True):
        def delete_later():
            try:
                bot.delete_message(group_id, message.message_id)
            except:
                pass
        threading.Timer(settings.get('auto_delete_seconds', 43200), delete_later).start()
    
    # هوش مصنوعی
    if settings.get('ai_assistant_enabled', True) and message.text:
        if udb.get_trust_score(user_id) >= udb.default_settings.get('user_trust_minimum', 10):
            if random.random() < 0.1:
                response = asyncio.run(udb.get_ai_response(user_id, message.text))
                if response and not response.startswith("🤖"):
                    bot.send_message(group_id, f"🤖 {response}")
    
    udb.stats["total_messages"] += 1
    udb._save_stats()

# ========== کال‌بک‌ها ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data
    group_id = chat_id if call.message.chat.type in ['group', 'supergroup'] else None

    if group_id is not None:
        settings = udb.get_group(group_id)
        if settings.get('button_access_locked', True) and not is_admin(user_id, group_id) and not is_bot_admin(user_id):
            bot.answer_callback_query(call.id, "⛔ دسترسی به دکمه‌ها برای اعضا قفل است.")
            return

    if data == "back_main":
        bot.edit_message_text("✨ **منوی اصلی**", chat_id, call.message.message_id, reply_markup=main_menu(), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    # ===== تنظیمات =====
    if data.startswith("toggle_afk_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["afk_enabled"] = not settings.get("afk_enabled", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🔰 تنظیمات پایه", chat_id, call.message.message_id, reply_markup=basic_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_goodbye_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["goodbye_enabled"] = not settings.get("goodbye_enabled", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🔰 تنظیمات پایه", chat_id, call.message.message_id, reply_markup=basic_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_ghostping_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["anti_ghost_ping"] = not settings.get("anti_ghost_ping", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🛡️ تنظیمات ضد اسپم", chat_id, call.message.message_id, reply_markup=spam_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_web3_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["anti_web3_scam"] = not settings.get("anti_web3_scam", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🔐 تنظیمات امنیت", chat_id, call.message.message_id, reply_markup=security_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_faketg_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["anti_fake_telegram"] = not settings.get("anti_fake_telegram", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🔐 تنظیمات امنیت", chat_id, call.message.message_id, reply_markup=security_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_voicexp_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["voice_xp_enabled"] = not settings.get("voice_xp_enabled", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🎯 تنظیمات پیشرفته", chat_id, call.message.message_id, reply_markup=advanced_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_trust_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["trust_system_enabled"] = not settings.get("trust_system_enabled", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🎯 تنظیمات پیشرفته", chat_id, call.message.message_id, reply_markup=advanced_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_wordfilter_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["word_filter_enabled"] = not settings.get("word_filter_enabled", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🌟 تنظیمات فوق‌پیشرفته", chat_id, call.message.message_id, reply_markup=ultra_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_anomaly_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["anomaly_detection"] = not settings.get("anomaly_detection", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🌟 تنظیمات فوق‌پیشرفته", chat_id, call.message.message_id, reply_markup=ultra_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_proactive_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["proactive_security"] = not settings.get("proactive_security", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🌟 تنظیمات فوق‌پیشرفته", chat_id, call.message.message_id, reply_markup=ultra_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("toggle_autoheal_"):
        gid = int(data.split("_")[2])
        settings = udb.get_group(gid)
        settings["auto_healing"] = not settings.get("auto_healing", True)
        udb.save_group(gid, settings)
        bot.answer_callback_query(call.id, "✅ تنظیمات ذخیره شد.")
        bot.edit_message_text("🌟 تنظیمات فوق‌پیشرفته", chat_id, call.message.message_id, reply_markup=ultra_settings_menu(gid), parse_mode='HTML')
        return
    
    if data.startswith("ai_"):
        gid = int(data.split("_")[1])
        bot.edit_message_text("🧠 **تنظیمات هوش مصنوعی**", chat_id, call.message.message_id, reply_markup=ai_settings_menu(gid), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    # ===== منوهای جدید =====
    if data == "economy":
        bot.edit_message_text("💰 **سیستم اقتصاد**", chat_id, call.message.message_id, reply_markup=economy_menu(user_id), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if data == "marriage":
        bot.edit_message_text("💑 **سیستم ازدواج**", chat_id, call.message.message_id, reply_markup=marriage_menu(user_id), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if data == "family":
        bot.edit_message_text("👨‍👩‍👧‍👦 **سیستم خانواده**", chat_id, call.message.message_id, reply_markup=family_menu(user_id), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if data == "events":
        if not group_id:
            bot.answer_callback_query(call.id, "❌ این بخش فقط در گروه قابل استفاده است.")
            return
        bot.edit_message_text("📅 **رویدادها**", chat_id, call.message.message_id, reply_markup=events_menu(group_id), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if data == "badges":
        badges = udb.get_achievements(user_id)
        if not badges:
            bot.answer_callback_query(call.id, "🎖️ شما هیچ نشان‌ای ندارید.")
            return
        text = "🎖️ **نشان‌های شما**\n━━━━━━━━━━━━━━━━━━━━━━\n"
        badge_names = {
            "level_5": "⭐ سطح ۵",
            "level_10": "⭐ سطح ۱۰",
            "level_25": "⭐ سطح ۲۵",
            "level_50": "⭐ سطح ۵۰",
            "100_messages": "📨 ۱۰۰ پیام",
            "1000_messages": "📨 ۱۰۰۰ پیام",
            "7_day_streak": "🔥 استریک ۷ روزه",
            "30_day_streak": "🔥 استریک ۳۰ روزه",
            "earned_1000": "💰 ۱۰۰۰ سکه",
            "earned_10000": "💰 ۱۰۰۰۰ سکه",
            "married": "💍 ازدواج",
            "has_child": "👨‍👦 داشتن فرزند",
            "trusted_member": "🤝 عضو مورد اعتماد"
        }
        for badge in badges:
            name = badge_names.get(badge[1], badge[1])
            date = datetime.fromtimestamp(badge[2]).strftime('%Y-%m-%d')
            text += f"• {name} ({date})\n"
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=back_button(), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if data == "roles":
        if not group_id:
            bot.answer_callback_query(call.id, "❌ این بخش فقط در گروه قابل استفاده است.")
            return
        if not is_admin(user_id, group_id) and not is_bot_admin(user_id):
            bot.answer_callback_query(call.id, "⛔ فقط ادمین‌ها می‌توانند نقش‌ها را ببینند.")
            return
        roles = udb.get_role_list(group_id)
        if not roles:
            bot.edit_message_text("📭 هیچ نقشی تعریف نشده است.", chat_id, call.message.message_id, reply_markup=back_button())
        else:
            text = "🔰 **نقش‌های گروه**\n━━━━━━━━━━━━━━━━━━━━━━\n"
            for role in roles:
                try:
                    user = bot.get_chat_member(group_id, role[2]).user
                    name = user.first_name
                except:
                    name = f"ID: {role[2]}"
                text += f"• {role[3]} - {name}\n"
            bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=back_button(), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if data == "ai_chat":
        bot.send_message(chat_id, "🧠 با استفاده از دستور /هوش مصنوعی [سوال] با من گفتگو کنید.")
        bot.answer_callback_query(call.id)
        return
    
    # ===== کال‌بک‌های اقتصاد =====
    if data.startswith("eco_balance_"):
        uid = int(data.split("_")[2])
        eco = udb.get_economy(uid)
        user = udb.get_user(uid)
        text = f"""
💰 **موجودی شما**
━━━━━━━━━━━━━━━━━━━━━━
🪙 **سکه:** {eco['coins']:,}
🏦 **بانک:** {eco['bank']:,}
💼 **شغل:** {eco['job']}
📈 **سطح شغل:** {eco['job_level']}
💰 **کل درآمد:** {eco['total_earned']:,}
💸 **کل هزینه:** {eco['total_spent']:,}
━━━━━━━━━━━━━━━━━━━━━━
"""
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=economy_menu(uid), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("eco_work_"):
        uid = int(data.split("_")[2])
        earn = udb.work(uid)
        if earn is None:
            eco = udb.get_economy(uid)
            remaining = udb.default_settings.get('economy_work_cooldown', 3600) - (int(time.time()) - eco["last_work"])
            bot.answer_callback_query(call.id, f"⏳ {format_duration(max(0, remaining))} باقی مانده")
        else:
            udb.add_xp(uid, earn // 10)
            bot.answer_callback_query(call.id, f"💼 {earn} سکه کار کردید! +{earn//10} XP")
            eco = udb.get_economy(uid)
            text = f"""
💰 **موجودی جدید**
━━━━━━━━━━━━━━━━━━━━━━
🪙 **سکه:** {eco['coins']:,}
💼 **شغل:** {eco['job']}
━━━━━━━━━━━━━━━━━━━━━━
"""
            bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=economy_menu(uid), parse_mode='HTML')
        return
    
    if data.startswith("eco_bank_"):
        uid = int(data.split("_")[2])
        bot.answer_callback_query(call.id, "🏦 سیستم بانک در حال توسعه است.")
        return
    
    if data.startswith("eco_shop_"):
        if not group_id:
            bot.answer_callback_query(call.id, "❌ این بخش فقط در گروه قابل استفاده است.")
            return
        items = udb.get_shop_items(group_id)
        if not items:
            bot.edit_message_text("🛒 فروشگاه خالی است.", chat_id, call.message.message_id, reply_markup=economy_menu(user_id))
        else:
            text = "🛒 **فروشگاه گروه**\n━━━━━━━━━━━━━━━━━━━━━━\n"
            for item in items:
                stock_text = f"موجودی: {item[4]}" if item[4] > 0 else "نامحدود"
                text += f"#{item[0]} - {item[1]}: {item[2]:,} سکه\n📝 {item[3]}\n{stock_text}\n\n"
            text += "برای خرید: /خرید [شناسه]"
            bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=economy_menu(user_id), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("eco_job_"):
        uid = int(data.split("_")[2])
        eco = udb.get_economy(uid)
        user = udb.get_user(uid)
        jobs = udb.get_job_list()
        text = f"💼 **شغل‌های موجود**\n━━━━━━━━━━━━━━━━━━━━━━\nشغل فعلی: {eco['job']}\n\n"
        for job in jobs:
            status = "✅" if job["name"] == eco["job"] else " "
            req = f"(سطح {job['level_req']})" if job["level_req"] > 1 else ""
            text += f"{status} {job['name']}: {job['base']} سکه پایه {req}\n"
        text += f"\nسطح شما: {user['level']}"
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=economy_menu(uid), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("eco_gift_"):
        bot.answer_callback_query(call.id, "🎁 از دستور /هدیه [کاربر] [مقدار] استفاده کنید.")
        return
    
    # ===== کال‌بک‌های ازدواج =====
    if data.startswith("marry_"):
        uid = int(data.split("_")[2])
        bot.answer_callback_query(call.id, "💍 از دستور /ازدواج [کاربر] استفاده کنید.")
        return
    
    if data.startswith("divorce_"):
        uid = int(data.split("_")[2])
        result = udb.divorce(uid)
        if result == "success":
            bot.answer_callback_query(call.id, "💔 طلاق با موفقیت انجام شد.")
        elif result == "not_married":
            bot.answer_callback_query(call.id, "❌ شما ازدواج نکرده‌اید.")
        elif result == "insufficient":
            bot.answer_callback_query(call.id, f"❌ به {udb.default_settings.get('divorce_cost', 100)} سکه نیاز دارید.")
        else:
            bot.answer_callback_query(call.id, "❌ خطا در طلاق.")
        return
    
    if data.startswith("marriage_status_"):
        uid = int(data.split("_")[2])
        marriage = udb.get_marriage(uid)
        if marriage:
            other_id = marriage[1] if marriage[1] != uid else marriage[2]
            try:
                user = bot.get_chat_member(group_id, other_id).user
                name = user.first_name
            except:
                name = f"ID: {other_id}"
            date = datetime.fromtimestamp(marriage[3]).strftime('%Y-%m-%d')
            text = f"""
💕 **وضعیت ازدواج**
━━━━━━━━━━━━━━━━━━━━━━
💑 **همسر:** {name}
📅 **تاریخ ازدواج:** {date}
💖 **امتیاز عشق:** {marriage[5]}
━━━━━━━━━━━━━━━━━━━━━━
"""
            bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=marriage_menu(uid), parse_mode='HTML')
        else:
            bot.answer_callback_query(call.id, "❌ شما ازدواج نکرده‌اید.")
        return
    
    # ===== کال‌بک‌های خانواده =====
    if data.startswith("family_add_"):
        uid = int(data.split("_")[2])
        bot.answer_callback_query(call.id, "👨‍👦 از دستور /افزودن فرزند [کاربر] استفاده کنید.")
        return
    
    if data.startswith("family_list_"):
        uid = int(data.split("_")[2])
        members = udb.get_family_members(uid)
        if not members:
            bot.answer_callback_query(call.id, "❌ شما عضو هیچ خانواده‌ای نیستید.")
            return
        text = "👨‍👩‍👧‍👦 **خانواده شما**\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for member in members:
            if member[1] == uid:
                child_id = member[2]
                relation = member[3]
                try:
                    user = bot.get_chat_member(group_id, child_id).user
                    name = user.first_name
                except:
                    name = f"ID: {child_id}"
                text += f"👶 فرزند {relation}: {name}\n"
            elif member[2] == uid:
                parent_id = member[1]
                relation = member[3]
                try:
                    user = bot.get_chat_member(group_id, parent_id).user
                    name = user.first_name
                except:
                    name = f"ID: {parent_id}"
                text += f"👨‍👦 والد {relation}: {name}\n"
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=family_menu(uid), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    # ===== کال‌بک‌های رویدادها =====
    if data.startswith("event_add_"):
        gid = int(data.split("_")[2])
        bot.answer_callback_query(call.id, "📅 از دستور /رویداد [نام] | [توضیحات] | [زمان] استفاده کنید.")
        return
    
    if data.startswith("event_list_"):
        gid = int(data.split("_")[2])
        events = udb.get_events(gid)
        if not events:
            bot.edit_message_text("📭 هیچ رویدادی وجود ندارد.", chat_id, call.message.message_id, reply_markup=events_menu(gid))
        else:
            text = "📅 **رویدادهای گروه**\n━━━━━━━━━━━━━━━━━━━━━━\n"
            for event in events:
                date = datetime.fromtimestamp(event[3]).strftime('%Y-%m-%d %H:%M')
                text += f"#{event[0]} - {event[1]}\n📝 {event[2]}\n📅 {date}\n\n"
            bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=events_menu(gid), parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return

# ========== پاسخ به پیام‌های معمولی ==========
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.chat.type in ['group', 'supergroup']:
        if message.text and message.text.lower() in ["سلام", "درود", "hi", "hello"]:
            bot.reply_to(message, f"✨ سلام {message.from_user.first_name} جان! به گروه خوش آمدی! 🛡️")
    else:
        if message.text:
            bot.reply_to(message, "👋 سلام! لطفاً من رو به گروه اضافه کنید تا بتونم محافظت کنم.")

# ========== اجرا ==========
if __name__ == "__main__":
    print("=" * 70)
    print("✨ ربات محافظ فوق‌پیشرفته Luffy Ultra Pro V4 ✨")
    print("=" * 70)
    print(f"👥 ادمین‌ها: {ADMIN_IDS}")
    print("=" * 70)
    print("🆕 قابلیت‌های جدید فوق‌پیشرفته:")
    print("✅ 🤖 هوش مصنوعی مکالمه")
    print("✅ 💰 اقتصاد کامل (کار، خرید، بانک)")
    print("✅ 💑 سیستم ازدواج و عشق")
    print("✅ 👨‍👩‍👧‍👦 سیستم خانواده")
    print("✅ 📅 رویدادهای گروه")
    print("✅ 🎖️ سیستم نشان‌ها و دستاوردها")
    print("✅ 🔰 سیستم نقش‌ها")
    print("✅ 😴 سیستم AFK")
    print("✅ 🎤 امتیاز مکالمات صوتی")
    print("✅ 🤝 سیستم اعتماد و امتیاز")
    print("✅ 🚨 تشخیص ناهنجاری رفتاری")
    print("✅ 🛡️ امنیت پیش‌گیرانه")
    print("✅ 🔄 خودترمیمی")
    print("✅ 🧠 تحلیل محتوای هوشمند")
    print("✅ 🔍 تشخیص کلاهبرداری Web3")
    print("✅ 🚫 ضد Ghost Ping")
    print("✅ 📝 فیلتر کلمات پیشرفته")
    print("✅ 📅 پیام‌های زمان‌بندی شده")
    print("=" * 70)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"❌ خطا: {e}")
            print("🔄 راه‌اندازی مجدد در 5 ثانیه...")
            time.sleep(5)
            continue
[file content end]