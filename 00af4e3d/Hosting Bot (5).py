#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================================================
🚀 PRO TELEGRAM BOT HOSTING & CLOUD MANAGER (ULTRA-LIGHT RAM EDITION) — hosting_bot.py
=========================================================================================
نسخة فائقة الخفة والسرعة (Low-Memory / Zero-Crash Edition) مصممة خصيصاً لتعمل على أي
استضافة مجانية أو مدفوعة أو بوتات الاستضافة والهواتف دون استهلاك الذاكرة (RAM < 12MB).

المطورون الأساسيون (Admins): 8923631338 , 6486550968
التوكن المدمج: 9000019302:AAGo0CQf6goHyXERkirL-VY8ijDZ5BDDYDs
=========================================================================================
"""

import os
import gc
import sys
import json
import time
import uuid
import shutil
import zipfile
import sqlite3
import logging
import subprocess
import threading
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta

# تقليص حجم مكدس الخيوط (Thread Stack Size) لتوفير 90% من استهلاك الـ RAM في الاستضافات المحدودة
try:
    threading.stack_size(65536)
except Exception:
    pass

# ==============================================================================
# 1. الإعدادات الأساسية والبيانات الافتراضية (CONFIGURATION)
# ==============================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "9000019302:AAGo0CQf6goHyXERkirL-VY8ijDZ5BDDYDs")
PRIMARY_ADMINS = [8923631338, 6486550968]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "hosting_data")
WORKSPACES_DIR = os.path.join(DATA_DIR, "workspaces")
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")
DB_PATH = os.path.join(DATA_DIR, "hosting_bot.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(WORKSPACES_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("HostingBot")

DEFAULT_PLANS = [
    {"id": "free_starter", "name": "🌱 الخطة المبتدئة (Starter)", "price_usd": 0.0, "price_stars": 0, "max_bots": 2, "ram_mb": 256, "duration_days": 30},
    {"id": "pro_plan", "name": "⚡ الخطة الاحترافية (Pro)", "price_usd": 5.0, "price_stars": 250, "max_bots": 10, "ram_mb": 1024, "duration_days": 30},
    {"id": "ultra_plan", "name": "🔥 الخطة الخارقة (Ultra VIP)", "price_usd": 15.0, "price_stars": 750, "max_bots": 35, "ram_mb": 4096, "duration_days": 30},
    {"id": "enterprise_plan", "name": "👑 خطة الشركات (Enterprise)", "price_usd": 35.0, "price_stars": 1750, "max_bots": 100, "ram_mb": 16384, "duration_days": 30}
]

DEFAULT_PAYMENT_GATEWAYS = {
    "telegram_stars": {
        "name": "⭐ نجوم تيليجرام (Telegram Stars - تلقائي)",
        "enabled": True, "type": "auto_stars", "api_key": "", "secret": "",
        "instructions": "الدفع الفوري التلقائي عبر نجوم تيليجرام الرسمية بضغطة زر."
    },
    "cryptobot": {
        "name": "💎 CryptoBot (@send - USDT/TON/BTC تلقائي)",
        "enabled": True, "type": "auto_api", "api_key": "YOUR_CRYPTO_PAY_API_TOKEN", "secret": "https://pay.crypt.bot/api",
        "instructions": "يتم توليد فاتورة دفع تلقائية عبر CryptoBot وفحصها بالـ API فوراً."
    },
    "binance_pay": {
        "name": "🟡 Binance Pay (بينانس باي - API/ID)",
        "enabled": True, "type": "hybrid", "api_key": "YOUR_BINANCE_API_KEY", "wallet_id": "892363133",
        "instructions": "حول المبلغ إلى Binance ID الموضح ثم أرسل رقم العملية (Order ID)."
    },
    "nowpayments": {
        "name": "🌐 NOWPayments (أكثر من 200 عملة رقمية - API)",
        "enabled": True, "type": "auto_api", "api_key": "YOUR_NOWPAYMENTS_API_KEY", "secret": "https://api.nowpayments.io/v1",
        "instructions": "دفع تلقائي يدعم USDT TRC20/BEP20, TRX, TON, ETH, LTC وغيرها."
    },
    "stripe": {
        "name": "💳 البطاقات البنكية العالمية (Visa / MasterCard / Apple Pay)",
        "enabled": True, "type": "auto_api", "api_key": "sk_live_YOUR_STRIPE_KEY", "wallet_id": "https://buy.stripe.com/your_link",
        "instructions": "الدفع المباشر بالبطاقة البنكية عبر بوابة Stripe الآمنة."
    },
    "paypal": {
        "name": "🅿️ PayPal (باي بال العالمي)",
        "enabled": True, "type": "hybrid", "api_key": "YOUR_PAYPAL_CLIENT_ID", "wallet_id": "payments@yourdomain.com",
        "instructions": "ادفع عبر PayPal وأرسل رقم العملية للتأكيد الفوري."
    },
    "payeer": {
        "name": "🅿️ Payeer (بايير)",
        "enabled": True, "type": "hybrid", "api_key": "YOUR_PAYEER_MERCHANT_ID", "wallet_id": "P100000000",
        "instructions": "حول إلى محفظة Payeer الموضحة وأرسل رقم العملية (Transaction ID)."
    },
    "local_wallets": {
        "name": "🏦 المحافظ المحلية والعربية (BaridiMob / CCP / Vodafone / ZainCash)",
        "enabled": True, "type": "manual_receipt", "api_key": "",
        "wallet_id": "CCP/BaridiMob: 007999990000000000 | Vodafone Cash: 01000000000 | ZainCash: 9647800000000",
        "instructions": "قم بالتحويل لأحد الحسابات الموضحة أعلاه ثم أرسل رقم العملية ليتم شحن حسابك."
    }
}


# ==============================================================================
# 2. قاعدة البيانات الخفيفة (LOW-RAM SQLITE MANAGER)
# ==============================================================================
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=15, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # تقليل استهلاك الذاكرة لـ SQLite لأقصى درجة
        conn.execute("PRAGMA cache_size = -1000")
        conn.execute("PRAGMA temp_store = FILE")
        return conn

    def _init_db(self):
        with self.lock, self._connect() as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT,
                    balance_usd REAL DEFAULT 0.0, balance_stars INTEGER DEFAULT 0,
                    plan_id TEXT DEFAULT 'free_starter', plan_expiry TEXT,
                    custom_max_bots INTEGER DEFAULT NULL, is_banned INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0, joined_at TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS hosted_bots (
                    bot_id TEXT PRIMARY KEY, owner_id INTEGER, name TEXT, runtime TEXT,
                    main_file TEXT, folder_path TEXT, env_vars TEXT DEFAULT '{}',
                    auto_restart INTEGER DEFAULT 1, status TEXT DEFAULT 'stopped',
                    pid INTEGER DEFAULT NULL, created_at TEXT, last_started TEXT,
                    restart_count INTEGER DEFAULT 0
                )
            """)
            c.execute("CREATE TABLE IF NOT EXISTS force_channels (channel_id TEXT PRIMARY KEY, title TEXT, invite_link TEXT)")
            c.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    invoice_id TEXT PRIMARY KEY, user_id INTEGER, gateway TEXT,
                    amount_usd REAL, amount_stars INTEGER, status TEXT DEFAULT 'pending',
                    external_ref TEXT, proof_text TEXT, created_at TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS coupons (
                    code TEXT PRIMARY KEY, amount_usd REAL, amount_stars INTEGER,
                    max_uses INTEGER DEFAULT 1, used_count INTEGER DEFAULT 0, used_by TEXT DEFAULT '[]'
                )
            """)
            defaults = {
                "paid_mode": "0",
                "stars_per_usd": "50",
                "free_mode_max_bots": "3",
                "free_mode_ram_mb": "512",
                "maintenance_mode": "0",
                "welcome_message": "🔥 أهلاً بك في أقوى وأسرع بوت استضافة سحابية لبوتات تيليجرام 24/7!\n\n🚀 ارفع ملفات Python أو Node.js أو مشاريع ZIP كاملة وشغّلها فوراً مع مراقبة حية ودعم كامل.",
                "allow_pip_install": "1",
                "auto_boot_bots": "1",
                "plans_json": json.dumps(DEFAULT_PLANS, ensure_ascii=False),
                "gateways_json": json.dumps(DEFAULT_PAYMENT_GATEWAYS, ensure_ascii=False)
            }
            for k, v in defaults.items():
                c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            for admin_id in PRIMARY_ADMINS:
                c.execute("""
                    INSERT INTO users (user_id, username, full_name, balance_usd, balance_stars, plan_id, is_admin, joined_at)
                    VALUES (?, 'Developer', 'Super Admin', 999999.0, 999999, 'enterprise_plan', 1, ?)
                    ON CONFLICT(user_id) DO UPDATE SET is_admin = 1
                """, (admin_id, now_str))
            conn.commit()

    def get_setting(self, key, default=None):
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def set_setting(self, key, value):
        with self.lock, self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    def get_plans(self):
        try:
            return json.loads(self.get_setting("plans_json", "[]"))
        except Exception:
            return DEFAULT_PLANS

    def save_plans(self, plans):
        self.set_setting("plans_json", json.dumps(plans, ensure_ascii=False))

    def get_gateways(self):
        try:
            return json.loads(self.get_setting("gateways_json", "{}"))
        except Exception:
            return DEFAULT_PAYMENT_GATEWAYS

    def save_gateways(self, gateways):
        self.set_setting("gateways_json", json.dumps(gateways, ensure_ascii=False))

    def ensure_user(self, user_id, username="", full_name=""):
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            is_adm = 1 if user_id in PRIMARY_ADMINS else 0
            if not row:
                conn.execute("""
                    INSERT INTO users (user_id, username, full_name, is_admin, joined_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username or "", full_name or "", is_adm, now_str))
            else:
                if is_adm and not row["is_admin"]:
                    conn.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
                conn.execute("UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                             (username or row["username"], full_name or row["full_name"], user_id))
            conn.commit()
            return dict(conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone())

    def get_user(self, user_id):
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return dict(row) if row else None

    def update_balance(self, user_id, delta_usd=0.0, delta_stars=0):
        with self.lock, self._connect() as conn:
            conn.execute("""
                UPDATE users
                SET balance_usd = MAX(0.0, ROUND(balance_usd + ?, 4)),
                    balance_stars = MAX(0, balance_stars + ?)
                WHERE user_id = ?
            """, (float(delta_usd), int(delta_stars), user_id))
            conn.commit()

    def set_balance(self, user_id, new_usd=None, new_stars=None):
        with self.lock, self._connect() as conn:
            if new_usd is not None:
                conn.execute("UPDATE users SET balance_usd = ? WHERE user_id = ?", (round(float(new_usd), 4), user_id))
            if new_stars is not None:
                conn.execute("UPDATE users SET balance_stars = ? WHERE user_id = ?", (int(new_stars), user_id))
            conn.commit()

    def is_admin(self, user_id):
        if user_id in PRIMARY_ADMINS:
            return True
        u = self.get_user(user_id)
        return bool(u and u.get("is_admin") == 1)


db = Database(DB_PATH)


# ==============================================================================
# 3. محرك تشغيل البوتات المستضافة مع حماية الذاكرة (MEMORY-SAFE PROCESS ENGINE)
# ==============================================================================
class ProcessManager:
    def __init__(self, database: Database):
        self.db = database
        self.processes = {}
        self.log_handles = {}
        self.lock = threading.RLock()

    def start_bot(self, bot_id):
        with self.lock:
            bot_info = self.get_bot(bot_id)
            if not bot_info:
                return False, "❌ البوت غير موجود."

            if bot_id in self.processes and self.processes[bot_id].poll() is None:
                return True, "✅ البوت يعمل بالفعل."

            folder = bot_info["folder_path"]
            main_file = bot_info["main_file"]
            runtime = bot_info["runtime"]
            full_main_path = os.path.join(folder, main_file)

            if not os.path.exists(full_main_path):
                return False, f"❌ الملف `{main_file}` غير موجود."

            log_file_path = os.path.join(folder, "runtime.log")
            # تقليص حجم ملف السجل إذا تجاوز 512KB لحماية الذاكرة والقرص
            if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 524288:
                try:
                    with open(log_file_path, "rb") as f:
                        f.seek(-102400, os.SEEK_END)
                        tail_bytes = f.read()
                    with open(log_file_path, "wb") as f:
                        f.write(tail_bytes)
                except Exception:
                    pass

            if bot_id in self.log_handles:
                try:
                    self.log_handles[bot_id].close()
                except Exception:
                    pass

            log_file = open(log_file_path, "a", encoding="utf-8")
            self.log_handles[bot_id] = log_file
            log_file.write(f"\n--- [START {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] ---\n")
            log_file.flush()

            env = os.environ.copy()
            try:
                for k, v in json.loads(bot_info.get("env_vars") or "{}").items():
                    env[str(k)] = str(v)
            except Exception:
                pass
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONOPTIMIZE"] = "1"

            if runtime == "nodejs":
                cmd = ["node", "--max-old-space-size=128", full_main_path]
            elif runtime == "bash":
                cmd = ["bash", full_main_path]
            else:
                cmd = [sys.executable, "-u", "-O", full_main_path]

            try:
                proc = subprocess.Popen(
                    cmd, cwd=folder, stdout=log_file, stderr=subprocess.STDOUT,
                    env=env, close_fds=True
                )
                self.processes[bot_id] = proc
                now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                with self.db.lock, self.db._connect() as conn:
                    conn.execute("UPDATE hosted_bots SET status = 'running', pid = ?, last_started = ? WHERE bot_id = ?",
                                 (proc.pid, now_str, bot_id))
                    conn.commit()
                return True, f"🚀 تم تشغيل البوت بنجاح! (PID: `{proc.pid}`)"
            except Exception as e:
                return False, f"❌ فشل التشغيل: `{e}`"

    def stop_bot(self, bot_id):
        with self.lock:
            proc = self.processes.get(bot_id)
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                except Exception:
                    pass
            self.processes.pop(bot_id, None)
            if bot_id in self.log_handles:
                try:
                    self.log_handles.pop(bot_id).close()
                except Exception:
                    pass
            with self.db.lock, self.db._connect() as conn:
                conn.execute("UPDATE hosted_bots SET status = 'stopped', pid = NULL WHERE bot_id = ?", (bot_id,))
                conn.commit()
            return True, "🛑 تم إيقاف البوت بنجاح."

    def restart_bot(self, bot_id):
        self.stop_bot(bot_id)
        time.sleep(0.3)
        return self.start_bot(bot_id)

    def install_requirements(self, bot_id, custom_packages=None):
        bot_info = self.get_bot(bot_id)
        if not bot_info:
            return False, "❌ البوت غير موجود."
        if self.db.get_setting("allow_pip_install", "1") != "1":
            return False, "⚠️ تثبيت المكاتب معطل من الإدارة."

        folder = bot_info["folder_path"]
        req_path = os.path.join(folder, "requirements.txt")
        # استخدام --no-cache-dir لمنع pip من استهلاك الرام أثناء التثبيت!
        base_pip = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--disable-pip-version-check"]
        if custom_packages:
            cmd = base_pip + custom_packages.split()
        elif os.path.exists(req_path):
            cmd = base_pip + ["-r", req_path]
        else:
            return False, "❌ لا يوجد ملف `requirements.txt` ولم يتم تحديد مكتبة."

        try:
            res = subprocess.run(cmd, cwd=folder, capture_output=True, text=True, timeout=150)
            output = (res.stdout + "\n" + res.stderr).strip()[-1500:]
            if res.returncode == 0:
                return True, f"✅ تم التثبيت بنجاح (بدون استهلاك الكاش):\n```\n{output}\n```"
            return False, f"⚠️ خطأ أثناء التثبيت:\n```\n{output}\n```"
        except Exception as e:
            return False, f"❌ خطأ: `{e}`"

    def get_logs(self, bot_id):
        bot_info = self.get_bot(bot_id)
        if not bot_info:
            return "لا يوجد سجل."
        log_path = os.path.join(bot_info["folder_path"], "runtime.log")
        if not os.path.exists(log_path):
            return "📭 السجل فارغ حالياً."
        try:
            # قراءة آخر 3000 بايت فقط بدلاً من تحميل الملف كاملاً في الذاكرة
            with open(log_path, "rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                f.seek(max(0, size - 3000), os.SEEK_SET)
                data = f.read().decode("utf-8", errors="replace")
                return data.strip() or "📭 السجل فارغ."
        except Exception as e:
            return f"خطأ في قراءة السجل: {e}"

    def clear_logs(self, bot_id):
        bot_info = self.get_bot(bot_id)
        if not bot_info:
            return False
        log_path = os.path.join(bot_info["folder_path"], "runtime.log")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"--- [CLEARED {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] ---\n")
            return True
        except Exception:
            return False

    def get_bot(self, bot_id):
        with self.db.lock, self.db._connect() as conn:
            row = conn.execute("SELECT * FROM hosted_bots WHERE bot_id = ?", (bot_id,)).fetchone()
            return dict(row) if row else None

    def get_user_bots(self, owner_id):
        with self.db.lock, self.db._connect() as conn:
            rows = conn.execute("SELECT * FROM hosted_bots WHERE owner_id = ? ORDER BY created_at DESC", (owner_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_all_bots(self):
        with self.db.lock, self.db._connect() as conn:
            rows = conn.execute("SELECT * FROM hosted_bots ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def delete_bot(self, bot_id):
        self.stop_bot(bot_id)
        bot_info = self.get_bot(bot_id)
        if bot_info and os.path.exists(bot_info["folder_path"]):
            shutil.rmtree(bot_info["folder_path"], ignore_errors=True)
        with self.db.lock, self.db._connect() as conn:
            conn.execute("DELETE FROM hosted_bots WHERE bot_id = ?", (bot_id,))
            conn.commit()
        return True

    def check_watchdog_once(self):
        """فحص دوري خفيف يستدعى داخل الحلقة الرئيسية بدلاً من فتح خيط إضافي يستهلك الرام"""
        with self.lock:
            for b in self.get_all_bots():
                bid = b["bot_id"]
                if b["status"] == "running":
                    proc = self.processes.get(bid)
                    if proc is None or proc.poll() is not None:
                        if b.get("auto_restart", 1) == 1:
                            with self.db.lock, self.db._connect() as conn:
                                conn.execute("UPDATE hosted_bots SET restart_count = restart_count + 1 WHERE bot_id = ?", (bid,))
                                conn.commit()
                            self.start_bot(bid)
                        else:
                            with self.db.lock, self.db._connect() as conn:
                                conn.execute("UPDATE hosted_bots SET status = 'crashed', pid = NULL WHERE bot_id = ?", (bid,))
                                conn.commit()


pm = ProcessManager(db)


# ==============================================================================
# 4. محرك بوابات الدفع العالمية والـ API (GLOBAL PAYMENT GATEWAYS ENGINE)
# ==============================================================================
class PaymentEngine:
    @staticmethod
    def create_cryptobot_invoice(api_token, base_url, amount_usd, description, payload):
        url = f"{base_url.rstrip('/')}/createInvoice"
        data = json.dumps({
            "currency_type": "fiat", "fiat": "USD", "amount": str(round(amount_usd, 2)),
            "description": description, "payload": payload
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Crypto-Pay-API-Token": api_token, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("ok"):
                    inv = res["result"]
                    return True, inv["bot_invoice_url"], str(inv["invoice_id"])
                return False, str(res), None
        except Exception as e:
            return False, str(e), None

    @staticmethod
    def check_cryptobot_invoice(api_token, base_url, ext_invoice_id):
        url = f"{base_url.rstrip('/')}/getInvoices?invoice_ids={ext_invoice_id}"
        req = urllib.request.Request(url, headers={"Crypto-Pay-API-Token": api_token})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("ok") and res["result"].get("items"):
                    return res["result"]["items"][0].get("status") == "paid"
        except Exception:
            pass
        return False

    @staticmethod
    def create_nowpayments_invoice(api_key, base_url, amount_usd, order_id, description):
        url = f"{base_url.rstrip('/')}/invoice"
        data = json.dumps({
            "price_amount": round(amount_usd, 2), "price_currency": "usd",
            "order_id": order_id, "order_description": description
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"x-api-key": api_key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if "invoice_url" in res:
                    return True, res["invoice_url"], str(res.get("id"))
                return False, str(res), None
        except Exception as e:
            return False, str(e), None


# ==============================================================================
# 5. عميل تيليجرام المباشر (FAST STREAMING TELEGRAM CLIENT)
# ==============================================================================
class TelegramBotClient:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.file_url = f"https://api.telegram.org/file/bot{token}"

    def call(self, method, params=None, timeout=25):
        url = f"{self.api_url}/{method}"
        data = json.dumps(params).encode("utf-8") if params is not None else None
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode("utf-8"))
            except Exception:
                return {"ok": False, "description": str(e)}
        except Exception as e:
            return {"ok": False, "description": str(e)}

    def send_message(self, chat_id, text, reply_markup=None, parse_mode="Markdown"):
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = self.call("sendMessage", payload)
        if not res.get("ok") and parse_mode:
            payload.pop("parse_mode", None)
            res = self.call("sendMessage", payload)
        return res

    def edit_message(self, chat_id, message_id, text, reply_markup=None, parse_mode="Markdown"):
        payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "disable_web_page_preview": True}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = self.call("editMessageText", payload)
        if not res.get("ok") and parse_mode:
            payload.pop("parse_mode", None)
            res = self.call("editMessageText", payload)
        return res

    def answer_callback(self, callback_query_id, text="", show_alert=False):
        return self.call("answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text, "show_alert": show_alert})

    def send_stars_invoice(self, chat_id, title, description, payload_str, amount_stars):
        return self.call("sendInvoice", {
            "chat_id": chat_id, "title": title, "description": description,
            "payload": payload_str, "provider_token": "", "currency": "XTR",
            "prices": [{"label": title, "amount": int(amount_stars)}]
        })

    def answer_pre_checkout_query(self, pre_checkout_query_id, ok=True):
        return self.call("answerPreCheckoutQuery", {"pre_checkout_query_id": pre_checkout_query_id, "ok": ok})

    def download_file_stream(self, file_id, dest_path):
        """تنزيل الملفات عبر التدفق المباشر (64KB Chunks) لعدم استهلاك الذاكرة (RAM)"""
        info = self.call("getFile", {"file_id": file_id})
        if not info.get("ok"):
            return False, info.get("description", "Failed to getFile")
        dl_url = f"{self.file_url}/{info['result']['file_path']}"
        try:
            with urllib.request.urlopen(dl_url, timeout=60) as r, open(dest_path, "wb") as out_f:
                shutil.copyfileobj(r, out_f, length=65536)
            return True, dest_path
        except Exception as e:
            return False, str(e)

    def check_channel_membership(self, channel_id, user_id):
        res = self.call("getChatMember", {"chat_id": channel_id, "user_id": user_id})
        if not res.get("ok"):
            return True
        return res["result"].get("status", "") in ("creator", "administrator", "member", "restricted")


bot = TelegramBotClient(BOT_TOKEN)
USER_STATES = {}


# ==============================================================================
# 6. دوال المساعدة والواجهات (HELPERS & UI BUILDERS)
# ==============================================================================
def get_user_effective_limits(user_id):
    user = db.get_user(user_id)
    paid_mode = db.get_setting("paid_mode", "0") == "1"

    if db.is_admin(user_id):
        return {
            "plan_name": "👑 مطور النظام (غير محدود)", "max_bots": 9999, "ram_mb": 65536,
            "mode_label": "الوضع المدفوع مفعل 💰" if paid_mode else "الوضع المجاني مفعل 🎁"
        }

    if not paid_mode:
        free_max = int(db.get_setting("free_mode_max_bots", "3"))
        free_ram = int(db.get_setting("free_mode_ram_mb", "512"))
        if user and user.get("custom_max_bots"):
            free_max = max(free_max, int(user["custom_max_bots"]))
        return {"plan_name": "🎁 الاستضافة المجانية الشاملة", "max_bots": free_max, "ram_mb": free_ram, "mode_label": "الوضع المجاني العام 🎁"}

    plans = {p["id"]: p for p in db.get_plans()}
    user_plan_id = user.get("plan_id", "free_starter") if user else "free_starter"
    expiry = user.get("plan_expiry") if user else None
    if expiry:
        try:
            if datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S") < datetime.utcnow():
                user_plan_id = "free_starter"
        except Exception:
            pass

    plan = plans.get(user_plan_id, DEFAULT_PLANS[0])
    max_bots = int(user["custom_max_bots"]) if (user and user.get("custom_max_bots") is not None) else int(plan.get("max_bots", 1))
    return {"plan_name": plan.get("name", "Starter"), "max_bots": max_bots, "ram_mb": plan.get("ram_mb", 256), "mode_label": "الوضع المدفوع (VIP) 💰"}


def check_force_sub(user_id):
    if db.is_admin(user_id):
        return True, []
    with db.lock, db._connect() as conn:
        channels = [dict(r) for r in conn.execute("SELECT * FROM force_channels").fetchall()]
    missing = [ch for ch in channels if not bot.check_channel_membership(ch["channel_id"], user_id)]
    return len(missing) == 0, missing


def get_system_metrics():
    cpu_load, ram_info, disk_info = "غير معروف", "غير معروف", "غير معروف"
    try:
        if hasattr(os, "getloadavg"):
            l1, l5, _ = os.getloadavg()
            cpu_load = f"{l1:.2f} / {l5:.2f} ({os.cpu_count() or 1} أنوية)"
        if os.path.exists("/proc/meminfo"):
            mem = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    p = line.split(":")
                    if len(p) == 2:
                        mem[p[0].strip()] = int(p[1].strip().split()[0]) // 1024
            tot = mem.get("MemTotal", 0)
            avail = mem.get("MemAvailable", mem.get("MemFree", 0))
            ram_info = f"{tot - avail} MB / {tot} MB"
        total_d, used_d, _ = shutil.disk_usage(BASE_DIR)
        disk_info = f"{used_d // (1024**3)} GB / {total_d // (1024**3)} GB"
    except Exception:
        pass
    return cpu_load, ram_info, disk_info


def main_menu_keyboard(user_id):
    paid_mode = db.get_setting("paid_mode", "0") == "1"
    kb = [
        [{"text": "➕ استضافة بوت / مشروع جديد", "callback_data": "new_bot"}, {"text": "🤖 بوتاتي المستضافة", "callback_data": "my_bots"}],
        [{"text": "💰 محفظتي وشحن الرصيد", "callback_data": "wallet"}, {"text": "💎 خطط وعروض الاستضافة" if paid_mode else "🎁 ميزات الاستضافة المجانية", "callback_data": "plans_menu"}],
        [{"text": "🎟️ استرداد كود هدية", "callback_data": "redeem_coupon"}, {"text": "📊 حالة السيرفر والسرعة", "callback_data": "server_status"}],
        [{"text": "📚 دليل الاستخدام السريع", "callback_data": "help_guide"}]
    ]
    if db.is_admin(user_id):
        kb.append([{"text": "👑 لوحة تحكم المطور الشاملة (Full Control) 👑", "callback_data": "admin_panel"}])
    return {"inline_keyboard": kb}


def admin_panel_keyboard():
    paid_mode = db.get_setting("paid_mode", "0") == "1"
    maint_mode = db.get_setting("maintenance_mode", "0") == "1"
    pip_mode = db.get_setting("allow_pip_install", "1") == "1"
    return {
        "inline_keyboard": [
            [{"text": "🟢 الوضع المدفوع: مفعل (اضغط للتحويل لمجاني 🎁)" if paid_mode else "⚪ الوضع المدفوع: مجاني (اضغط لتفعيل المدفوع 💰)", "callback_data": "adm_toggle_paid"}],
            [{"text": "➕ إضافة رصيد لمستخدم", "callback_data": "adm_add_balance"}, {"text": "➖ نزع/خصم رصيد مستخدم", "callback_data": "adm_sub_balance"}],
            [{"text": "🎯 تحديد رصيد مباشر", "callback_data": "adm_set_balance"}, {"text": "🎟️ إنشاء كود شحن/هدية", "callback_data": "adm_create_coupon"}],
            [{"text": "💲 تخصيص خطط وأسعار الاستضافة ($ و ⭐)", "callback_data": "adm_manage_plans"}, {"text": "💳 إدارة بوابات الدفع والـ API", "callback_data": "adm_manage_gateways"}],
            [{"text": "📢 قسم الإذاعة الشامل (Broadcast)", "callback_data": "adm_broadcast"}, {"text": "🔒 قنوات الاشتراك الإجباري", "callback_data": "adm_force_sub"}],
            [{"text": "🤖 مراقبة وإدارة كل البوتات", "callback_data": "adm_all_bots"}, {"text": "👤 فحص/حظر/ترقية مستخدم", "callback_data": "adm_user_manage"}],
            [{"text": "🛠️ وضع الصيانة: مفعل" if maint_mode else "✅ وضع الصيانة: معطل", "callback_data": "adm_toggle_maint"}, {"text": "📦 تثبيت المكاتب: مفعل" if pip_mode else "🚫 تثبيت المكاتب: معطل", "callback_data": "adm_toggle_pip"}],
            [{"text": "⚙️ حدود الوضع المجاني وسعر النجوم", "callback_data": "adm_free_limits"}, {"text": "👑 إدارة المطورين (Admins)", "callback_data": "adm_admins_list"}],
            [{"text": "🗄️ سحب نسخة احتياطية كاملة (Backup)", "callback_data": "adm_backup"}],
            [{"text": "🔙 العودة للقائمة الرئيسية", "callback_data": "back_home"}]
        ]
    }


def build_home_text(user_id):
    user = db.get_user(user_id)
    limits = get_user_effective_limits(user_id)
    user_bots = pm.get_user_bots(user_id)
    running_cnt = sum(1 for b in user_bots if b["status"] == "running")
    return (
        f"{db.get_setting('welcome_message', '')}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 **معرف الحساب:** `{user_id}`\n"
        f"🏷️ **حالة النظام:** {limits['mode_label']}\n"
        f"💎 **خطتك الحالية:** {limits['plan_name']}\n"
        f"💵 **الرصيد بالدولار:** `${user['balance_usd']:.2f}`\n"
        f"⭐ **الرصيد بالنجوم:** `{user['balance_stars']} ⭐`\n"
        f"🤖 **البوتات المستضافة:** `{len(user_bots)} / {limits['max_bots']}` (يعمل منها: `{running_cnt}`)\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👇 اختر من القائمة أدناه للتحكم الكامل:"
    )


# ==============================================================================
# 7. معالج الرسائل والأوامر والملفات (MESSAGE & FILE HANDLERS)
# ==============================================================================
def handle_message(msg):
    chat_id = msg["chat"]["id"]
    from_user = msg.get("from", {})
    user_id = from_user.get("id", chat_id)
    username = from_user.get("username", "")
    full_name = (from_user.get("first_name", "") + " " + from_user.get("last_name", "")).strip()

    user = db.ensure_user(user_id, username, full_name)
    if user.get("is_banned") == 1 and not db.is_admin(user_id):
        bot.send_message(chat_id, "🚫 عذراً، تم حظر حسابك من استخدام البوت.")
        return

    if db.get_setting("maintenance_mode", "0") == "1" and not db.is_admin(user_id):
        bot.send_message(chat_id, "🛠️ البوت في وضع الصيانة والتحديث حالياً، يرجى المحاولة لاحقاً.")
        return

    if "successful_payment" in msg:
        sp = msg["successful_payment"]
        total_stars = int(sp.get("total_amount", 0))
        stars_per_usd = float(db.get_setting("stars_per_usd", "50"))
        usd_equiv = round(total_stars / max(1.0, stars_per_usd), 2)
        db.update_balance(user_id, delta_usd=usd_equiv, delta_stars=total_stars)
        bot.send_message(
            chat_id,
            f"🎉 **تمت عملية الدفع بنجوم تيليجرام بنجاح!**\n⭐ النجوم المضافة: `{total_stars} ⭐` (`${usd_equiv:.2f}`)",
            reply_markup=main_menu_keyboard(user_id)
        )
        for adm in PRIMARY_ADMINS:
            bot.send_message(adm, f"💰 **شحن تلقائي بنجوم تيليجرام!**\n👤 المستخدم: `{user_id}` (@{username})\n⭐ المبلغ: `{total_stars} ⭐` (`${usd_equiv}`)")
        return

    ok_sub, missing_channels = check_force_sub(user_id)
    if not ok_sub:
        kb = [[{"text": f"📢 اشترك في: {ch['title']}", "url": ch["invite_link"]}] for ch in missing_channels]
        kb.append([{"text": "✅ تحققت من الاشتراك (تحديث)", "callback_data": "verify_sub"}])
        bot.send_message(chat_id, "⚠️ **يجب عليك الاشتراك في قنوات البوت أولاً لتتمكن من استخدام الاستضافة:**", reply_markup={"inline_keyboard": kb})
        return

    text = msg.get("text", "").strip()
    if text.startswith("/start"):
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, build_home_text(user_id), reply_markup=main_menu_keyboard(user_id))
        return

    if text.startswith("/admin") and db.is_admin(user_id):
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, "👑 **لوحة تحكم المطور الشاملة (Full Control Panel):**", reply_markup=admin_panel_keyboard())
        return

    state = USER_STATES.get(user_id)
    if not state:
        bot.send_message(chat_id, build_home_text(user_id), reply_markup=main_menu_keyboard(user_id))
        return

    action = state.get("action")

    if action == "awaiting_bot_upload":
        limits = get_user_effective_limits(user_id)
        if len(pm.get_user_bots(user_id)) >= limits["max_bots"]:
            USER_STATES.pop(user_id, None)
            bot.send_message(chat_id, f"⚠️ وصلت للحد الأقصى المسموح (`{limits['max_bots']}` بوتات).", reply_markup=main_menu_keyboard(user_id))
            return

        doc = msg.get("document")
        if not doc:
            bot.send_message(chat_id, "📎 أرسل ملف البوت الآن بصيغة `.py` أو `.js` أو `.sh` أو `.zip` (أو /start للإلغاء).")
            return

        file_name = doc.get("file_name", "bot.py")
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in (".py", ".js", ".sh", ".zip"):
            bot.send_message(chat_id, "❌ صيغة غير مدعومة! أرسل `.py` أو `.js` أو `.sh` أو `.zip`.")
            return

        bot_id = f"bot_{user_id}_{uuid.uuid4().hex[:6]}"
        bot_folder = os.path.join(WORKSPACES_DIR, bot_id)
        os.makedirs(bot_folder, exist_ok=True)
        local_path = os.path.join(bot_folder, file_name)

        bot.send_message(chat_id, "⏳ جاري تنزيل الملف وتجهيز الاستضافة...")
        ok, info = bot.download_file_stream(doc["file_id"], local_path)
        if not ok:
            shutil.rmtree(bot_folder, ignore_errors=True)
            bot.send_message(chat_id, f"❌ فشل التحميل: `{info}`")
            return

        main_file, runtime = file_name, "python"
        if ext == ".js":
            runtime = "nodejs"
        elif ext == ".sh":
            runtime = "bash"
        elif ext == ".zip":
            try:
                with zipfile.ZipFile(local_path, "r") as zf:
                    zf.extractall(bot_folder)
                os.remove(local_path)
                candidates = ["main.py", "bot.py", "app.py", "run.py", "index.js", "bot.js"]
                found_main = None
                for root_d, _, files_list in os.walk(bot_folder):
                    for cand in candidates:
                        if cand in files_list:
                            found_main = os.path.relpath(os.path.join(root_d, cand), bot_folder)
                            break
                    if found_main:
                        break
                if not found_main:
                    for root_d, _, files_list in os.walk(bot_folder):
                        for f in files_list:
                            if f.endswith(".py") or f.endswith(".js"):
                                found_main = os.path.relpath(os.path.join(root_d, f), bot_folder)
                                break
                        if found_main:
                            break
                main_file = found_main or "main.py"
                runtime = "nodejs" if main_file.endswith(".js") else "python"
            except Exception as e:
                shutil.rmtree(bot_folder, ignore_errors=True)
                bot.send_message(chat_id, f"❌ فشل فك ضغط ZIP: `{e}`")
                return

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with db.lock, db._connect() as conn:
            conn.execute("""
                INSERT INTO hosted_bots (bot_id, owner_id, name, runtime, main_file, folder_path, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'stopped', ?)
            """, (bot_id, user_id, file_name, runtime, main_file, bot_folder, now_str))
            conn.commit()

        pip_note = ""
        if os.path.exists(os.path.join(bot_folder, "requirements.txt")):
            ok_pip, pip_out = pm.install_requirements(bot_id)
            pip_note = "\n📦 تم تثبيت `requirements.txt` تلقائياً!" if ok_pip else f"\n⚠️ ملاحظة التثبيت: {pip_out[:180]}"

        _, start_msg = pm.start_bot(bot_id)
        USER_STATES.pop(user_id, None)
        gc.collect()
        bot.send_message(
            chat_id,
            f"🎉 **تم رفع واستضافة مشروعك بنجاح!**\n"
            f"🆔 المعرف: `{bot_id}` | 📄 الملف: `{main_file}` ({runtime}){pip_note}\n{start_msg}",
            reply_markup={"inline_keyboard": [[{"text": "🎛️ التحكم بالبوت", "callback_data": f"manage_bot:{bot_id}"}], [{"text": "🔙 القائمة الرئيسية", "callback_data": "back_home"}]]}
        )
        return

    if action == "awaiting_pip_pkg":
        bot_id = state["bot_id"]
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, f"⏳ جاري تثبيت `{text}`...")
        _, out = pm.install_requirements(bot_id, custom_packages=text)
        bot.send_message(chat_id, out, reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع للبوت", "callback_data": f"manage_bot:{bot_id}"}]]})
        return

    if action == "awaiting_env_var":
        bot_id = state["bot_id"]
        if "=" not in text:
            bot.send_message(chat_id, "❌ أرسل بالصيغة: `KEY=VALUE`")
            return
        k, v = text.split("=", 1)
        b_info = pm.get_bot(bot_id)
        if b_info:
            envs = json.loads(b_info.get("env_vars") or "{}")
            envs[k.strip()] = v.strip()
            with db.lock, db._connect() as conn:
                conn.execute("UPDATE hosted_bots SET env_vars = ? WHERE bot_id = ?", (json.dumps(envs, ensure_ascii=False), bot_id))
                conn.commit()
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, f"✅ تم حفظ المتغير `{k.strip()}`!", reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع للبوت", "callback_data": f"manage_bot:{bot_id}"}]]})
        return

    if action == "awaiting_main_file":
        bot_id = state["bot_id"]
        with db.lock, db._connect() as conn:
            conn.execute("UPDATE hosted_bots SET main_file = ? WHERE bot_id = ?", (text.strip(), bot_id))
            conn.commit()
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, f"✅ تم تغيير الملف الرئيسي إلى `{text.strip()}`.", reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع للبوت", "callback_data": f"manage_bot:{bot_id}"}]]})
        return

    if action == "awaiting_coupon_code":
        code = text.strip()
        USER_STATES.pop(user_id, None)
        with db.lock, db._connect() as conn:
            row = conn.execute("SELECT * FROM coupons WHERE code = ?", (code,)).fetchone()
            if not row:
                bot.send_message(chat_id, "❌ الكود غير صحيح.", reply_markup=main_menu_keyboard(user_id))
                return
            used_by = json.loads(row["used_by"] or "[]")
            if user_id in used_by or row["used_count"] >= row["max_uses"]:
                bot.send_message(chat_id, "⚠️ الكود مستخدم مسبقاً أو منتهي.", reply_markup=main_menu_keyboard(user_id))
                return
            used_by.append(user_id)
            conn.execute("UPDATE coupons SET used_count = used_count + 1, used_by = ? WHERE code = ?", (json.dumps(used_by), code))
            conn.commit()
        db.update_balance(user_id, delta_usd=row["amount_usd"], delta_stars=row["amount_stars"])
        bot.send_message(chat_id, f"🎉 **تم تفعيل الكود!** (`+${row['amount_usd']:.2f}` / `+{row['amount_stars']} ⭐`)", reply_markup=main_menu_keyboard(user_id))
        return

    if action == "awaiting_deposit_amount":
        gw_key = state["gateway"]
        try:
            amount_usd = float(text.strip())
            if amount_usd <= 0:
                raise ValueError()
        except ValueError:
            bot.send_message(chat_id, "❌ أدخل رقماً صحيحاً للمبلغ بالدولار.")
            return

        stars_per_usd = float(db.get_setting("stars_per_usd", "50"))
        amount_stars = max(1, int(round(amount_usd * stars_per_usd)))
        gw = db.get_gateways().get(gw_key, {})
        inv_id = f"INV_{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        USER_STATES.pop(user_id, None)

        if gw_key == "telegram_stars":
            with db.lock, db._connect() as conn:
                conn.execute("INSERT INTO invoices (invoice_id, user_id, gateway, amount_usd, amount_stars, status, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                             (inv_id, user_id, gw_key, amount_usd, amount_stars, now_str))
                conn.commit()
            bot.send_stars_invoice(chat_id, f"شحن المحفظة (${amount_usd:.2f})", f"شحن رصيد بقيمة ${amount_usd:.2f} ({amount_stars} نجمة)", inv_id, amount_stars)
            return

        if gw_key == "cryptobot" and gw.get("api_key") and not gw["api_key"].startswith("YOUR_"):
            ok_cb, url_or_err, ext_id = PaymentEngine.create_cryptobot_invoice(gw["api_key"], gw.get("secret", "https://pay.crypt.bot/api"), amount_usd, f"شحن ${amount_usd}", inv_id)
            if ok_cb:
                with db.lock, db._connect() as conn:
                    conn.execute("INSERT INTO invoices (invoice_id, user_id, gateway, amount_usd, amount_stars, status, external_ref, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
                                 (inv_id, user_id, gw_key, amount_usd, amount_stars, ext_id, now_str))
                    conn.commit()
                bot.send_message(
                    chat_id, f"💎 **فاتورة CryptoBot جاهزة (`{inv_id}`):**\n💵 المبلغ: `${amount_usd:.2f}`",
                    reply_markup={"inline_keyboard": [[{"text": f"💳 ادفع الآن (${amount_usd:.2f})", "url": url_or_err}], [{"text": "🔄 تحقق تلقائياً (API)", "callback_data": f"check_api_inv:{inv_id}"}]]}
                )
                return

        if gw_key == "nowpayments" and gw.get("api_key") and not gw["api_key"].startswith("YOUR_"):
            ok_np, url_or_err, ext_id = PaymentEngine.create_nowpayments_invoice(gw["api_key"], gw.get("secret", "https://api.nowpayments.io/v1"), amount_usd, inv_id, f"Top-up ${amount_usd}")
            if ok_np:
                with db.lock, db._connect() as conn:
                    conn.execute("INSERT INTO invoices (invoice_id, user_id, gateway, amount_usd, amount_stars, status, external_ref, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
                                 (inv_id, user_id, gw_key, amount_usd, amount_stars, ext_id, now_str))
                    conn.commit()
                bot.send_message(
                    chat_id, f"🌐 **فاتورة NOWPayments جاهزة (`{inv_id}`):**\n💵 المبلغ: `${amount_usd:.2f}`",
                    reply_markup={"inline_keyboard": [[{"text": "🌐 صفحة الدفع", "url": url_or_err}], [{"text": "📩 تأكيد الدفع", "callback_data": f"submit_proof:{inv_id}"}]]}
                )
                return

        with db.lock, db._connect() as conn:
            conn.execute("INSERT INTO invoices (invoice_id, user_id, gateway, amount_usd, amount_stars, status, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                         (inv_id, user_id, gw_key, amount_usd, amount_stars, now_str))
            conn.commit()

        wallet_target = gw.get("wallet_id") or gw.get("api_key") or "تواصل مع المطور"
        bot.send_message(
            chat_id,
            f"🧾 **فاتورة الشحن `{inv_id}`**\n💳 البوابة: {gw.get('name', gw_key)}\n💵 المبلغ: `${amount_usd:.2f}` (`{amount_stars} ⭐`)\n🏦 الحساب/المحفظة:\n`{wallet_target}`\n📌 {gw.get('instructions', '')}",
            reply_markup={"inline_keyboard": [[{"text": "📤 إرسال رقم العملية / الإثبات", "callback_data": f"submit_proof:{inv_id}"}], [{"text": "🔙 للمحفظة", "callback_data": "wallet"}]]}
        )
        return

    if action == "awaiting_payment_proof":
        inv_id = state["inv_id"]
        USER_STATES.pop(user_id, None)
        with db.lock, db._connect() as conn:
            inv = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (inv_id,)).fetchone()
            if not inv:
                bot.send_message(chat_id, "❌ الفاتورة غير موجودة.")
                return
            conn.execute("UPDATE invoices SET proof_text = ?, status = 'review' WHERE invoice_id = ?", (text, inv_id))
            conn.commit()

        bot.send_message(chat_id, f"✅ تم إرسال إثبات الفاتورة `{inv_id}` للإدارة بنجاح!", reply_markup=main_menu_keyboard(user_id))
        for adm in PRIMARY_ADMINS:
            bot.send_message(
                adm,
                f"🔔 **طلب شحن جديد!**\n🧾 الفاتورة: `{inv_id}`\n👤 المستخدم: `{user_id}` (@{username})\n💳 البوابة: `{inv['gateway']}`\n💵 المبلغ: `${inv['amount_usd']:.2f}` (`{inv['amount_stars']} ⭐`)\n📝 الإثبات:\n`{text}`",
                reply_markup={"inline_keyboard": [[{"text": "✅ قبول وشحن", "callback_data": f"adm_approve_inv:{inv_id}"}, {"text": "❌ رفض", "callback_data": f"adm_reject_inv:{inv_id}"}]]}
            )
        return

    if not db.is_admin(user_id):
        USER_STATES.pop(user_id, None)
        return

    if action in ("adm_add_bal", "adm_sub_bal", "adm_set_bal"):
        parts = text.split()
        if len(parts) < 2:
            bot.send_message(chat_id, "❌ الصيغة: `USER_ID AMOUNT_USD [AMOUNT_STARS]`")
            return
        try:
            target_uid, amt_usd = int(parts[0]), float(parts[1])
            stars_per_usd = float(db.get_setting("stars_per_usd", "50"))
            amt_stars = int(parts[2]) if len(parts) >= 3 else int(round(amt_usd * stars_per_usd))
        except Exception:
            bot.send_message(chat_id, "❌ تأكد من الأرقام.")
            return

        db.ensure_user(target_uid)
        if action == "adm_add_bal":
            db.update_balance(target_uid, delta_usd=amt_usd, delta_stars=amt_stars)
            bot.send_message(target_uid, f"🎁 **تم إضافة رصيد لحسابك من الإدارة:** `${amt_usd:.2f}` (`{amt_stars} ⭐`)")
        elif action == "adm_sub_bal":
            db.update_balance(target_uid, delta_usd=-amt_usd, delta_stars=-amt_stars)
            bot.send_message(target_uid, f"⚠️ **تم خصم رصيد من حسابك:** `${amt_usd:.2f}` (`{amt_stars} ⭐`)")
        else:
            db.set_balance(target_uid, new_usd=amt_usd, new_stars=amt_stars)

        USER_STATES.pop(user_id, None)
        tu = db.get_user(target_uid)
        bot.send_message(chat_id, f"✅ تم التحديث للمستخدم `{target_uid}`!\n💵 الرصيد: `${tu['balance_usd']:.2f}` | ⭐ النجوم: `{tu['balance_stars']} ⭐`", reply_markup=admin_panel_keyboard())
        return

    if action == "adm_new_coupon":
        parts = text.split()
        if len(parts) < 3:
            bot.send_message(chat_id, "❌ الصيغة: `CODE AMOUNT_USD MAX_USES`")
            return
        code, amt_usd, max_u = parts[0].strip(), float(parts[1]), int(parts[2])
        amt_stars = int(round(amt_usd * float(db.get_setting("stars_per_usd", "50"))))
        with db.lock, db._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO coupons (code, amount_usd, amount_stars, max_uses, used_count, used_by) VALUES (?, ?, ?, ?, 0, '[]')",
                         (code, amt_usd, amt_stars, max_u))
            conn.commit()
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, f"✅ تم إنشاء الكود `{code}` بقيمة `${amt_usd:.2f}` (`{amt_stars} ⭐`) لـ `{max_u}` مستخدمين.", reply_markup=admin_panel_keyboard())
        return

    if action == "adm_broadcast_msg":
        USER_STATES.pop(user_id, None)
        with db.lock, db._connect() as conn:
            all_users = [r["user_id"] for r in conn.execute("SELECT user_id FROM users").fetchall()]
        sent_ok, failed = 0, 0
        for uid in all_users:
            if bot.send_message(uid, f"📢 **إشعار من الإدارة:**\n\n{text}").get("ok"):
                sent_ok += 1
            else:
                failed += 1
            time.sleep(0.04)
        bot.send_message(chat_id, f"✅ اكتملت الإذاعة!\n📬 وصلت: `{sent_ok}` | ⚠️ فشل: `{failed}`", reply_markup=admin_panel_keyboard())
        return

    if action == "adm_add_force_ch":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) < 3:
            bot.send_message(chat_id, "❌ الصيغة: `@channel | اسم القناة | الرابط`")
            return
        with db.lock, db._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO force_channels (channel_id, title, invite_link) VALUES (?, ?, ?)", (parts[0], parts[1], parts[2]))
            conn.commit()
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, f"✅ تم إضافة قناة الاشتراك الإجباري `{parts[1]}`!", reply_markup=admin_panel_keyboard())
        return

    if action == "adm_edit_plan":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) < 6:
            bot.send_message(chat_id, "❌ الصيغة: `id | الاسم | السعر_$ | السعر_⭐ | عدد_البوتات | الرام_MB`")
            return
        pid, pname, pusd, pstars, pmax, pram = parts[0], parts[1], float(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
        plans = db.get_plans()
        updated = False
        for p in plans:
            if p["id"] == pid:
                p.update({"name": pname, "price_usd": pusd, "price_stars": pstars, "max_bots": pmax, "ram_mb": pram})
                updated = True
                break
        if not updated:
            plans.append({"id": pid, "name": pname, "price_usd": pusd, "price_stars": pstars, "max_bots": pmax, "ram_mb": pram, "duration_days": 30})
        db.save_plans(plans)
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, f"✅ تم حفظ الخطة **{pname}** (`${pusd}` / `{pstars} ⭐`)!", reply_markup=admin_panel_keyboard())
        return

    if action == "adm_edit_gateway":
        gw_key = state["gw_key"]
        parts = [p.strip() for p in text.split("|")]
        gateways = db.get_gateways()
        if gw_key in gateways:
            if len(parts) >= 1 and parts[0]:
                gateways[gw_key]["api_key"] = parts[0]
            if len(parts) >= 2 and parts[1]:
                gateways[gw_key]["wallet_id"] = parts[1]
            if len(parts) >= 3 and parts[2]:
                gateways[gw_key]["instructions"] = parts[2]
            db.save_gateways(gateways)
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, f"✅ تم تحديث بوابة `{gw_key}`!", reply_markup=admin_panel_keyboard())
        return

    if action == "adm_edit_free_limits":
        parts = text.split()
        if len(parts) < 2:
            bot.send_message(chat_id, "❌ أرسل: `أقصى_بوتات_مجانية سعر_النجمة_للدولار`")
            return
        db.set_setting("free_mode_max_bots", int(parts[0]))
        db.set_setting("stars_per_usd", float(parts[1]))
        USER_STATES.pop(user_id, None)
        bot.send_message(chat_id, "✅ تم تحديث إعدادات الوضع المجاني وسعر النجوم!", reply_markup=admin_panel_keyboard())
        return

    if action == "adm_lookup_user":
        try:
            target_uid = int(text.strip())
        except ValueError:
            bot.send_message(chat_id, "❌ أرسل أيدي رقمي صحيح.")
            return
        USER_STATES.pop(user_id, None)
        u = db.ensure_user(target_uid)
        ubots = pm.get_user_bots(target_uid)
        bot.send_message(
            chat_id,
            f"👤 **المستخدم `{target_uid}`:**\n💵 الرصيد: `${u['balance_usd']:.2f}` | ⭐ النجوم: `{u['balance_stars']} ⭐`\n🤖 البوتات: `{len(ubots)}` | 🚫 محظور: `{u['is_banned']}` | 👑 مطور: `{u['is_admin']}`",
            reply_markup={"inline_keyboard": [
                [{"text": "🟢 فك الحظر" if u["is_banned"] else "🚫 حظر", "callback_data": f"adm_toggle_ban:{target_uid}"},
                 {"text": "⬇️ تنزيل" if u["is_admin"] else "👑 ترقية لمطور", "callback_data": f"adm_toggle_admin:{target_uid}"}],
                [{"text": "🔙 لوحة المطور", "callback_data": "admin_panel"}]
            ]}
        )


# ==============================================================================
# 8. معالج الأزرار التفاعلية (CALLBACK QUERY HANDLER)
# ==============================================================================
def handle_callback(cb):
    cb_id = cb["id"]
    from_user = cb["from"]
    user_id = from_user["id"]
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id", user_id)
    msg_id = msg.get("message_id")
    data = cb.get("data", "")

    db.ensure_user(user_id, from_user.get("username", ""), from_user.get("first_name", ""))

    if data == "verify_sub":
        ok_sub, _ = check_force_sub(user_id)
        if ok_sub:
            bot.answer_callback(cb_id, "✅ تم التحقق من الاشتراك!")
            bot.edit_message(chat_id, msg_id, build_home_text(user_id), reply_markup=main_menu_keyboard(user_id))
        else:
            bot.answer_callback(cb_id, "❌ لم تشترك في جميع القنوات بعد!", show_alert=True)
        return

    if data == "back_home":
        USER_STATES.pop(user_id, None)
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, build_home_text(user_id), reply_markup=main_menu_keyboard(user_id))
        return

    if data == "new_bot":
        limits = get_user_effective_limits(user_id)
        if len(pm.get_user_bots(user_id)) >= limits["max_bots"]:
            bot.answer_callback(cb_id, f"⚠️ وصلت للحد الأقصى ({limits['max_bots']} بوتات).", show_alert=True)
            return
        USER_STATES[user_id] = {"action": "awaiting_bot_upload"}
        bot.answer_callback(cb_id)
        bot.edit_message(
            chat_id, msg_id,
            "📤 **استضافة بوت / مشروع جديد:**\nأرسل الآن ملف `.py` أو `.js` أو `.sh` أو أرشيف `.zip` يحتوي على مشروعك:",
            reply_markup={"inline_keyboard": [[{"text": "🔙 إلغاء", "callback_data": "back_home"}]]}
        )
        return

    if data == "my_bots":
        bot.answer_callback(cb_id)
        ubots = pm.get_user_bots(user_id)
        if not ubots:
            bot.edit_message(chat_id, msg_id, "🤖 **ليس لديك بوتات مستضافة حالياً.**",
                             reply_markup={"inline_keyboard": [[{"text": "➕ استضافة بوت الآن", "callback_data": "new_bot"}], [{"text": "🔙 رجوع", "callback_data": "back_home"}]]})
            return
        kb = [[{"text": f"{'🟢' if b['status']=='running' else '🔴'} {b['name']} [{b['status']}]", "callback_data": f"manage_bot:{b['bot_id']}"}] for b in ubots]
        kb.append([{"text": "➕ إضافة بوت جديد", "callback_data": "new_bot"}])
        kb.append([{"text": "🔙 القائمة الرئيسية", "callback_data": "back_home"}])
        bot.edit_message(chat_id, msg_id, "🤖 **قائمة بوتاتك المستضافة:**", reply_markup={"inline_keyboard": kb})
        return

    if data.startswith("manage_bot:"):
        bot_id = data.split(":", 1)[1]
        b = pm.get_bot(bot_id)
        if not b or (b["owner_id"] != user_id and not db.is_admin(user_id)):
            bot.answer_callback(cb_id, "❌ غير مصرح.", show_alert=True)
            return
        bot.answer_callback(cb_id)
        text = (
            f"🎛️ **لوحة التحكم بالبوت `{b['name']}`**\n"
            f"🆔 المعرف: `{b['bot_id']}` | البيئة: `{b['runtime']}`\n"
            f"📄 الملف الرئيسي: `{b['main_file']}` | الحالة: `{'🟢 يعمل' if b['status']=='running' else '🔴 متوقف'}` (PID: `{b['pid'] or 'N/A'}`)\n"
            f"♻️ مرات الإنعاش التلقائي: `{b['restart_count']}`"
        )
        kb = [
            [{"text": "▶️ تشغيل", "callback_data": f"bot_act:start:{bot_id}"}, {"text": "🔄 إعادة تشغيل", "callback_data": f"bot_act:restart:{bot_id}"}, {"text": "🛑 إيقاف", "callback_data": f"bot_act:stop:{bot_id}"}],
            [{"text": "📜 السجل (Logs)", "callback_data": f"bot_act:logs:{bot_id}"}, {"text": "🧹 مسح السجل", "callback_data": f"bot_act:clearlogs:{bot_id}"}],
            [{"text": "📦 تثبيت مكتبة (pip)", "callback_data": f"bot_act:pip:{bot_id}"}, {"text": "🔐 متغير بيئة (ENV)", "callback_data": f"bot_act:env:{bot_id}"}],
            [{"text": "✏️ تغيير الملف الرئيسي", "callback_data": f"bot_act:mainfile:{bot_id}"}, {"text": "🗑️ حذف نهائي", "callback_data": f"bot_act:delete:{bot_id}"}],
            [{"text": "🔙 لقائمة بوتاتي", "callback_data": "my_bots"}]
        ]
        bot.edit_message(chat_id, msg_id, text, reply_markup={"inline_keyboard": kb})
        return

    if data.startswith("bot_act:"):
        _, act, bot_id = data.split(":", 2)
        b = pm.get_bot(bot_id)
        if not b or (b["owner_id"] != user_id and not db.is_admin(user_id)):
            bot.answer_callback(cb_id, "❌ غير مصرح.", show_alert=True)
            return
        if act in ("start", "stop", "restart"):
            _, m = getattr(pm, f"{act}_bot")(bot_id)
            bot.answer_callback(cb_id, m, show_alert=True)
            cb["data"] = f"manage_bot:{bot_id}"
            handle_callback(cb)
        elif act == "logs":
            bot.answer_callback(cb_id)
            bot.edit_message(chat_id, msg_id, f"📜 **سجل `{b['name']}`:**\n```\n{pm.get_logs(bot_id)}\n```",
                             reply_markup={"inline_keyboard": [[{"text": "🔄 تحديث", "callback_data": f"bot_act:logs:{bot_id}"}], [{"text": "🔙 رجوع", "callback_data": f"manage_bot:{bot_id}"}]]})
        elif act == "clearlogs":
            pm.clear_logs(bot_id)
            bot.answer_callback(cb_id, "🧹 تم مسح السجل!")
            cb["data"] = f"manage_bot:{bot_id}"
            handle_callback(cb)
        elif act == "pip":
            USER_STATES[user_id] = {"action": "awaiting_pip_pkg", "bot_id": bot_id}
            bot.answer_callback(cb_id)
            bot.edit_message(chat_id, msg_id, "📦 أرسل اسم المكتبة لتثبيتها (مثال: `pyTelegramBotAPI requests`):",
                             reply_markup={"inline_keyboard": [[{"text": "🔙 إلغاء", "callback_data": f"manage_bot:{bot_id}"}]]})
        elif act == "env":
            USER_STATES[user_id] = {"action": "awaiting_env_var", "bot_id": bot_id}
            bot.answer_callback(cb_id)
            bot.edit_message(chat_id, msg_id, "🔐 أرسل المتغير بالصيغة `KEY=VALUE`:",
                             reply_markup={"inline_keyboard": [[{"text": "🔙 إلغاء", "callback_data": f"manage_bot:{bot_id}"}]]})
        elif act == "mainfile":
            USER_STATES[user_id] = {"action": "awaiting_main_file", "bot_id": bot_id}
            bot.answer_callback(cb_id)
            bot.edit_message(chat_id, msg_id, f"✏️ أرسل اسم الملف الرئيسي الجديد (الحالي: `{b['main_file']}`):",
                             reply_markup={"inline_keyboard": [[{"text": "🔙 إلغاء", "callback_data": f"manage_bot:{bot_id}"}]]})
        elif act == "delete":
            pm.delete_bot(bot_id)
            bot.answer_callback(cb_id, "🗑️ تم حذف البوت نهائياً.", show_alert=True)
            cb["data"] = "my_bots"
            handle_callback(cb)
        return

    if data == "wallet":
        bot.answer_callback(cb_id)
        u = db.get_user(user_id)
        kb = [[{"text": g["name"], "callback_data": f"pay_gw:{k}"}] for k, g in db.get_gateways().items() if g.get("enabled", True)]
        kb.append([{"text": "🎟️ استرداد كود هدية", "callback_data": "redeem_coupon"}])
        kb.append([{"text": "🔙 القائمة الرئيسية", "callback_data": "back_home"}])
        bot.edit_message(
            chat_id, msg_id,
            f"💰 **محفظتك وبوابات الدفع العالمية**\n💵 الرصيد: `${u['balance_usd']:.2f}` | ⭐ النجوم: `{u['balance_stars']} ⭐`\nاختر طريقة الشحن:",
            reply_markup={"inline_keyboard": kb}
        )
        return

    if data.startswith("pay_gw:"):
        gw_key = data.split(":", 1)[1]
        gw = db.get_gateways().get(gw_key, {})
        USER_STATES[user_id] = {"action": "awaiting_deposit_amount", "gateway": gw_key}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, f"💳 **{gw.get('name', gw_key)}**\n{gw.get('instructions', '')}\n\n💵 أرسل المبلغ المراد شحنه بالدولار (مثلاً `5` أو `10`):",
                         reply_markup={"inline_keyboard": [[{"text": "🔙 للمحفظة", "callback_data": "wallet"}]]})
        return

    if data.startswith("check_api_inv:"):
        inv_id = data.split(":", 1)[1]
        with db.lock, db._connect() as conn:
            inv = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (inv_id,)).fetchone()
        if not inv or inv["status"] == "paid":
            bot.answer_callback(cb_id, "✅ الفاتورة مدفوعة مسبقاً.", show_alert=True)
            return
        gw = db.get_gateways().get(inv["gateway"], {})
        if PaymentEngine.check_cryptobot_invoice(gw.get("api_key", ""), gw.get("secret", "https://pay.crypt.bot/api"), inv["external_ref"]):
            with db.lock, db._connect() as conn:
                conn.execute("UPDATE invoices SET status = 'paid' WHERE invoice_id = ?", (inv_id,))
                conn.commit()
            db.update_balance(user_id, delta_usd=inv["amount_usd"], delta_stars=inv["amount_stars"])
            bot.answer_callback(cb_id, "🎉 تم التحقق وشحن رصيدك تلقائياً!", show_alert=True)
            bot.edit_message(chat_id, msg_id, build_home_text(user_id), reply_markup=main_menu_keyboard(user_id))
        else:
            bot.answer_callback(cb_id, "⏳ لم يكتمل الدفع بعد.", show_alert=True)
        return

    if data.startswith("submit_proof:"):
        inv_id = data.split(":", 1)[1]
        USER_STATES[user_id] = {"action": "awaiting_payment_proof", "inv_id": inv_id}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, f"📩 أرسل رقم العملية (Transaction ID) لتأكيد الفاتورة `{inv_id}`:",
                         reply_markup={"inline_keyboard": [[{"text": "🔙 إلغاء", "callback_data": "wallet"}]]})
        return

    if data == "plans_menu":
        bot.answer_callback(cb_id)
        if db.get_setting("paid_mode", "0") != "1":
            bot.edit_message(
                chat_id, msg_id,
                f"🎁 **الوضع المجاني مفعل حالياً لجميع المستخدمين!**\n• عدد البوتات المجانية لكل حساب: `{db.get_setting('free_mode_max_bots', '3')}`\n• الرام المتاحة: `{db.get_setting('free_mode_ram_mb', '512')} MB`",
                reply_markup={"inline_keyboard": [[{"text": "➕ استضافة بوت الآن", "callback_data": "new_bot"}], [{"text": "🔙 رجوع", "callback_data": "back_home"}]]}
            )
            return
        u = db.get_user(user_id)
        txt = f"💎 **خطط الاستضافة (رصيدك: `${u['balance_usd']:.2f}` | `{u['balance_stars']} ⭐`):**\n"
        kb = []
        for p in db.get_plans():
            txt += f"\n🔹 **{p['name']}**: `${p['price_usd']}` أو `{p['price_stars']} ⭐` ({p['max_bots']} بوتات، {p['ram_mb']}MB)"
            if p["price_usd"] > 0 or p["price_stars"] > 0:
                kb.append([{"text": f"💵 شراء (${p['price_usd']})", "callback_data": f"buy_plan:usd:{p['id']}"},
                           {"text": f"⭐ شراء ({p['price_stars']} ⭐)", "callback_data": f"buy_plan:stars:{p['id']}"}])
        kb.append([{"text": "💰 شحن المحفظة", "callback_data": "wallet"}, {"text": "🔙 رجوع", "callback_data": "back_home"}])
        bot.edit_message(chat_id, msg_id, txt, reply_markup={"inline_keyboard": kb})
        return

    if data.startswith("buy_plan:"):
        _, curr, plan_id = data.split(":", 2)
        plan = {p["id"]: p for p in db.get_plans()}.get(plan_id)
        if not plan:
            bot.answer_callback(cb_id, "❌ الخطة غير موجودة.", show_alert=True)
            return
        u = db.get_user(user_id)
        if curr == "usd":
            if u["balance_usd"] < plan["price_usd"]:
                bot.answer_callback(cb_id, f"❌ رصيدك بالدولار غير كافٍ (${plan['price_usd']}).", show_alert=True)
                return
            db.update_balance(user_id, delta_usd=-plan["price_usd"])
        else:
            if u["balance_stars"] < plan["price_stars"]:
                bot.answer_callback(cb_id, f"❌ رصيدك بالنجوم غير كافٍ ({plan['price_stars']} ⭐).", show_alert=True)
                return
            db.update_balance(user_id, delta_stars=-plan["price_stars"])
        exp_date = (datetime.utcnow() + timedelta(days=int(plan.get("duration_days", 30)))).strftime("%Y-%m-%d %H:%M:%S")
        with db.lock, db._connect() as conn:
            conn.execute("UPDATE users SET plan_id = ?, plan_expiry = ? WHERE user_id = ?", (plan_id, exp_date, user_id))
            conn.commit()
        bot.answer_callback(cb_id, f"🎉 تم تفعيل {plan['name']} بنجاح!", show_alert=True)
        bot.edit_message(chat_id, msg_id, build_home_text(user_id), reply_markup=main_menu_keyboard(user_id))
        return

    if data == "redeem_coupon":
        USER_STATES[user_id] = {"action": "awaiting_coupon_code"}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, "🎟️ أرسل كود الهدية الآن:", reply_markup={"inline_keyboard": [[{"text": "🔙 إلغاء", "callback_data": "back_home"}]]})
        return

    if data == "server_status":
        cpu_load, ram_info, disk_info = get_system_metrics()
        all_bots = pm.get_all_bots()
        bot.answer_callback(cb_id)
        bot.edit_message(
            chat_id, msg_id,
            f"📊 **حالة السيرفر:**\n⚡ CPU: `{cpu_load}`\n🧠 RAM: `{ram_info}`\n💾 Disk: `{disk_info}`\n🤖 البوتات المستضافة: `{len(all_bots)}`",
            reply_markup={"inline_keyboard": [[{"text": "🔄 تحديث", "callback_data": "server_status"}], [{"text": "🔙 رجوع", "callback_data": "back_home"}]]}
        )
        return

    if data == "help_guide":
        bot.answer_callback(cb_id)
        bot.edit_message(
            chat_id, msg_id,
            "📚 **دليل الاستخدام:**\n1️⃣ اضغط `استضافة بوت جديد` وأرسل ملف `.py` أو `.js` أو أرشيف `.zip`.\n2️⃣ يثبت البوت ملف `requirements.txt` تلقائياً ويعيد تشغيل البوت إذا توقف 24/7.",
            reply_markup={"inline_keyboard": [[{"text": "🔙 القائمة الرئيسية", "callback_data": "back_home"}]]}
        )
        return

    if not db.is_admin(user_id):
        bot.answer_callback(cb_id, "🚫 مخصص للمطورين فقط!", show_alert=True)
        return

    if data == "admin_panel":
        USER_STATES.pop(user_id, None)
        bot.answer_callback(cb_id)
        with db.lock, db._connect() as conn:
            u_cnt = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
            b_cnt = conn.execute("SELECT COUNT(*) as c FROM hosted_bots").fetchone()["c"]
        paid_mode = db.get_setting("paid_mode", "0") == "1"
        bot.edit_message(
            chat_id, msg_id,
            f"👑 **لوحة تحكم المطور الشاملة**\n👥 المستخدمون: `{u_cnt}` | 🤖 البوتات: `{b_cnt}`\n💰 الوضع الحالي: **{'مدفوع ($ + ⭐)' if paid_mode else 'مجاني للجميع 🎁'}**",
            reply_markup=admin_panel_keyboard()
        )
        return

    if data == "adm_toggle_paid":
        new_val = "0" if db.get_setting("paid_mode", "0") == "1" else "1"
        db.set_setting("paid_mode", new_val)
        bot.answer_callback(cb_id, "💰 تم تفعيل الوضع المدفوع!" if new_val == "1" else "🎁 عاد البوت للوضع المجاني الطبيعي!", show_alert=True)
        cb["data"] = "admin_panel"
        handle_callback(cb)
        return

    if data == "adm_toggle_maint":
        db.set_setting("maintenance_mode", "0" if db.get_setting("maintenance_mode", "0") == "1" else "1")
        bot.answer_callback(cb_id, "✅ تم تحديث وضع الصيانة.")
        cb["data"] = "admin_panel"
        handle_callback(cb)
        return

    if data == "adm_toggle_pip":
        db.set_setting("allow_pip_install", "0" if db.get_setting("allow_pip_install", "1") == "1" else "1")
        bot.answer_callback(cb_id, "✅ تم تحديث صلاحية pip.")
        cb["data"] = "admin_panel"
        handle_callback(cb)
        return

    if data in ("adm_add_balance", "adm_sub_balance", "adm_set_balance"):
        act_map = {"adm_add_balance": "adm_add_bal", "adm_sub_balance": "adm_sub_bal", "adm_set_balance": "adm_set_bal"}
        USER_STATES[user_id] = {"action": act_map[data]}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, "💵 أرسل: `USER_ID AMOUNT_USD [AMOUNT_STARS]`\nمثال: `6486550968 15 750`",
                         reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": "admin_panel"}]]})
        return

    if data.startswith("adm_approve_inv:") or data.startswith("adm_reject_inv:"):
        is_app = data.startswith("adm_approve_inv:")
        inv_id = data.split(":", 1)[1]
        with db.lock, db._connect() as conn:
            inv = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (inv_id,)).fetchone()
            if not inv or inv["status"] == "paid":
                bot.answer_callback(cb_id, "⚠️ تمت معالجتها مسبقاً.", show_alert=True)
                return
            conn.execute("UPDATE invoices SET status = ? WHERE invoice_id = ?", ("paid" if is_app else "rejected", inv_id))
            conn.commit()
        if is_app:
            db.update_balance(inv["user_id"], delta_usd=inv["amount_usd"], delta_stars=inv["amount_stars"])
            bot.send_message(inv["user_id"], f"🎉 **تمت الموافقة على الفاتورة `{inv_id}` وإضافة `${inv['amount_usd']:.2f}` (`{inv['amount_stars']} ⭐`)!**")
            bot.edit_message(chat_id, msg_id, f"✅ تم قبول الفاتورة `{inv_id}`.")
        else:
            bot.send_message(inv["user_id"], f"❌ تم رفض الفاتورة `{inv_id}`.")
            bot.edit_message(chat_id, msg_id, f"❌ تم رفض الفاتورة `{inv_id}`.")
        return

    if data == "adm_manage_plans":
        bot.answer_callback(cb_id)
        txt = "💲 **الخطط الحالية:**\n" + "\n".join([f"• `{p['id']}` | {p['name']} — `${p['price_usd']}` / `{p['price_stars']} ⭐` ({p['max_bots']} بوتات)" for p in db.get_plans()])
        txt += "\n\n✏️ للتعديل أو الإضافة أرسل:\n`id | الاسم | السعر_$ | السعر_⭐ | عدد_البوتات | الرام_MB`"
        USER_STATES[user_id] = {"action": "adm_edit_plan"}
        bot.edit_message(chat_id, msg_id, txt, reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": "admin_panel"}]]})
        return

    if data == "adm_manage_gateways":
        bot.answer_callback(cb_id)
        kb = [[{"text": f"{'🟢' if g.get('enabled', True) else '🔴'} {g['name'][:25]}", "callback_data": f"adm_gw_toggle:{k}"},
               {"text": "⚙️ تعديل API", "callback_data": f"adm_gw_edit:{k}"}] for k, g in db.get_gateways().items()]
        kb.append([{"text": "🔙 رجوع", "callback_data": "admin_panel"}])
        bot.edit_message(chat_id, msg_id, "💳 **إدارة بوابات الدفع والـ API:**", reply_markup={"inline_keyboard": kb})
        return

    if data.startswith("adm_gw_toggle:"):
        gk = data.split(":", 1)[1]
        gws = db.get_gateways()
        if gk in gws:
            gws[gk]["enabled"] = not gws[gk].get("enabled", True)
            db.save_gateways(gws)
        bot.answer_callback(cb_id, "✅ تم التحديث.")
        cb["data"] = "adm_manage_gateways"
        handle_callback(cb)
        return

    if data.startswith("adm_gw_edit:"):
        gk = data.split(":", 1)[1]
        gw = db.get_gateways().get(gk, {})
        USER_STATES[user_id] = {"action": "adm_edit_gateway", "gw_key": gk}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, f"⚙️ **تعديل `{gw.get('name', gk)}`:**\nأرسل: `API_KEY | WALLET_ID | التعليمات`",
                         reply_markup={"inline_keyboard": [[{"text": "🔙 إلغاء", "callback_data": "adm_manage_gateways"}]]})
        return

    if data == "adm_create_coupon":
        USER_STATES[user_id] = {"action": "adm_new_coupon"}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, "🎟️ أرسل: `CODE AMOUNT_USD MAX_USES`", reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": "admin_panel"}]]})
        return

    if data == "adm_broadcast":
        USER_STATES[user_id] = {"action": "adm_broadcast_msg"}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, "📢 أرسل رسالة الإذاعة الآن:", reply_markup={"inline_keyboard": [[{"text": "🔙 إلغاء", "callback_data": "admin_panel"}]]})
        return

    if data == "adm_force_sub":
        bot.answer_callback(cb_id)
        with db.lock, db._connect() as conn:
            chs = [dict(r) for r in conn.execute("SELECT * FROM force_channels").fetchall()]
        kb = [[{"text": f"🗑️ حذف: {c['title']}", "callback_data": f"adm_del_fch:{c['channel_id']}"}] for c in chs]
        kb.append([{"text": "➕ إضافة قناة اشتراك إجباري", "callback_data": "adm_add_fch_btn"}])
        kb.append([{"text": "🔙 رجوع", "callback_data": "admin_panel"}])
        bot.edit_message(chat_id, msg_id, f"🔒 **قنوات الاشتراك الإجباري ({len(chs)}):**", reply_markup={"inline_keyboard": kb})
        return

    if data == "adm_add_fch_btn":
        USER_STATES[user_id] = {"action": "adm_add_force_ch"}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, "➕ أرسل: `@channel_username | اسم القناة | رابط الدعوة`", reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": "adm_force_sub"}]]})
        return

    if data.startswith("adm_del_fch:"):
        chid = data.split(":", 1)[1]
        with db.lock, db._connect() as conn:
            conn.execute("DELETE FROM force_channels WHERE channel_id = ?", (chid,))
            conn.commit()
        bot.answer_callback(cb_id, "🗑️ تم الحذف.")
        cb["data"] = "adm_force_sub"
        handle_callback(cb)
        return

    if data == "adm_all_bots":
        bot.answer_callback(cb_id)
        all_b = pm.get_all_bots()
        kb = [[{"text": f"{'🟢' if b['status']=='running' else '🔴'} {b['name']} ({b['owner_id']})", "callback_data": f"manage_bot:{b['bot_id']}"}] for b in all_b[:25]]
        kb.append([{"text": "▶️ تشغيل الكل", "callback_data": "adm_mass_bots:start"}, {"text": "🛑 إيقاف الكل", "callback_data": "adm_mass_bots:stop"}])
        kb.append([{"text": "🔙 رجوع", "callback_data": "admin_panel"}])
        bot.edit_message(chat_id, msg_id, f"🤖 **كل البوتات المستضافة (`{len(all_b)}`):**", reply_markup={"inline_keyboard": kb})
        return

    if data.startswith("adm_mass_bots:"):
        op = data.split(":", 1)[1]
        for b in pm.get_all_bots():
            getattr(pm, f"{op}_bot")(b["bot_id"])
        bot.answer_callback(cb_id, f"✅ تم تنفيذ ({op}) للكل!", show_alert=True)
        cb["data"] = "adm_all_bots"
        handle_callback(cb)
        return

    if data == "adm_user_manage":
        USER_STATES[user_id] = {"action": "adm_lookup_user"}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, "👤 أرسل الأيدي الرقمي (User ID) للمستخدم:", reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": "admin_panel"}]]})
        return

    if data.startswith("adm_toggle_ban:"):
        t_uid = int(data.split(":", 1)[1])
        if t_uid not in PRIMARY_ADMINS:
            u = db.get_user(t_uid)
            with db.lock, db._connect() as conn:
                conn.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (0 if u["is_banned"] else 1, t_uid))
                conn.commit()
        bot.answer_callback(cb_id, "✅ تم التحديث.", show_alert=True)
        cb["data"] = "admin_panel"
        handle_callback(cb)
        return

    if data.startswith("adm_toggle_admin:"):
        t_uid = int(data.split(":", 1)[1])
        if t_uid not in PRIMARY_ADMINS:
            u = db.get_user(t_uid)
            with db.lock, db._connect() as conn:
                conn.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (0 if u["is_admin"] else 1, t_uid))
                conn.commit()
        bot.answer_callback(cb_id, "✅ تم التحديث.", show_alert=True)
        cb["data"] = "admin_panel"
        handle_callback(cb)
        return

    if data == "adm_free_limits":
        USER_STATES[user_id] = {"action": "adm_edit_free_limits"}
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, "⚙️ أرسل: `أقصى_بوتات_مجانية سعر_النجمة_للدولار` (مثال: `3 50`):", reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": "admin_panel"}]]})
        return

    if data == "adm_admins_list":
        with db.lock, db._connect() as conn:
            adms = [dict(r) for r in conn.execute("SELECT user_id, username, full_name FROM users WHERE is_admin = 1").fetchall()]
        lines = "\n".join([f"• `{a['user_id']}` — {a['full_name']} (@{a['username']})" for a in adms])
        bot.answer_callback(cb_id)
        bot.edit_message(chat_id, msg_id, f"👑 **المطورون:**\n{lines}", reply_markup={"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": "admin_panel"}]]})
        return

    if data == "adm_backup":
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        zip_base = os.path.join(BACKUPS_DIR, f"backup_{ts}")
        shutil.make_archive(zip_base, "zip", DATA_DIR)
        bot.answer_callback(cb_id, f"✅ تم حفظ النسخة: {zip_base}.zip", show_alert=True)
        return


# ==============================================================================
# 9. حلقة الاستماع الرئيسية الموفرة للذاكرة (ULTRA-LOW RAM EVENT LOOP)
# ==============================================================================
def run_polling():
    logger.info("🚀 Starting Ultra-Light Telegram Hosting Bot (Low-RAM Mode)...")
    if db.get_setting("auto_boot_bots", "1") == "1":
        for b in pm.get_all_bots():
            if b["status"] == "running":
                pm.start_bot(b["bot_id"])

    offset = 0
    last_watchdog = time.time()

    while True:
        try:
            # فحص البوتات المستضافة وتنظيف الرام كل 15 ثانية بدون فتح خيوط إضافية
            if time.time() - last_watchdog > 15:
                pm.check_watchdog_once()
                gc.collect()
                last_watchdog = time.time()

            res = bot.call("getUpdates", {"offset": offset, "limit": 20, "timeout": 20}, timeout=28)
            if not res.get("ok"):
                time.sleep(2)
                continue

            for upd in res.get("result", []):
                offset = upd["update_id"] + 1
                if "pre_checkout_query" in upd:
                    bot.answer_pre_checkout_query(upd["pre_checkout_query"]["id"], ok=True)
                elif "message" in upd:
                    handle_message(upd["message"])
                elif "callback_query" in upd:
                    handle_callback(upd["callback_query"])

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Loop error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run_polling()