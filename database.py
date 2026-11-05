import os
import json
import aiosqlite
from datetime import datetime, date, timedelta
from calendar import monthrange

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "pramida.db")


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        # 1. Foydalanuvchilar jadvali
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_seen TEXT,
            joined_at TEXT
        )
        """)

        # 2. O'quvchilar jadvali (Ro'yxatdan o'tganlar va to'lovlar)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS students (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            subject TEXT NOT NULL,
            teacher TEXT NOT NULL,
            days TEXT NOT NULL,
            time TEXT NOT NULL,
            payment_day INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            payment_status TEXT DEFAULT 'unpaid',
            pending_payment INTEGER DEFAULT 0,
            last_paid TEXT,
            registered_at TEXT,
            sent_reminders TEXT DEFAULT '[]',
            next_payment_date TEXT DEFAULT ''
        )
        """)

        # 3. Fanlar jadvali
        await db.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            teacher TEXT NOT NULL,
            time TEXT NOT NULL,
            small_group TEXT DEFAULT '',
            days TEXT DEFAULT '',
            price TEXT DEFAULT ''
        )
        """)

        # 4. Sozlamalar jadvali
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        # Migratsiya: Agar next_payment_date ustuni bo'lmasa, qo'shish
        cursor = await db.execute("PRAGMA table_info(students)")
        cols = [r[1] for r in await cursor.fetchall()]
        if "next_payment_date" not in cols:
            await db.execute("ALTER TABLE students ADD COLUMN next_payment_date TEXT DEFAULT ''")

        await db.commit()

        # Standart fanlarni faqat birinchi marta kiritish
        cursor = await db.execute("SELECT COUNT(*) FROM subjects")
        count = (await cursor.fetchone())[0]

        if count == 0:
            default_subjects = [
                (
                    "Ona tili",
                    "Bozorboyev Murodbek",
                    "16:00 - 18:00",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Matematika (Kattalar)",
                    "Tursunboyev Haitboy",
                    "16:00 - 18:00",
                    "Ertalabki o'quvchilar: 08:00 - 10:00",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Matematika (Yosh bolalar)",
                    "Ergashev Ohunjon",
                    "16:00 - 18:00",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Matematika (Kichkinalar)",
                    "Saidmurodov Ro'zimurod",
                    "08:00 - 10:00",
                    "Tushdan keyingi guruh: 14:00 - 16:00",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 250 000 so'm"
                ),
                (
                    "Ingliz tili (Ibrohim)",
                    "Majidov Ibrohim",
                    "14:00 - 18:00",
                    "",
                    "Dushanba, Chorshanba, Juma",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Kimyo",
                    "Bekbo'tayev Zohid",
                    "14:00 - 18:00",
                    "",
                    "Dushanba, Chorshanba, Juma",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Rus tili",
                    "Ortiqova Iroda",
                    "14:00 - 16:00",
                    "Ertalabki darsi: 08:00 - 10:00",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Tarix",
                    "Bozorboyev Murodbek",
                    "14:00 - 16:00",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Ingliz tili (Jaloliddin)",
                    "Yangiboyev Jaloliddin",
                    "16:30 - 18:30",
                    "Ertalabki guruh: 08:00 - 10:00",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 250 000 so'm"
                ),
                (
                    "Biologiya",
                    "Abduvoitova Gulnora",
                    "16:30 - 18:30",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Fizika",
                    "Azzamqulov Islombek",
                    "16:30 - 18:30",
                    "",
                    "Dushanba, Chorshanba, Juma",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Huquq",
                    "G'oibnazarov Nodir",
                    "15:00 - 17:00",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Informatika",
                    "Malakali ustoz",
                    "14:00 - 18:00",
                    "Kompyuter savodxonligi va IT",
                    "Dushanba, Chorshanba, Juma",
                    "Oyiga 350 000 so'm"
                )
            ]

            await db.executemany("""
            INSERT INTO subjects
            (name, teacher, time, small_group, days, price)
            VALUES (?, ?, ?, ?, ?, ?)
            """, default_subjects)
            await db.commit()

        # Standart sozlamalar
        default_settings = {
            "center_name": "Piramida O'quv Markazi",
            "address": "Piramida O'quv Markazi",
            "phone": "+998-97-152-84-00",
            "admin_name": "Isroilova Ozoda",
            "admin_username": "@Isroilova_Ozoda",
            "card_number": "8600 5304 1234 5678",
            "card_holder": "Isroilova Ozoda",
            "description": (
                "🎓 <b>PIRAMIDA O'QUV MARKAZI</b>\n\n"
                "Markazimizda abituriyentlar va o'quvchilar uchun sifatli va "
                "chuqurlashtirilgan o'quv kurslari faoliyat yuritadi."
            ),
            "map_url": "https://maps.app.goo.gl/orwFAVu6N3APkD216"
        }

        for key, value in default_settings.items():
            await db.execute("""
            INSERT OR IGNORE INTO settings (key, value)
            VALUES (?, ?)
            """, (key, value))

        await db.commit()


# =========================================================
# USERS
# =========================================================

async def add_user(user_id, username, first_name):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO users (id, username, first_name, last_seen, joined_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_seen=excluded.last_seen
        """, (user_id, username or "", first_name or "", now, now))
        await db.commit()


async def get_users_count():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        return (await cursor.fetchone())[0]


async def get_active_users():
    limit = datetime.now() - timedelta(minutes=5)
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT COUNT(*) FROM users WHERE last_seen >= ?
        """, (limit.isoformat(),))
        return (await cursor.fetchone())[0]


async def get_today_users():
    today = datetime.now().date().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT COUNT(*) FROM users WHERE date(joined_at) = ?
        """, (today,))
        return (await cursor.fetchone())[0]


async def get_all_user_ids():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id FROM users")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


# =========================================================
# DATE CALCULATION HELPERS
# =========================================================

def calculate_next_due_date(payment_day: int, base_date: date = None) -> date:
    """
    To'lov tasdiqlanganda keyingi oyning mos kunini hisoblaydi.
    """
    if base_date is None:
        base_date = date.today()

    year = base_date.year
    month = base_date.month + 1
    if month > 12:
        month = 1
        year += 1

    _, max_days = monthrange(year, month)
    day = min(payment_day, max_days)
    return date(year, month, day)


def advance_payment_date(payment_day: int, current_date_str: str = None) -> str:
    """
    Oylik to'lov sanasini keyingi oyga suradi va DD.MM.YYYY formatida qaytaradi.
    """
    base_date = None
    if current_date_str:
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                base_date = datetime.strptime(str(current_date_str).strip(), fmt).date()
                break
            except Exception:
                pass

    if base_date is None:
        today = date.today()
        _, max_days = monthrange(today.year, today.month)
        curr_due = date(today.year, today.month, min(payment_day, max_days))
        if curr_due > today:
            base_date = curr_due
        else:
            base_date = today

    next_date = calculate_next_due_date(payment_day, base_date)
    return next_date.strftime("%d.%m.%Y")


# =========================================================
# STUDENTS (RO'YXAT VA TO'LOVLAR)
# =========================================================

def _row_to_student(row):
    if not row:
        return None
    try:
        reminders = json.loads(row[13]) if row[13] else []
    except Exception:
        reminders = []

    next_pay_date = row[14] if len(row) > 14 and row[14] else None

    return {
        "user_id": row[0],
        "name": row[1],
        "phone": row[2],
        "subject": row[3],
        "teacher": row[4],
        "days": row[5],
        "time": row[6],
        "payment_day": row[7],
        "amount": row[8],
        "payment_status": row[9] or "unpaid",
        "pending_payment": bool(row[10]),
        "last_paid": row[11],
        "registered_at": row[12],
        "sent_reminders": reminders,
        "next_payment_date": next_pay_date
    }


async def add_student(user_id, data):
    reminders_json = json.dumps(data.get("sent_reminders", []), ensure_ascii=False)
    p_day = int(data["payment_day"])
    next_date = data.get("next_payment_date")
    if not next_date:
        next_date = advance_payment_date(p_day)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO students (
            user_id, name, phone, subject, teacher, days, time,
            payment_day, amount, payment_status, pending_payment,
            last_paid, registered_at, sent_reminders, next_payment_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            phone=excluded.phone,
            subject=excluded.subject,
            teacher=excluded.teacher,
            days=excluded.days,
            time=excluded.time,
            payment_day=excluded.payment_day,
            amount=excluded.amount,
            payment_status=excluded.payment_status,
            pending_payment=excluded.pending_payment,
            last_paid=excluded.last_paid,
            sent_reminders=excluded.sent_reminders,
            next_payment_date=excluded.next_payment_date
        """, (
            user_id,
            data["name"],
            data["phone"],
            data["subject"],
            data["teacher"],
            data["days"],
            data["time"],
            p_day,
            int(data["amount"]),
            data.get("payment_status", "unpaid"),
            1 if data.get("pending_payment") else 0,
            data.get("last_paid"),
            data.get("registered_at", datetime.now().isoformat()),
            reminders_json,
            next_date
        ))
        await db.commit()


async def get_student(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT user_id, name, phone, subject, teacher, days, time,
               payment_day, amount, payment_status, pending_payment,
               last_paid, registered_at, sent_reminders, next_payment_date
        FROM students WHERE user_id=?
        """, (int(user_id),))
        row = await cursor.fetchone()
        return _row_to_student(row)


async def get_students():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT user_id, name, phone, subject, teacher, days, time,
               payment_day, amount, payment_status, pending_payment,
               last_paid, registered_at, sent_reminders, next_payment_date
        FROM students
        ORDER BY name
        """)
        rows = await cursor.fetchall()
        result = {}
        for row in rows:
            student = _row_to_student(row)
            result[str(student["user_id"])] = student
        return result


async def update_student(user_id, **kwargs):
    if not kwargs:
        return False

    valid_cols = {
        "name", "phone", "subject", "teacher", "days", "time",
        "payment_day", "amount", "payment_status", "pending_payment",
        "last_paid", "sent_reminders", "next_payment_date"
    }

    updates = []
    values = []

    for key, val in kwargs.items():
        if key in valid_cols:
            if key == "pending_payment":
                val = 1 if val else 0
            elif key == "sent_reminders" and isinstance(val, (list, set)):
                val = json.dumps(list(val), ensure_ascii=False)
            updates.append(f"{key}=?")
            values.append(val)

    if not updates:
        return False

    values.append(int(user_id))
    sql = f"UPDATE students SET {', '.join(updates)} WHERE user_id=?"

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(sql, values)
        await db.commit()
        return True


async def delete_student(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM students WHERE user_id=?", (int(user_id),))
        await db.commit()


async def mark_reminder(user_id, reminder_key):
    student = await get_student(user_id)
    if not student:
        return False

    sent = student.get("sent_reminders", [])
    if reminder_key in sent:
        return False

    sent.append(reminder_key)
    sent = sent[-100:]  # Oxirgi 100 ta kalitni saqlash

    await update_student(user_id, sent_reminders=sent)
    return True


async def get_pending_payment_students():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT user_id, name, phone, subject, teacher, days, time,
               payment_day, amount, payment_status, pending_payment,
               last_paid, registered_at, sent_reminders, next_payment_date
        FROM students WHERE pending_payment=1
        ORDER BY registered_at
        """)
        rows = await cursor.fetchall()
        return [_row_to_student(r) for r in rows]


async def get_debtor_students():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT user_id, name, phone, subject, teacher, days, time,
               payment_day, amount, payment_status, pending_payment,
               last_paid, registered_at, sent_reminders, next_payment_date
        FROM students WHERE payment_status!='paid'
        ORDER BY name
        """)
        rows = await cursor.fetchall()
        return [_row_to_student(r) for r in rows]


async def get_students_count():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM students")
        return (await cursor.fetchone())[0]


async def get_students_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM students")
        total = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM students WHERE payment_status='paid'")
        paid = (await cursor.fetchone())[0]
        unpaid = total - paid
        return total, paid, unpaid


# =========================================================
# SUBJECTS
# =========================================================

_cached_subjects = []

def get_cached_subjects():
    global _cached_subjects
    return _cached_subjects


async def get_subjects():
    global _cached_subjects
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT id, name, teacher, time, small_group, days, price
        FROM subjects ORDER BY id
        """)
        rows = await cursor.fetchall()
        _cached_subjects = rows
        return rows


async def get_subject(subject_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT id, name, teacher, time, small_group, days, price
        FROM subjects WHERE id=?
        """, (subject_id,))
        return await cursor.fetchone()


async def add_subject(name, teacher, time, small_group="", days="", price=""):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO subjects (name, teacher, time, small_group, days, price)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, teacher, time, small_group, days, price))
        await db.commit()


async def update_subject(subject_id, name, teacher, time, small_group, days="", price=""):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        UPDATE subjects
        SET name=?, teacher=?, time=?, small_group=?, days=?, price=?
        WHERE id=?
        """, (name, teacher, time, small_group, days, price, subject_id))
        await db.commit()


async def delete_subject(subject_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
        await db.commit()


# =========================================================
# SETTINGS
# =========================================================

async def get_setting(key):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
        result = await cursor.fetchone()
        return result[0] if result else ""


async def set_setting(key, value):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (key, value))
        await db.commit()


async def get_authenticated_admins():
    val = await get_setting("authenticated_admins")
    if not val:
        return set()
    try:
        return set(json.loads(val))
    except Exception:
        return set()


async def add_authenticated_admin(user_id):
    admins = await get_authenticated_admins()
    admins.add(int(user_id))
    await set_setting("authenticated_admins", json.dumps(list(admins)))


async def remove_authenticated_admin(user_id):
    admins = await get_authenticated_admins()
    admins.discard(int(user_id))
    await set_setting("authenticated_admins", json.dumps(list(admins)))


async def get_all_settings():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT key, value FROM settings")
        return await cursor.fetchall()