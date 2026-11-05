from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


# =========================================================
# SUBJECT ICONS
# =========================================================

def get_subject_icon(name: str) -> str:
    n = name.lower()
    if "ona tili" in n:
        return "🇺🇿"
    elif "rus tili" in n:
        return "🇷🇺"
    elif "ingliz" in n:
        return "🇬🇧"
    elif "matematika" in n:
        return "📐"
    elif "kimyo" in n:
        return "🧪"
    elif "biologiya" in n:
        return "🧬"
    elif "fizika" in n:
        return "⚡"
    elif "tarix" in n or "tarih" in n:
        return "🏛️"
    elif "huquq" in n:
        return "⚖️"
    elif "informatika" in n or "it" in n or "dasturlash" in n:
        return "💻"
    elif "geografiya" in n:
        return "🌍"
    elif "adabiyot" in n:
        return "📜"
    elif "mantiq" in n:
        return "🧠"
    return "📚"


# =========================================================
# USER MAIN MENU
# =========================================================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Mening profilim"),
                KeyboardButton(text="💳 To‘lov qilish")
            ],
            [
                KeyboardButton(text="🔔 Eslatmalar"),
                KeyboardButton(text="📚 Darslar haqida (@Peramidauzbot)")
            ],
            [
                KeyboardButton(text="📍 Manzil"),
                KeyboardButton(text="📞 Bog'lanish")
            ],
            [
                KeyboardButton(text="ℹ️ Markaz haqida"),
                KeyboardButton(text="👑 Admin panel")
            ]
        ],
        resize_keyboard=True
    )


def peramida_bot_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👉 @Peramidauzbot ga o‘tish",
                    url="https://t.me/Peramidauzbot"
                )
            ]
        ]
    )


# =========================================================
# REGISTRATION KEYBOARDS
# =========================================================

def contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Telefon raqamni yuborish",
                    request_contact=True
                )
            ],
            [
                KeyboardButton(text="❌ Bekor qilish")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def days_selection_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Seshanba, Payshanba, Shanba")
            ],
            [
                KeyboardButton(text="Dushanba, Chorshanba, Juma")
            ],
            [
                KeyboardButton(text="Har kuni (Dushanba - Shanba)")
            ],
            [
                KeyboardButton(text="❌ Bekor qilish")
            ]
        ],
        resize_keyboard=True
    )


def subjects_selection_inline(subjects):
    buttons = []
    row = []
    for s in subjects:
        icon = get_subject_icon(s[1])
        row.append(
            InlineKeyboardButton(
                text=f"{icon} {s[1]}",
                callback_data=f"reg_sub:{s[0]}"
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================================================
# PAYMENT KEYBOARDS
# =========================================================

def payment_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Payme / Karta (📸 Chek yuborish)",
                    callback_data="send_receipt"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💵 Naqd to‘lov qildim (✅ Tasdiqlash)",
                    callback_data="pay_cash"
                )
            ]
        ]
    )


def payment_action_keyboard(admin_username="Isroilova_Ozoda", is_pending=False, is_paid=False):
    clean_user = admin_username.replace("@", "").strip() if admin_username else "Isroilova_Ozoda"

    if is_pending:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📸 Chekni qayta yuborish (Payme / Karta)",
                        callback_data="send_receipt"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💵 Naqd to‘lov qildim (✅ Tasdiqlash)",
                        callback_data="pay_cash"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✈️ Administratorga yozish",
                        url=f"https://t.me/{clean_user}"
                    )
                ]
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Payme / Karta (📸 Chek yuborish)",
                    callback_data="send_receipt"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💵 Naqd to‘lov qildim (✅ Tasdiqlash)",
                    callback_data="pay_cash"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✈️ Administratorga yozish",
                    url=f"https://t.me/{clean_user}"
                )
            ]
        ]
    )


def reminder_payment_keyboard(admin_username="Isroilova_Ozoda"):
    clean_user = admin_username.replace("@", "").strip() if admin_username else "Isroilova_Ozoda"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 To‘lov qilish",
                    callback_data="pay_card"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💵 Naqd to‘lov qildim (✅ Tasdiqlash)",
                    callback_data="pay_cash"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✈️ Administrator bilan bog‘lanish",
                    url=f"https://t.me/{clean_user}"
                )
            ]
        ]
    )


def cash_payment_confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha, naqd to‘lov qildim",
                    callback_data="confirm_cash_done"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel_cash_done"
                )
            ]
        ]
    )


def payment_decision_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"approve_{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"reject_{user_id}"
                )
            ]
        ]
    )


# =========================================================
# CANCEL KEYBOARD
# =========================================================

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


# =========================================================
# MAP & CONTACT INLINE
# =========================================================

def map_inline_keyboard(url):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗺 Google Maps'da ochish",
                    url=url
                )
            ]
        ]
    )


def contact_inline_keyboard(phone="+998-97-162-84-00", username="Isroilova_Ozoda"):
    clean_user = username.replace("@", "").strip() if username else "Isroilova_Ozoda"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✈️ Admin bilan bog'lanish",
                    url=f"https://t.me/{clean_user}"
                )
            ]
        ]
    )


def subject_detail_keyboard(phone="+998-97-162-84-00", username="Isroilova_Ozoda"):
    clean_user = username.replace("@", "").strip() if username else "Isroilova_Ozoda"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✈️ Kursga yozilish (Admin)",
                    url=f"https://t.me/{clean_user}"
                )
            ]
        ]
    )


# =========================================================
# ADMIN MENU
# =========================================================

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👨‍🎓 O‘quvchilar"),
                KeyboardButton(text="🗑 O‘quvchini o‘chirish")
            ],
            [
                KeyboardButton(text="💰 To‘lov kutilmoqda"),
                KeyboardButton(text="⚠️ Qarzdorlar")
            ],
            [
                KeyboardButton(text="📊 Statistika"),
                KeyboardButton(text="📢 Xabar yuborish")
            ],
            [
                KeyboardButton(text="📚 Fanlarni boshqarish"),
                KeyboardButton(text="➕ Fan qo'shish")
            ],
            [
                KeyboardButton(text="📚 ⚙️ Sozlamalar"),
                KeyboardButton(text="🚪 Chiqish")
            ],
            [
                KeyboardButton(text="⬅️ Asosiy menyu")
            ]
        ],
        resize_keyboard=True
    )


# =========================================================
# ADMIN STUDENTS MANAGEMENT KEYBOARDS
# =========================================================

def admin_students_action_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 O‘quvchini o‘chirish",
                    callback_data="admin_open_delete_students"
                )
            ]
        ]
    )


def admin_delete_students_keyboard(students):
    buttons = []
    for uid, s in list(students.items())[:50]:
        name = s.get("name", "Noma'lum")
        subject = s.get("subject", "")
        btn_text = f"👤 {name}"
        if subject:
            btn_text += f" ({subject})"
        if len(btn_text) > 40:
            btn_text = btn_text[:37] + "..."
        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"del_stud:{uid}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="del_stud_cancel"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_confirm_delete_student_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Ha, o‘chirilsin",
                    callback_data=f"del_stud_conf:{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="del_stud_cancel"
                )
            ]
        ]
    )


# =========================================================
# SUBJECTS INLINE KEYBOARDS
# =========================================================

def subjects_keyboard(subjects):
    buttons = []
    for subject in subjects:
        subject_id = subject[0]
        name = subject[1]
        icon = get_subject_icon(name)
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {name}",
                callback_data=f"subject:{subject_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_subjects_keyboard(subjects):
    buttons = []
    for subject in subjects:
        subject_id = subject[0]
        name = subject[1]
        icon = get_subject_icon(name)
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} ✏️ {name}",
                callback_data=f"edit:{subject_id}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"delete:{subject_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================================================
# SETTINGS INLINE KEYBOARD
# =========================================================

def settings_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏫 Markaz nomi",
                    callback_data="setting:center_name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📍 Manzil",
                    callback_data="setting:address"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗺 Xarita linki",
                    callback_data="setting:map_url"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 Telefon",
                    callback_data="setting:phone"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👩‍💼 Admin ismi",
                    callback_data="setting:admin_name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✈️ Admin Telegram",
                    callback_data="setting:admin_username"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Karta raqami",
                    callback_data="setting:card_number"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Karta egasi",
                    callback_data="setting:card_holder"
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ Markaz haqida",
                    callback_data="setting:description"
                )
            ]
        ]
    )