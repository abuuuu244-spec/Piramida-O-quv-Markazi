import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8948763336:AAEmq7Xi6t-MUc3tReSBz6Msbqz87a464ws")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234567890")
raw_admin_id = os.getenv("ADMIN_ID", "").strip()
ADMIN_ID = int(raw_admin_id) if raw_admin_id and raw_admin_id.isdigit() else None
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT", "@Isroilova_Ozoda")
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "+998-97-152-84-00")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida mavjud emas!")

if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD .env faylida mavjud emas!")