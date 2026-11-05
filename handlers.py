import os
import re
import html
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, ADMIN_PASSWORD
from database import (
    add_user,
    get_users_count,
    get_active_users,
    get_today_users,
    get_all_user_ids,
    add_student,
    get_student,
    get_students,
    update_student,
    delete_student,
    get_pending_payment_students,
    get_debtor_students,
    get_students_stats,
    get_subjects,
    get_subject,
    add_subject,
    update_subject,
    delete_subject,
    get_setting,
    set_setting,
    advance_payment_date,
    get_authenticated_admins,
    add_authenticated_admin,
    remove_authenticated_admin
)
from keyboards import (
    main_menu,
    contact_keyboard,
    days_selection_keyboard,
    subjects_selection_inline,
    payment_keyboard,
    payment_action_keyboard,
    payment_decision_keyboard,
    cash_payment_confirm_keyboard,
    cancel_keyboard,
    map_inline_keyboard,
    contact_inline_keyboard,
    subject_detail_keyboard,
    admin_menu,
    admin_students_action_keyboard,
    admin_delete_students_keyboard,
    admin_confirm_delete_student_keyboard,
    subjects_keyboard,
    admin_subjects_keyboard,
    settings_keyboard,
    get_subject_icon,
    peramida_bot_inline_keyboard
)

router = Router()

authenticated_admins = set()


async def sync_admins():
    try:
        db_admins = await get_authenticated_admins()
        authenticated_admins.update(db_admins)
    except Exception:
        pass


def is_admin(user_id):
    if user_id in authenticated_admins:
        return True
    return False


def get_admin_targets(sender_id=None):
    targets = set(authenticated_admins)
    if ADMIN_ID:
        try:
            targets.add(int(ADMIN_ID))
        except Exception:
            pass
    if sender_id and len(targets) > 1 and sender_id in targets:
        targets.discard(sender_id)
    return list(targets)


# =========================================================
# FSM STATES
# =========================================================

class Registration(StatesGroup):
    name = State()
    phone = State()
    subject = State()
    teacher = State()
    days = State()
    time = State()
    payment_day = State()
    amount = State()


class PaymentState(StatesGroup):
    receipt = State()


class AdminLoginState(StatesGroup):
    password = State()


class AddSubjectState(StatesGroup):
    name = State()
    teacher = State()
    days = State()
    time = State()
    price = State()
    small_group = State()


class EditSubjectState(StatesGroup):
    name = State()
    teacher = State()
    days = State()
    time = State()
    price = State()
    small_group = State()


class BroadcastState(StatesGroup):
    message = State()


class SettingState(StatesGroup):
    value = State()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def format_subject_card(target):
    _, name, teacher, time, small_group, days, price = target
    icon = get_subject_icon(name)

    text = f"""
╭───────────────────────
│ {icon} <b>{name.upper()} KURSI</b>
╰───────────────────────

👨‍🏫 <b>Ustoz:</b> {teacher}
"""
    if days:
        text += f"📅 <b>Dars kunlari:</b> {days}\n"
    text += f"🕐 <b>Dars vaqti:</b> {time}\n"
    if price:
        text += f"💰 <b>Kurs narxi:</b> {price}\n"
    if small_group:
        text += f"👥 <b>Qo'shimcha guruh:</b> {small_group}\n"

    text += """
───────────────────────
💡 <i>Kursga yozilish yoki ma'lumot olish uchun quyidagi tugmalardan foydalaning!</i>
"""
    return text


def clean_query(text: str) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    for e in ["🇺🇿", "🇷🇺", "🇬🇧", "📐", "🧪", "🧬", "⚡", "🏛️", "🏛", "⚖️", "⚖", "💻", "🌍", "📜", "📚", "📖", "⭐", "🔹", "🔸"]:
        t = t.replace(e, "")
    return t.replace("‘", "'").replace("’", "'").replace("`", "'").strip()


# =========================================================
# CANCEL HANDLER
# =========================================================

@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    student = await get_student(message.from_user.id)
    if student:
        await message.answer("❌ Jarayon bekor qilindi.", reply_markup=main_menu())
    else:
        await message.answer(
            "❌ Jarayon bekor qilindi. Boshlash uchun /start buyrug‘ini bosing.",
            reply_markup=cancel_keyboard()
        )


# =========================================================
# START & REGISTRATION
# =========================================================

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await add_user(user.id, user.username, user.first_name)

    student = await get_student(user.id)

    if student:
        await message.answer(
            f"Assalomu alaykum, <b>{html.escape(student['name'])}</b>! 👋\n\n"
            f"🏛 <b>«PIRAMIDA» O'QUV MARKAZI</b> rasmiy botiga xush kelibsiz!\n\n"
            "Kerakli bo‘limni tanlang 👇",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
        return

    # Ro'yxatdan o'tmagan bo'lsa - ro'yxatdan o'tkazish
    await message.answer(
        "🎓 <b>PIRAMIDA O‘QUV MARKAZI</b>\n\n"
        "Assalomu alaykum! Markazimiz botidan to‘liq foydalanish va oylik dars hamda "
        "to‘lovlaringizni nazorat qilish uchun ro‘yxatdan o‘ting.\n\n"
        "1️⃣ <b>Ism va familiyangizni kiriting:</b>\n"
        "<i>(Masalan: Aliyev Ali)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.name)


@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3 or len(name) > 100:
        await message.answer("Iltimos, ism va familiyangizni to‘g‘ri kiriting (kamida 3 ta harf).")
        return

    await state.update_data(name=name)
    await message.answer(
        "2️⃣ <b>Telefon raqamingizni yuboring:</b>\n"
        "Pastdagi tugmani bosing yoki raqamingizni yozib yuboring (+998901234567):",
        reply_markup=contact_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.phone)


@router.message(Registration.phone, F.contact)
async def reg_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    subjects = await get_subjects()

    await message.answer(
        "3️⃣ <b>Qaysi fandan tahsil olasiz?</b>\n"
        "Quyidagi fanlardan birini tanlang yoki nomini yozing:",
        reply_markup=subjects_selection_inline(subjects),
        parse_mode="HTML"
    )
    await state.set_state(Registration.subject)


@router.message(Registration.phone)
async def reg_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 7:
        await message.answer("Iltimos, telefon raqamingizni to‘g‘ri kiriting yoki pastdagi tugmani bosing.")
        return

    await state.update_data(phone=phone)
    subjects = await get_subjects()

    await message.answer(
        "3️⃣ <b>Qaysi fandan tahsil olasiz?</b>\n"
        "Quyidagi fanlardan birini tanlang yoki nomini yozing:",
        reply_markup=subjects_selection_inline(subjects),
        parse_mode="HTML"
    )
    await state.set_state(Registration.subject)


@router.callback_query(Registration.subject, F.data.startswith("reg_sub:"))
async def reg_sub_callback(callback: CallbackQuery, state: FSMContext):
    subject_id = int(callback.data.split(":")[1])
    sub = await get_subject(subject_id)

    if sub:
        await state.update_data(
            subject=sub[1],
            teacher=sub[2],
            days=sub[5] or "Seshanba, Payshanba, Shanba",
            time=sub[3] or "16:00 - 18:00"
        )
        await callback.message.answer(
            f"✅ Tanlangan fan: <b>{sub[1]}</b>\n"
            f"👨‍🏫 Ustoz: <b>{sub[2]}</b>\n"
            f"📅 Kunlari: <b>{sub[5]}</b>\n"
            f"🕐 Vaqti: <b>{sub[3]}</b>\n\n"
            "7️⃣ <b>Oylik to‘lovingiz har oyning nechanchi sanasida?</b>\n"
            "<i>(1 dan 31 gacha bo‘lgan kun raqamini yozing, masalan: 5 yoki 15)</i>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(Registration.payment_day)
    else:
        await callback.message.answer("Fan nomini yozib yuboring:")
    await callback.answer()


@router.message(Registration.subject)
async def reg_sub_text(message: Message, state: FSMContext):
    await state.update_data(subject=message.text.strip())
    await message.answer(
        "4️⃣ <b>Ustozingizning ismi-familiyasini yozing:</b>\n"
        "<i>(Masalan: Tursunboyev Haitboy)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.teacher)


@router.message(Registration.teacher)
async def reg_teacher(message: Message, state: FSMContext):
    await state.update_data(teacher=message.text.strip())
    await message.answer(
        "5️⃣ <b>Dars kunlaringizni tanlang yoki yozing:</b>",
        reply_markup=days_selection_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.days)


@router.message(Registration.days)
async def reg_days(message: Message, state: FSMContext):
    await state.update_data(days=message.text.strip())
    await message.answer(
        "6️⃣ <b>Darsingiz soat nechida boshlanadi?</b>\n"
        "<i>(Masalan: 14:00 yoki 16:00 - 18:00)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.time)


@router.message(Registration.time)
async def reg_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text.strip())
    await message.answer(
        "7️⃣ <b>Oylik to‘lovingiz har oyning nechanchi sanasida?</b>\n"
        "<i>(1 dan 31 gacha bo‘lgan kun raqamini yozing, masalan: 5 yoki 15)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.payment_day)


@router.message(Registration.payment_day)
async def reg_payment_day(message: Message, state: FSMContext):
    val = message.text.strip()
    if not val.isdigit() or not (1 <= int(val) <= 31):
        await message.answer("Iltimos, 1 dan 31 gacha bo‘lgan son kiriting (masalan: 5).")
        return

    await state.update_data(payment_day=int(val))
    await message.answer(
        "8️⃣ <b>Oylik to‘lov miqdorini kiriting (so‘mda):</b>\n"
        "<i>(Masalan: 350000)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.amount)


@router.message(Registration.amount)
async def reg_amount(message: Message, state: FSMContext):
    val = message.text.strip().replace(" ", "").replace(",", "").replace(".", "")
    if not val.isdigit() or int(val) < 1000:
        await message.answer("Iltimos, to‘lov miqdorini to‘g‘ri kiriting (masalan: 350000).")
        return

    data = await state.get_data()
    amount = int(val)

    student_data = {
        "name": data["name"],
        "phone": data["phone"],
        "subject": data["subject"],
        "teacher": data.get("teacher", "Markaz ustozi"),
        "days": data.get("days", "Seshanba, Payshanba, Shanba"),
        "time": data.get("time", "16:00 - 18:00"),
        "payment_day": data["payment_day"],
        "amount": amount,
        "payment_status": "unpaid",
        "pending_payment": False,
        "last_paid": None,
        "registered_at": datetime.now().isoformat(),
        "sent_reminders": []
    }

    await add_student(message.from_user.id, student_data)
    await state.clear()

    await message.answer(
        "🎉 <b>RO‘YXATDAN MUVAFFAQIYATLI O‘TDINGIZ!</b>\n\n"
        f"👤 <b>Ism:</b> {html.escape(student_data['name'])}\n"
        f"📱 <b>Telefon:</b> {html.escape(student_data['phone'])}\n"
        f"📚 <b>Fan:</b> {html.escape(student_data['subject'])}\n"
        f"👨‍🏫 <b>Ustoz:</b> {html.escape(student_data['teacher'])}\n"
        f"📅 <b>Dars kunlari:</b> {html.escape(student_data['days'])}\n"
        f"🕒 <b>Dars vaqti:</b> {html.escape(student_data['time'])}\n"
        f"📆 <b>To‘lov sanasi:</b> Har oyning {student_data['payment_day']}-sanasi\n"
        f"💰 <b>Oylik to‘lov:</b> {amount:,} so‘m\n\n"
        "Endi bot orqali dars jadvalingizni kuzatishingiz, to‘lov holatini tekshirishingiz va har oy avtomatik eslatmalar olishingiz mumkin! 🎓",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================================================
# USER PROFILE & SCHEDULE
# =========================================================

@router.message(F.text == "👤 Mening profilim")
async def profile_handler(message: Message):
    student = await get_student(message.from_user.id)
    if not student:
        await message.answer("Siz hali ro‘yxatdan o‘tmabsiz. /start buyrug‘ini bosing.")
        return

    status = (
        "🟢 To‘langan" if student["payment_status"] == "paid"
        else "⏳ Tasdiqlanishi kutilmoqda" if student.get("pending_payment")
        else "🔴 To‘lanmagan"
    )

    next_date_val = student.get("next_payment_date") or f"Har oyning {student['payment_day']}-kuni"

    username_val = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"

    await message.answer(
        f"👤 <b>SIZNING PROFILINGIZ</b>\n\n"
        f"Ism: <b>{html.escape(student['name'])}</b>\n"
        f"Telegram: <b>{username_val}</b>\n"
        f"Telefon: <b>{html.escape(student['phone'])}</b>\n"
        f"Fan: <b>{html.escape(student['subject'])}</b>\n"
        f"Ustoz: <b>{html.escape(student['teacher'])}</b>\n"
        f"Dars kunlari: <b>{html.escape(student['days'])}</b>\n"
        f"Dars vaqti: <b>{html.escape(student['time'])}</b>\n"
        f"To‘lov kuni: <b>Har oyning {student['payment_day']}-sanasi</b>\n"
        f"📆 Keyingi to‘lov sanasi: <b>{next_date_val}</b>\n"
        f"Oylik to‘lov: <b>{student['amount']:,} so‘m</b>\n"
        f"To‘lov holati: <b>{status}</b>\n\n"
        f"🆔 Telegram ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )


@router.message(F.text.in_([
    "📚 Darslar haqida (@Peramidauzbot)",
    "📚 Darslar haqida",
    "📅 Dars jadvalim",
    "📚 Fanlar",
    "📚 Fanlarimiz",
    "👨‍🏫 O'qituvchilar",
    "/jadval",
    "/fanlar",
    "/ustozlar"
]))
async def redirect_to_peramida_bot(message: Message):
    await message.answer(
        "📚 <b>DARSLAR, FANLAR VA DARS JADVALI</b>\n\n"
        "Markazimizdagi barcha o‘quv fanlari, dars jadvali, ustozlar va kurslar haqida to‘liq ma’lumot olish uchun "
        "quyidagi tugma orqali maxsus botimizga o‘ting:\n\n"
        "👉 @Peramidauzbot",
        reply_markup=peramida_bot_inline_keyboard(),
        parse_mode="HTML"
    )


# =========================================================
# USER PAYMENTS & DONE
# =========================================================

@router.message(F.text.in_([
    "💳 To‘lov qilish",
    "✅ To‘lov qildim",
    "To'lov qildim",
    "To‘lov qildim",
    "Tolov qildim",
    "Naqd to'lov qildim",
    "Naqd to‘lov qildim",
    "💰 To‘lovlarim",
    "/tolov",
    "/pay"
]))
async def my_payments_handler(message: Message):
    student = await get_student(message.from_user.id)
    if not student:
        await message.answer("Siz hali ro‘yxatdan o‘tmabsiz. /start buyrug‘ini bosing.")
        return

    card_number = await get_setting("card_number") or "8600 5304 1234 5678"
    card_holder = await get_setting("card_holder") or "Isroilova Ozoda"
    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"

    status = (
        "🟢 To‘langan" if student["payment_status"] == "paid"
        else "⏳ Administrator tasdiqlashini kutmoqda" if student.get("pending_payment")
        else "🔴 To‘lanmagan"
    )

    next_date_val = student.get("next_payment_date") or f"Har oyning {student['payment_day']}-kuni"

    last_paid_text = "Mavjud emas"
    if student.get("last_paid"):
        try:
            lp_date = datetime.fromisoformat(student["last_paid"]).strftime("%d.%m.%Y %H:%M")
            last_paid_text = lp_date
        except Exception:
            last_paid_text = student["last_paid"]

    text = f"""
💳 <b>OYLIK TO‘LOV MA’LUMOTLARI VA REKVIZITLAR</b>

👤 O‘quvchi: <b>{html.escape(student['name'])}</b>
📚 Fan: <b>{html.escape(student['subject'])}</b>
💵 Oylik to‘lov miqdori: <b>{student['amount']:,} so‘m</b>
📆 Keyingi to‘lov sanasi: <b>{next_date_val}</b>
Holati: <b>{status}</b>
Oxirgi to‘lov: <b>{last_paid_text}</b>

───────────────────────
🏦 <b>TO‘LOV QILISH UCHUN KARTA:</b>
💳 Karta raqami: <code>{card_number}</code>
<i>(Nusxalash uchun raqam ustiga bir marta bosing 👆)</i>
👤 Karta egasi: <b>{card_holder}</b>
✈️ Administrator: <b>{admin_user}</b>

💡 <b>To‘lov qilish tartibi:</b>
1. <b>Payme yoki Click orqali:</b> Karta raqamiga to‘lov qilib, pastdagi <b>«💳 Payme / Karta (📸 Chek yuborish)»</b> tugmasi orqali chek fotosuratini yuboring.
2. <b>Naqd pul orqali:</b> O‘quv markazida to‘lov qilgan bo‘lsangiz, pastdagi <b>«💵 Naqd to‘lov qildim (✅ Tasdiqlash)»</b> tugmasini bosing.

Administrator to‘lovni tasdiqlagach, to‘lov sanangiz avtomatik keyingi oyga uzaytiriladi!
"""

    is_paid = (student["payment_status"] == "paid")
    is_pending = bool(student.get("pending_payment"))

    reply_markup = payment_action_keyboard(admin_user, is_pending=is_pending, is_paid=is_paid)

    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


@router.callback_query(F.data == "pay_card")
async def pay_card_callback(callback: CallbackQuery):
    student = await get_student(callback.from_user.id)
    if not student:
        await callback.answer("O‘quvchi topilmadi.", show_alert=True)
        return

    card_number = await get_setting("card_number") or "8600 5304 1234 5678"
    card_holder = await get_setting("card_holder") or "Isroilova Ozoda"
    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"
    next_date_val = student.get("next_payment_date") or f"Har oyning {student['payment_day']}-kuni"

    text = f"""
💳 <b>KARTA ORQALI TO‘LOV REKVIZITLARI</b>

👤 O‘quvchi: <b>{html.escape(student['name'])}</b>
📚 Fan: <b>{html.escape(student['subject'])}</b>
💰 To‘lov miqdori: <b>{student['amount']:,} so‘m</b>
📆 Keyingi to‘lov sanasi: <b>{next_date_val}</b>

───────────────────────
🏦 <b>TO‘LOV UCHUN KARTA:</b>
💳 Karta raqami: <code>{card_number}</code>
<i>(Nusxalash uchun raqam ustiga bosing 👆)</i>
👤 Karta egasi: <b>{card_holder}</b>
✈️ Administrator: <b>{admin_user}</b>

To‘lovni amalga oshirgach, chek fotosuratini (skrinshotini) yuborish uchun pastdagi tugmani bosing 👇
"""
    is_paid = (student["payment_status"] == "paid")
    is_pending = bool(student.get("pending_payment"))
    await callback.message.answer(
        text,
        reply_markup=payment_action_keyboard(admin_user, is_pending=is_pending, is_paid=is_paid),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "send_receipt")
async def send_receipt_start(callback: CallbackQuery, state: FSMContext):
    student = await get_student(callback.from_user.id)
    if not student:
        await callback.answer("O‘quvchi topilmadi.", show_alert=True)
        return

    await state.set_state(PaymentState.receipt)
    await callback.message.answer(
        "📸 <b>TO‘LOV CHEKINI (SKRINSHOT) YUBORISH</b>\n\n"
        "Click, Payme yoki bank ilovasidagi to‘lov kvitansiyasining skrinshotini (fotosuratini) shu yerga rasm ko‘rinishida yuboring 👇",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PaymentState.receipt, F.photo)
@router.message(F.photo)
async def process_receipt_photo(message: Message, state: FSMContext):
    curr_state = await state.get_state()
    if curr_state is not None and curr_state != PaymentState.receipt.state:
        return

    user_id = message.from_user.id
    student = await get_student(user_id)
    if not student:
        await state.clear()
        await message.answer("Siz hali ro‘yxatdan o‘tmabsiz. /start buyrug‘ini bosing.")
        return

    await update_student(user_id, pending_payment=True)
    await state.clear()

    photo_id = message.photo[-1].file_id
    next_date_val = student.get("next_payment_date") or f"Har oyning {student['payment_day']}-kuni"

    caption = (
        f"🔔 <b>YANGI TO‘LOV CHEKI (SKRINSHOT) YUBORILDI!</b>\n\n"
        f"👤 O‘quvchi: <b>{html.escape(student['name'])}</b>\n"
        f"📱 Telefon: <b>{html.escape(student['phone'])}</b>\n"
        f"📚 Fan: <b>{html.escape(student['subject'])}</b>\n"
        f"💰 Oylik to‘lov: <b>{student['amount']:,} so‘m</b>\n"
        f"📆 Hozirgi to‘lov sanasi: {next_date_val}\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n\n"
        "To‘lov chekini tekshirib, to‘lovni tasdiqlaysizmi?"
    )

    await sync_admins()
    admin_targets = get_admin_targets(sender_id=user_id)

    for adm_id in admin_targets:
        try:
            await message.bot.send_photo(
                chat_id=adm_id,
                photo=photo_id,
                caption=caption,
                reply_markup=payment_decision_keyboard(user_id),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Adminga chek yuborishda xatolik ({adm_id}): {e}")

    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"
    await message.answer(
        "⏳ <b>To‘lov chekingiz muvaffaqiyatli qabul qilindi va administratorga yuborildi!</b>\n\n"
        "Administrator chekni tekshirib tasdiqlagach, to‘lov sanangiz avtomatik keyingi oyga uzaytiriladi va sizga xabar keladi. Rahmat!\n\n"
        f"Savollar bo‘lsa administratorga murojaat qilishingiz mumkin: {admin_user}",
        reply_markup=payment_action_keyboard(admin_user, is_pending=True),
        parse_mode="HTML"
    )


@router.message(PaymentState.receipt, F.text)
async def process_receipt_text(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("To‘lov bekor qilindi.", reply_markup=main_menu())
        return

    user_id = message.from_user.id
    student = await get_student(user_id)
    if not student:
        await state.clear()
        await message.answer("O‘quvchi topilmadi. /start buyrug‘ini bosing.")
        return

    await update_student(user_id, pending_payment=True)
    await state.clear()

    next_date_val = student.get("next_payment_date") or f"Har oyning {student['payment_day']}-kuni"

    caption = (
        f"🔔 <b>YANGI TO‘LOV XABARI YUBORILDI!</b>\n\n"
        f"👤 O‘quvchi: <b>{html.escape(student['name'])}</b>\n"
        f"📱 Telefon: <b>{html.escape(student['phone'])}</b>\n"
        f"📚 Fan: <b>{html.escape(student['subject'])}</b>\n"
        f"💰 To‘lov miqdori: <b>{student['amount']:,} so‘m</b>\n"
        f"📆 To‘lov sanasi: {next_date_val}\n"
        f"📝 O‘quvchi izohi: <i>{html.escape(message.text)}</i>\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n\n"
        "To‘lovni tasdiqlaysizmi?"
    )

    await sync_admins()
    admin_targets = get_admin_targets(sender_id=user_id)

    for adm_id in admin_targets:
        try:
            await message.bot.send_message(
                chat_id=adm_id,
                text=caption,
                reply_markup=payment_decision_keyboard(user_id),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Adminga to‘lov xabari yuborishda xatolik ({adm_id}): {e}")

    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"
    await message.answer(
        "⏳ <b>To‘lov haqidagi xabaringiz administratorga yuborildi!</b>\n\n"
        "Administrator tekshirib tasdiqlagach, to‘lov sanangiz keyingi oyga uzaytiriladi va sizga xabar keladi. Rahmat!\n\n"
        f"Savollar bo‘lsa administratorga murojaat qilishingiz mumkin: {admin_user}",
        reply_markup=payment_action_keyboard(admin_user, is_pending=True),
        parse_mode="HTML"
    )


@router.callback_query(F.data.in_(["pay_cash", "payment_done"]))
async def pay_cash_start(callback: CallbackQuery):
    student = await get_student(callback.from_user.id)
    if not student:
        await callback.answer("O‘quvchi topilmadi.", show_alert=True)
        return

    if student.get("pending_payment"):
        await callback.answer("To‘lov so‘rovingiz allaqachon yuborilgan. Tasdiqlanishini kuting.", show_alert=True)
        return

    text = f"""
💵 <b>NAQD TO‘LOVNI TASDIQLASH</b>

👤 O‘quvchi: <b>{html.escape(student['name'])}</b>
📚 Fan: <b>{html.escape(student['subject'])}</b>
💰 Oylik to‘lov miqdori: <b>{student['amount']:,} so‘m</b>

Siz ushbu to‘lovni o‘quv markazida <b>naqd pul</b> ko‘rinishida to‘ladingizmi?
Tasdiqlash tugmasini bossangiz, administratorga tasdiqlash uchun so‘rov yuboriladi 👇
"""
    await callback.message.answer(
        text,
        reply_markup=cash_payment_confirm_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_cash_done")
async def cancel_cash_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer("Bekor qilindi.")


@router.callback_query(F.data == "confirm_cash_done")
async def confirm_cash_done_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    student = await get_student(user_id)
    if not student:
        await callback.answer("O‘quvchi topilmadi.", show_alert=True)
        return

    if student.get("pending_payment"):
        await callback.answer("To‘lov so‘rovingiz allaqachon yuborilgan. Tasdiqlanishini kuting.", show_alert=True)
        return

    await update_student(user_id, pending_payment=True)

    next_date_val = student.get("next_payment_date") or f"Har oyning {student['payment_day']}-kuni"

    caption = (
        f"🔔 <b>YANGI TO‘LOV SO‘ROVI (NAQD PUL)!</b>\n\n"
        f"👤 O‘quvchi: <b>{html.escape(student['name'])}</b>\n"
        f"📱 Telefon: <b>{html.escape(student['phone'])}</b>\n"
        f"📚 Fan: <b>{html.escape(student['subject'])}</b>\n"
        f"💰 To‘lov miqdori: <b>{student['amount']:,} so‘m</b>\n"
        f"💵 To‘lov usuli: <b>Naqd pul (Markazda)</b>\n"
        f"📆 Hozirgi to‘lov sanasi: {next_date_val}\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n\n"
        "O‘quvchi markazda naqd to‘lov qilganini bildirdi. To‘lovni tasdiqlaysizmi?"
    )

    await sync_admins()
    admin_targets = get_admin_targets(sender_id=user_id)

    for adm_id in admin_targets:
        try:
            await callback.bot.send_message(
                chat_id=adm_id,
                text=caption,
                reply_markup=payment_decision_keyboard(user_id),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Adminga naqd to‘lov so‘rovi yuborishda xatolik ({adm_id}): {e}")

    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "⏳ <b>Naqd to‘lov haqidagi so‘rovingiz administratorga yuborildi!</b>\n\n"
        "Administrator markazda to‘lov qabul qilinganini tekshirib tasdiqlagach, to‘lov sanangiz keyingi oyga uzaytiriladi va sizga xabar keladi. Rahmat!\n\n"
        f"Savollar bo‘lsa administratorga murojaat qilishingiz mumkin: {admin_user}",
        reply_markup=payment_action_keyboard(admin_user, is_pending=True),
        parse_mode="HTML"
    )
    await callback.answer("So‘rovingiz qabul qilindi!")


@router.message(F.text == "🔔 Eslatmalar")
async def reminders_info_handler(message: Message):
    student = await get_student(message.from_user.id)
    p_day = student["payment_day"] if student else "belgilangan"

    await message.answer(
        "🔔 <b>AVTOMATIK OYLIK ESLATMALAR TIZIMI</b>\n\n"
        "«Piramida» o‘quv markazi boti sizga har oy avtomatik ravishda eslatma yuborib turadi:\n\n"
        f"1️⃣ <b>To‘lovdan 3 kun oldin:</b> Tayyorgarlik eslatmasi\n"
        f"2️⃣ <b>To‘lov kuni (har oyning {p_day}-sanasi):</b> To‘lov kuni eslatmasi\n"
        f"3️⃣ <b>Muddat o‘tganidan 2 kun keyin:</b> Qarzdorlik eslatmasi\n\n"
        "To‘lovni amalga oshirgach, botdagi <b>«✅ To‘lov qildim»</b> tugmasi orqali xabar yuborishingiz mumkin.",
        parse_mode="HTML"
    )


# =========================================================
# USER SHOWCASE (FANLAR, USTOZLAR, MANZIL, HAQIDA, BOG'LANISH)
# =========================================================



@router.message(F.text.in_(["📍 Manzil", "/manzil"]))
async def address_handler(message: Message):
    address = await get_setting("address") or "Piramida O'quv Markazi"
    map_url = await get_setting("map_url") or "https://maps.app.goo.gl/orwFAVu6N3APkD216"

    text = (
        f"📍 <b>«PIRAMIDA» O'QUV MARKAZI MANZILI</b>\n\n"
        f"🏢 <b>Mo'ljal:</b> {address}\n"
        f"📸 Yuqoridagi fotosuratda markazimiz binosi ko'rsatilgan.\n\n"
        f"Xaritada ko'rish va yo'nalish olish uchun quyidagi tugmani bosing 👇"
    )

    photo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image.png")
    reply_markup = map_inline_keyboard(map_url) if map_url else None

    if os.path.exists(photo_path):
        await message.answer_photo(
            photo=FSInputFile(photo_path),
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


@router.message(F.text.in_(["ℹ️ Markaz haqida", "/about"]))
async def about_handler(message: Message):
    phone = await get_setting("phone") or "+998-97-152-84-00"
    admin_name = await get_setting("admin_name") or "Isroilova Ozoda"
    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"
    address = await get_setting("address") or "Piramida O'quv Markazi"

    text = f"""
🎓 <b>«PIRAMIDA» O'QUV MARKAZI</b>

🏛 <b>Markaz haqida:</b>
«Piramida» o'quv markazi — abituriyentlar va o'quvchilarni oliy ta'lim muassasalariga (OTM) kirishga, milliy hamda xalqaro sertifikatlarga tayyorlovchi zamonaviy o'quv maskanidir!

✨ <b>Bizning afzalliklarimiz:</b>
• 👨‍🏫 Yuqori malakali va tajribali ustozlar
• 👥 Kichik guruhlarda sifatli ta'lim
• 📊 Haftalik sinov testlari va o'zlashtirish nazorati
• 🏢 Qulay, shinam va zamonaviy dars xonalari
• 🎯 OTM ga kirishda kafolatlangan yuqori natijalar

📚 <b>Darslar va fanlar haqida to‘liq ma’lumot:</b>
👉 @Peramidauzbot

───────────────────────
🏢 <b>Manzil:</b> {address}
👩‍💼 <b>Admin:</b> {admin_name}
📞 <b>Telefon:</b> <code>{phone}</code>
✈️ <b>Telegram:</b> {admin_user}
"""
    await message.answer(
        text,
        reply_markup=contact_inline_keyboard(phone=phone, username=admin_user),
        parse_mode="HTML"
    )


@router.message(F.text.in_(["📞 Bog'lanish", "/contact"]))
async def contact_handler(message: Message):
    phone = await get_setting("phone") or "+998-97-152-84-00"
    address = await get_setting("address") or "Piramida O'quv Markazi"
    admin_name = await get_setting("admin_name") or "Isroilova Ozoda"
    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"

    text = f"""
📞 <b>BOG'LANISH VA ALOQA</b>

Savollaringiz yoki kurslarga yozilish bo‘yicha quyidagi vositalar orqali bog‘lanishingiz mumkin:

👩‍💼 <b>Administrator:</b> {admin_name}
📱 <b>Telefon:</b> <code>{phone}</code>
✈️ <b>Telegram:</b> {admin_user}
🏢 <b>Manzilimiz:</b> {address}
⏰ <b>Ish vaqti:</b> Har kuni 08:00 dan 20:00 gacha
"""
    await message.answer(
        text,
        reply_markup=contact_inline_keyboard(phone=phone, username=admin_user),
        parse_mode="HTML"
    )


# =========================================================
# ADMIN LOGIN & AUTHENTICATION
# =========================================================

@router.message(F.text == "👑 Admin panel")
@router.message(Command("admin"))
async def admin_panel_handler(message: Message, state: FSMContext):
    await state.set_state(AdminLoginState.password)
    await message.answer(
        "🔐 <b>ADMIN PANELGA KIRISH</b>\n\n"
        "Iltimos, administrator parolini kiriting:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdminLoginState.password)
async def check_admin_password(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Kirish bekor qilindi.", reply_markup=main_menu())
        return

    # Parol tekshiruvi: 1234567890
    entered_password = message.text.strip()
    if entered_password == "1234567890" or (ADMIN_PASSWORD and entered_password == str(ADMIN_PASSWORD).strip()):
        authenticated_admins.add(message.from_user.id)
        await state.clear()
        await message.answer(
            "✅ <b>PAROL TO‘G‘RI!</b>\n\n"
            "👑 <b>Siz administrator sifatida muvaffaqiyatli tizimga kirdingiz!</b>\n\n"
            "Kerakli bo‘limni tanlang 👇",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>Parol noto‘g‘ri!</b>\n\n"
            "Iltimos, administrator parolini qaytadan kiriting yoki <b>❌ Bekor qilish</b> tugmasini bosing:",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )


@router.message(F.text == "🚪 Chiqish")
async def admin_logout(message: Message):
    authenticated_admins.discard(message.from_user.id)
    await remove_authenticated_admin(message.from_user.id)
    await message.answer("🔒 Admin panelidan chiqildi.", reply_markup=main_menu())


@router.message(F.text.in_(["⬅️ Asosiy menyu", "🏠 Asosiy menyu"]))
async def back_to_main_menu(message: Message, state: FSMContext = None):
    if state:
        await state.clear()
    authenticated_admins.discard(message.from_user.id)
    await remove_authenticated_admin(message.from_user.id)
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu())


# =========================================================
# ADMIN: STUDENTS MANAGEMENT
# =========================================================

@router.message(F.text == "👨‍🎓 O‘quvchilar")
async def admin_students_list(message: Message):
    if not is_admin(message.from_user.id):
        return

    students = await get_students()
    if not students:
        await message.answer("Hozircha ro‘yxatdan o‘tgan o‘quvchilar yo‘q.")
        return

    text = f"👨‍🎓 <b>JAMI O‘QUVCHILAR ({len(students)} nafar):</b>\n\n"
    for idx, (uid, s) in enumerate(students.items(), 1):
        status_icon = "🟢" if s["payment_status"] == "paid" else "🔴"
        text += (
            f"{idx}. {status_icon} <b>{html.escape(s['name'])}</b>\n"
            f"   📱 {s['phone']} | 📚 {s['subject']}\n"
            f"   💰 {s['amount']:,} so'm | 📆 Har oyning {s['payment_day']}-kuni\n"
            f"   🆔 <code>{uid}</code>\n\n"
        )
        if len(text) > 3500:
            await message.answer(text, parse_mode="HTML")
            text = ""

    if text:
        await message.answer(text, reply_markup=admin_students_action_keyboard(), parse_mode="HTML")


@router.message(F.text.in_(["🗑 O‘quvchini o‘chirish", "O‘quvchini o‘chirish"]))
async def admin_delete_student_msg(message: Message):
    if not (is_admin(message.from_user.id) or (ADMIN_ID and str(message.from_user.id) == str(ADMIN_ID))):
        return

    students = await get_students()
    if not students:
        await message.answer("Markazda ro‘yxatdan o‘tgan o‘quvchilar mavjud emas.")
        return

    text = (
        "🗑 <b>O‘QUVCHINI O‘CHIRISH BO‘LIMI</b>\n\n"
        "O‘quvchi o‘quv markazida boshqa o‘qimasa, uni tizimdan o‘chirish uchun quyidagi ro‘yxatdan tanlang 👇"
    )
    await message.answer(text, reply_markup=admin_delete_students_keyboard(students), parse_mode="HTML")


@router.callback_query(F.data == "admin_open_delete_students")
async def admin_delete_student_callback_open(callback: CallbackQuery):
    if not (is_admin(callback.from_user.id) or (ADMIN_ID and str(callback.from_user.id) == str(ADMIN_ID))):
        await callback.answer("Siz administrator emassiz!", show_alert=True)
        return

    students = await get_students()
    if not students:
        await callback.answer("Markazda ro‘yxatdan o‘tgan o‘quvchilar mavjud emas.", show_alert=True)
        return

    text = (
        "🗑 <b>O‘QUVCHINI O‘CHIRISH BO‘LIMI</b>\n\n"
        "O‘quvchi o‘quv markazida boshqa o‘qimasa, uni tizimdan o‘chirish uchun quyidagi ro‘yxatdan tanlang 👇"
    )
    await callback.message.answer(text, reply_markup=admin_delete_students_keyboard(students), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("del_stud:"))
async def select_student_to_delete(callback: CallbackQuery):
    if not (is_admin(callback.from_user.id) or (ADMIN_ID and str(callback.from_user.id) == str(ADMIN_ID))):
        await callback.answer("Siz administrator emassiz!", show_alert=True)
        return

    target_id = int(callback.data.split(":")[1])
    student = await get_student(target_id)
    if not student:
        await callback.answer("O‘quvchi topilmadi yoki allaqachon o‘chirilgan!", show_alert=True)
        return

    status = "🟢 To‘langan" if student.get("payment_status") == "paid" else "🔴 To‘lanmagan"
    next_date_val = student.get("next_payment_date") or f"Har oyning {student.get('payment_day', '')}-kuni"

    text = (
        "⚠️ <b>O‘QUVCHINI O‘CHIRISHNI TASDIQLASH</b>\n\n"
        f"👤 <b>Ism:</b> {html.escape(student.get('name', ''))}\n"
        f"📱 <b>Telefon:</b> {html.escape(student.get('phone', ''))}\n"
        f"📚 <b>Fan:</b> {html.escape(student.get('subject', ''))}\n"
        f"👨‍🏫 <b>Ustoz:</b> {html.escape(student.get('teacher', ''))}\n"
        f"💰 <b>Oylik to‘lov:</b> {student.get('amount', 0):,} so‘m\n"
        f"📆 <b>To‘lov kuni:</b> {next_date_val}\n"
        f"Holati: <b>{status}</b>\n"
        f"🆔 <b>Telegram ID:</b> <code>{target_id}</code>\n\n"
        "Haqiqatan ham ushbu o‘quvchini tizimdan butunlay o‘chirib tashlamoqchimisiz?\n\n"
        "<i>(U markazda boshqa o‘qimasa, uni o‘chirishingiz mumkin. O‘chirilgandan so‘ng unga avtomatik eslatmalar bormaydi).</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=admin_confirm_delete_student_keyboard(target_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_stud_conf:"))
async def confirm_delete_student_callback(callback: CallbackQuery):
    if not (is_admin(callback.from_user.id) or (ADMIN_ID and str(callback.from_user.id) == str(ADMIN_ID))):
        await callback.answer("Siz administrator emassiz!", show_alert=True)
        return

    target_id = int(callback.data.split(":")[1])
    student = await get_student(target_id)
    student_name = student.get("name", "O‘quvchi") if student else "O‘quvchi"

    await delete_student(target_id)

    await callback.message.edit_text(
        f"✅ <b>{html.escape(student_name)}</b> (ID: <code>{target_id}</code>) o‘quv markazi ro‘yxatidan muvaffaqiyatli o‘chirildi!\n\n"
        "Ushbu o‘quvchiga endi to‘lov eslatmalari bormaydi.",
        parse_mode="HTML"
    )
    await callback.answer("O‘quvchi o‘chirildi!", show_alert=True)


@router.callback_query(F.data == "del_stud_cancel")
async def cancel_delete_student_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer("Bekor qilindi.")


# =========================================================
# ADMIN: PENDING PAYMENTS (TASDIQLASH / RAD ETISH)
# =========================================================

@router.message(F.text == "💰 To‘lov kutilmoqda")
async def admin_pending_payments(message: Message):
    if not is_admin(message.from_user.id):
        return

    pending = await get_pending_payment_students()
    if not pending:
        await message.answer("🎉 Tasdiqlashni kutayotgan to‘lov so‘rovlari mavjud emas.")
        return

    await message.answer(f"🔔 <b>TASDIQLASHNI KUTAYOTGAN TO‘LOVLAR ({len(pending)} ta):</b>", parse_mode="HTML")

    for s in pending:
        text = (
            f"👤 O‘quvchi: <b>{html.escape(s['name'])}</b>\n"
            f"📱 Telefon: <b>{html.escape(s['phone'])}</b>\n"
            f"📚 Fan: <b>{html.escape(s['subject'])}</b>\n"
            f"👨‍🏫 Ustoz: <b>{html.escape(s['teacher'])}</b>\n"
            f"💰 To‘lov miqdori: <b>{s['amount']:,} so‘m</b>\n"
            f"📆 To‘lov kuni: Har oyning {s['payment_day']}-sanasi\n"
            f"🆔 ID: <code>{s['user_id']}</code>"
        )
        await message.answer(
            text,
            reply_markup=payment_decision_keyboard(s['user_id']),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("approve_"))
async def approve_payment_callback(callback: CallbackQuery):
    await sync_admins()
    if not (is_admin(callback.from_user.id) or (ADMIN_ID and str(callback.from_user.id) == str(ADMIN_ID))):
        await callback.answer(
            "❌ Siz administrator emassiz! Faqat administrator to‘lovni tasdiqlashi mumkin.",
            show_alert=True
        )
        return

    target_id = int(callback.data.replace("approve_", ""))
    student = await get_student(target_id)

    if not student:
        await callback.answer("O‘quvchi topilmadi.")
        return

    new_next_date = advance_payment_date(student["payment_day"], student.get("next_payment_date"))

    await update_student(
        target_id,
        pending_payment=False,
        payment_status="paid",
        last_paid=datetime.now().isoformat(),
        next_payment_date=new_next_date,
        sent_reminders=[]
    )

    try:
        await callback.bot.send_message(
            target_id,
            "🎉 <b>TO‘LOVINGIZ ADMINISTRATOR TOMONIDAN TASDIQLANDI!</b>\n\n"
            f"Hurmatli <b>{html.escape(student['name'])}</b>, oylik to‘lovingiz muvaffaqiyatli qabul qilindi.\n\n"
            f"📆 <b>Keyingi oylik to‘lov sanangiz:</b> <b>{new_next_date}</b>\n\n"
            "«Piramida» o‘quv markaziga bo‘lgan ishonchingiz uchun rahmat! 🎓",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"O'quvchiga tasdiq xabari yuborishda xatolik: {e}")

    admin_display = callback.from_user.first_name or "Admin"
    status_text = (
        f"✅ <b>{html.escape(student['name'])}</b> to‘lovi muvaffaqiyatli tasdiqlandi!\n"
        f"📆 Keyingi to‘lov sanasi: <b>{new_next_date}</b>\n"
        f"👤 Tasdiqladi: <b>{admin_display}</b>"
    )

    try:
        if callback.message.caption:
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n{status_text}",
                reply_markup=None,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                status_text,
                reply_markup=None,
                parse_mode="HTML"
            )
    except Exception:
        pass

    await callback.answer(f"Tasdiqlandi! Yangi sana: {new_next_date}", show_alert=True)


@router.callback_query(F.data.startswith("reject_"))
async def reject_payment_callback(callback: CallbackQuery):
    await sync_admins()
    if not (is_admin(callback.from_user.id) or (ADMIN_ID and str(callback.from_user.id) == str(ADMIN_ID))):
        await callback.answer(
            "❌ Siz administrator emassiz! Faqat administrator to‘lovni rad etishi mumkin.",
            show_alert=True
        )
        return

    target_id = int(callback.data.replace("reject_", ""))
    student = await get_student(target_id)

    if not student:
        await callback.answer("O‘quvchi topilmadi.")
        return

    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"
    await update_student(target_id, pending_payment=False)

    try:
        await callback.bot.send_message(
            target_id,
            "❌ <b>To‘lov so‘rovingiz tasdiqlanmadi.</b>\n\n"
            "Chek ma'lumotlarida noaniqlik mavjud bo‘lishi mumkin yoki mablag‘ yetib kelmagan.\n"
            f"Iltimos, administrator bilan bog‘laning: {admin_user}",
            reply_markup=payment_action_keyboard(admin_user),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"O'quvchiga rad etish xabari yuborishda xatolik: {e}")

    admin_display = callback.from_user.first_name or "Admin"
    status_text = (
        f"❌ <b>{html.escape(student['name'])}</b> to‘lov so‘rovi rad etildi.\n"
        f"👤 Rad etdi: <b>{admin_display}</b>"
    )

    try:
        if callback.message.caption:
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n{status_text}",
                reply_markup=None,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                status_text,
                reply_markup=None,
                parse_mode="HTML"
            )
    except Exception:
        pass

    await callback.answer("Rad etildi!")


# =========================================================
# ADMIN: DEBTORS & STATS
# =========================================================

@router.message(F.text == "⚠️ Qarzdorlar")
async def admin_debtors_list(message: Message):
    if not is_admin(message.from_user.id):
        return

    debtors = await get_debtor_students()
    if not debtors:
        await message.answer("🎉 Hozirda to‘lov qilmagan qarzdorlar mavjud emas!")
        return

    text = f"⚠️ <b>TO‘LOV QILMAGAN O‘QUVCHILAR ({len(debtors)} nafar):</b>\n\n"
    for idx, s in enumerate(debtors, 1):
        text += (
            f"{idx}. <b>{html.escape(s['name'])}</b>\n"
            f"   📱 Tel: {s['phone']} | 📚 Fan: {s['subject']}\n"
            f"   💰 Qarzdorlik: <b>{s['amount']:,} so'm</b>\n"
            f"   📆 To‘lov kuni: {s['payment_day']}-sana\n\n"
        )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📊 Statistika")
async def admin_stats_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    total_users = await get_users_count()
    active_users = await get_active_users()
    today_users = await get_today_users()
    total_students, paid_students, unpaid_students = await get_students_stats()

    text = f"""
╭───────────────────────
│ 📊 <b>«PIRAMIDA» BOT STATISTIKASI</b>
╰───────────────────────

👥 <b>Bot foydalanuvchilari:</b>
• Jami a'zolar: <b>{total_users}</b> nafar
• So'nggi 5 daqiqada faol: <b>{active_users}</b> nafar
• Bugun qo'shilganlar: <b>{today_users}</b> nafar

🎓 <b>O'quvchilar va To'lovlar:</b>
• Jami o'quvchilar: <b>{total_students}</b> nafar
• 🟢 To'lov qilganlar: <b>{paid_students}</b> nafar
• 🔴 Qarzdorlar: <b>{unpaid_students}</b> nafar
"""
    await message.answer(text, parse_mode="HTML")


# =========================================================
# ADMIN: BROADCAST
# =========================================================

@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(BroadcastState.message)
    await message.answer(
        "📢 <b>BARCHA FOYDALANUVCHILARGA XABAR YUBORISH</b>\n\n"
        "Yubormoqchi bo‘lgan xabaringizni yozing (matn, rasm yoki e'lon):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(BroadcastState.message)
async def broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    user_ids = await get_all_user_ids()
    sent = 0
    failed = 0

    await message.answer(f"📢 Xabar {len(user_ids)} ta foydalanuvchiga yuborilmoqda...")

    for uid in user_ids:
        try:
            await message.bot.copy_message(
                chat_id=uid,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            sent += 1
        except Exception:
            failed += 1

    await state.clear()
    await message.answer(
        f"📢 <b>XABAR YUBORILDI!</b>\n\n"
        f"✅ Muvaffaqiyatli: <b>{sent}</b> ta\n"
        f"❌ Yetib bormadi: <b>{failed}</b> ta",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


# =========================================================
# ADMIN: SUBJECTS CRUD (FANLARNI BOSHQARISH)
# =========================================================

@router.message(F.text == "📚 Fanlarni boshqarish")
async def manage_subjects_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    subjects = await get_subjects()
    await message.answer(
        "📚 <b>FANLARNI BOSHQARISH</b>\n\n"
        "✏️ — fanni tahrirlash\n"
        "🗑 — fanni o'chirish",
        reply_markup=admin_subjects_keyboard(subjects),
        parse_mode="HTML"
    )


@router.message(F.text == "➕ Fan qo'shish")
async def add_sub_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AddSubjectState.name)
    await message.answer(
        "➕ <b>YANGI FAN QO'SHISH</b>\n\n1️⃣ Fan nomini kiriting:\n<i>(Masalan: Geografiya)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddSubjectState.name)
async def add_sub_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("2️⃣ O'qituvchi ism-familiyasini kiriting:")
    await state.set_state(AddSubjectState.teacher)


@router.message(AddSubjectState.teacher)
async def add_sub_teacher(message: Message, state: FSMContext):
    await state.update_data(teacher=message.text.strip())
    await message.answer("3️⃣ Dars kunlarini kiriting:\n<i>(Masalan: Dushanba, Chorshanba, Juma)</i>")
    await state.set_state(AddSubjectState.days)


@router.message(AddSubjectState.days)
async def add_sub_days(message: Message, state: FSMContext):
    await state.update_data(days=message.text.strip())
    await message.answer("4️⃣ Dars vaqtini kiriting:\n<i>(Masalan: 14:00 - 16:00)</i>")
    await state.set_state(AddSubjectState.time)


@router.message(AddSubjectState.time)
async def add_sub_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text.strip())
    await message.answer("5️⃣ Kurs narxini kiriting:\n<i>(Masalan: Oyiga 350 000 so'm)</i>")
    await state.set_state(AddSubjectState.price)


@router.message(AddSubjectState.price)
async def add_sub_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text.strip())
    await message.answer("6️⃣ Qo'shimcha guruh/ma'lumot (agar bo'lmasa 'yo'q' deb yozing):")
    await state.set_state(AddSubjectState.small_group)


@router.message(AddSubjectState.small_group)
async def add_sub_small_group(message: Message, state: FSMContext):
    data = await state.get_data()
    sg = "" if message.text.lower() in ["yo'q", "yoq", "yoq."] else message.text.strip()

    await add_subject(
        name=data["name"],
        teacher=data["teacher"],
        time=data["time"],
        small_group=sg,
        days=data.get("days", ""),
        price=data.get("price", "")
    )
    await state.clear()
    await message.answer(
        f"✅ <b>{data['name']}</b> fani muvaffaqiyatli qo‘shildi!",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit:"))
async def edit_sub_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    sub_id = int(callback.data.split(":")[1])
    sub = await get_subject(sub_id)
    if not sub:
        await callback.answer("Fan topilmadi!")
        return

    await state.update_data(sub_id=sub_id)
    await state.set_state(EditSubjectState.name)
    await callback.message.answer(
        f"✏️ <b>FANNI TAHRIRLASH: {sub[1]}</b>\n\nYangi fan nomini kiriting:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(EditSubjectState.name)
async def edit_sub_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Yangi o'qituvchi ism-familiyasini kiriting:")
    await state.set_state(EditSubjectState.teacher)


@router.message(EditSubjectState.teacher)
async def edit_sub_teacher(message: Message, state: FSMContext):
    await state.update_data(teacher=message.text.strip())
    await message.answer("Yangi dars kunlarini kiriting:")
    await state.set_state(EditSubjectState.days)


@router.message(EditSubjectState.days)
async def edit_sub_days(message: Message, state: FSMContext):
    await state.update_data(days=message.text.strip())
    await message.answer("Yangi dars vaqtini kiriting:")
    await state.set_state(EditSubjectState.time)


@router.message(EditSubjectState.time)
async def edit_sub_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text.strip())
    await message.answer("Yangi kurs narxini kiriting:")
    await state.set_state(EditSubjectState.price)


@router.message(EditSubjectState.price)
async def edit_sub_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text.strip())
    await message.answer("Yangi qo'shimcha guruh ma'lumotini yozing (yoki 'yo'q'):")
    await state.set_state(EditSubjectState.small_group)


@router.message(EditSubjectState.small_group)
async def edit_sub_small_group(message: Message, state: FSMContext):
    data = await state.get_data()
    sg = "" if message.text.lower() in ["yo'q", "yoq", "yoq."] else message.text.strip()

    await update_subject(
        subject_id=data["sub_id"],
        name=data["name"],
        teacher=data["teacher"],
        time=data["time"],
        small_group=sg,
        days=data.get("days", ""),
        price=data.get("price", "")
    )
    await state.clear()
    await message.answer("✅ Fan ma'lumotlari muvaffaqiyatli yangilandi!", reply_markup=admin_menu(), parse_mode="HTML")


@router.callback_query(F.data.startswith("delete:"))
async def delete_sub_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    sub_id = int(callback.data.split(":")[1])
    sub = await get_subject(sub_id)
    if not sub:
        await callback.answer("Fan topilmadi!")
        return

    await delete_subject(sub_id)
    await callback.message.edit_text(f"🗑 <b>{sub[1]}</b> fani o‘chirildi.", parse_mode="HTML")
    await callback.answer("O‘chirildi!")


# =========================================================
# ADMIN: SETTINGS
# =========================================================

@router.message(F.text.in_(["⚙️ Sozlamalar", "📚 ⚙️ Sozlamalar"]))
async def settings_menu_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⚙️ <b>MARKAZ SOZLAMALARI</b>\n\nQuyidagi ma'lumotlarni Telegram orqali o'zgartirishingiz mumkin:",
        reply_markup=settings_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("setting:"))
async def setting_start_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    key = callback.data.split(":")[1]
    current = await get_setting(key)

    names = {
        "center_name": "🏫 Markaz nomi",
        "address": "📍 Manzil",
        "map_url": "🗺 Xarita linki (Google Maps)",
        "phone": "📞 Telefon",
        "admin_name": "👩‍💼 Admin ismi",
        "admin_username": "✈️ Admin Telegram",
        "card_number": "💳 Karta raqami",
        "card_holder": "👤 Karta egasi",
        "description": "ℹ️ Markaz haqida"
    }

    await state.update_data(setting_key=key)
    await state.set_state(SettingState.value)

    await callback.message.answer(
        f"⚙️ <b>{names.get(key, key)}</b>\n\n"
        f"Hozirgi qiymat:\n<code>{current}</code>\n\n"
        "Yangi qiymatni kiriting:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(SettingState.value)
async def setting_save_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data["setting_key"]
    await set_setting(key, message.text.strip())
    await state.clear()
    await message.answer("✅ Sozlama muvaffaqiyatli saqlandi!", reply_markup=admin_menu(), parse_mode="HTML")