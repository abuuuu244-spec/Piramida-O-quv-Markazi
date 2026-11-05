import html
from datetime import datetime, date, timedelta
from calendar import monthrange
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import get_students, update_student, mark_reminder, get_setting
from keyboards import reminder_payment_keyboard

TZ = ZoneInfo("Asia/Tashkent")
scheduler = AsyncIOScheduler(timezone=TZ)


def get_due_date(year, month, day):
    # 31-kuni bo'lmagan oylarda oyning oxirgi kunini oladi (masalan, 28 yoki 30)
    last_day = monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


async def check_payments(bot):
    today = datetime.now(TZ).date()
    students = await get_students()

    for user_id, student in students.items():

        # Agar to'lov so'rovi adminga yuborilgan bo'lsa va tasdiqlanishini kutayotgan bo'lsa
        if student.get("pending_payment"):
            continue

        # To'lov muddatini aniqlash (next_payment_date mavjud bo'lsa undan foydalanish)
        due = None
        next_pay_str = student.get("next_payment_date")
        if next_pay_str:
            for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
                try:
                    due = datetime.strptime(next_pay_str.strip(), fmt).date()
                    break
                except Exception:
                    pass

        if due is None:
            payment_day = int(student["payment_day"])
            due = get_due_date(today.year, today.month, payment_day)

        # Agar navbatdagi to'lovga hali 3 kundan ko'p vaqt bo'lsa - to'langan deb hisoblanadi
        if due > today and (due - today).days > 3:
            if student["payment_status"] != "paid":
                await update_student(user_id, payment_status="paid")
            continue

        # Agar to'lov muddati kelgan bo'lsa va to'lanmagan bo'lsa, 'unpaid' ga o'tkazish
        if today >= due and student["payment_status"] == "paid":
            await update_student(user_id, payment_status="unpaid")

        admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"

        # Eslatmalar turlari: 3 kun oldin, to'lov kuni va 2 kun o'tgach
        reminders = [
            (
                due - timedelta(days=3),
                "before",
                f"Navbatdagi oylik to‘lovingizga <b>3 kun</b> qoldi.",
                "To‘lovni amalga oshirish uchun pastdagi tugmani bosing 👇"
            ),
            (
                due,
                "due",
                "Sizning oylik to‘lov vaqtingiz keldi.",
                "To‘lovni amalga oshirish uchun pastdagi tugmani bosing 👇"
            ),
            (
                due + timedelta(days=2),
                "overdue",
                "⚠️ Sizning oylik to‘lov muddatingiz <b>o‘tib ketdi</b>.",
                "Iltimos, to‘lovni amalga oshirish uchun pastdagi tugmani bosing 👇"
            )
        ]

        for reminder_date, reminder_type, msg_line, action_line in reminders:
            if today != reminder_date:
                continue

            reminder_key = f"{due.strftime('%Y-%m')}-{reminder_type}"
            sent = await mark_reminder(user_id, reminder_key)

            if not sent:
                continue

            student_name = html.escape(str(student.get("name") or student.get("full_name") or "O‘quvchi"))
            subject_name = html.escape(str(student.get("subject", "")))
            due_str = due.strftime("%d.%m.%Y")
            amount_val = student.get("amount", 0)

            text = (
                "🏛 <b>\"PIRAMIDA\" O‘QUV MARKAZI</b>\n\n"
                f"Hurmatli o‘quvchi, <b>{student_name}</b>!\n"
                f"{msg_line}\n\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"📚 <b>Fan:</b> {subject_name}\n"
                f"💰 <b>Summa:</b> {amount_val:,} so‘m\n"
                f"📅 <b>Muddat:</b> {due_str}\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                f"{action_line}"
            )

            try:
                await bot.send_message(
                    chat_id=int(user_id),
                    text=text,
                    reply_markup=reminder_payment_keyboard(admin_user),
                    parse_mode="HTML"
                )
            except Exception as error:
                print(f"Xabar yuborilmadi (ID: {user_id}): {error}")


def start_scheduler(bot):
    # Har kuni ertalab soat 09:00 da avtomatik eslatma tekshirish
    scheduler.add_job(
        check_payments,
        trigger="cron",
        hour=9,
        minute=0,
        args=[bot],
        id="payment_reminders",
        replace_existing=True,
        misfire_grace_time=3600
    )

    # Bot ishga tushganda ham 15 soniyadan so'ng 1 marta tekshirib qo'yish
    scheduler.add_job(
        check_payments,
        trigger="date",
        run_date=datetime.now(TZ) + timedelta(seconds=15),
        args=[bot],
        id="payment_check_startup",
        replace_existing=True
    )

    scheduler.start()
    print("✅ Avtomatik oylik eslatmalar jadvali ishga tushdi!")