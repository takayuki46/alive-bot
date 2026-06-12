import logging
import os
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# ⚠️ あなたのBotトークンを貼り付けてください
# ==========================================
TOKEN = '8924268839:AAG3AKBZfHYkXtXQEzNOpvBddqKgph9tVsc'

# ==========================================
# 🚨 緊急事態の通知先＆管理者ID（あなたの数字の識別番号）
# ==========================================
EMERGENCY_CONTACT_ID = 8743551795  # あなたのChat ID（数字）に書き換えてください

# ユーザーデータの保存用
user_data = {}

# 📊 統計データ用カウンター
stats_data = {
    "total_checkins": 0  # 総生存報告回数
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TEXTS = {
    'ja': {
        'welcome': "「生きてるかボット」へようこそ！\n48時間生存報告がない場合、登録された緊急連絡先へ通知されます。\n\n現在のステータス：生存確認完了🟢",
        'btn_alive': "生存報告（私は生きてる！）",
        'alive_confirm': "生存報告を確認しました！\n最終確認時刻: ",
        'emergency_msg': "🚨【緊急事態】ユーザーからの生存報告が48時間途絶えました！確認してください。"
    },
    'en': {
        'welcome': "Welcome to 'Are You Alive?' Bot!\nIf no report for 48 hours, an alert will be sent to your emergency contact.\n\nStatus: Checked In 🟢",
        'btn_alive': "I'm Alive!",
        'alive_confirm': "Check-in confirmed!\nLast check-in: ",
        'emergency_msg': "🚨 [EMERGENCY] No check-in reported from the user for 48 hours! Please verify."
    },
    'ru': {
        'welcome': "Добро пожаловать в бот «Я жив»!\nЕсли вы не будете отмечаться в течение 48 часов, ваше доверенное лицо получит уведомление.\n\nСтатус: Подтверждено 🟢",
        'btn_alive': "Я жив!",
        'alive_confirm': "Отметка принята!\nПоследняя отметка: ",
        'emergency_msg': "🚨 [ТРЕВОГА] Пользователь не выходил на связь более 48 часов! Пожалуйста, проверьте."
    },
    'uk': {
        'welcome': "Ласкаво просимо до бота «Я живий»!\nЯкщо ви не будете відмічатися протягом 48 годин, вашій довіреній особі буде надіслано сповіщення.\n\nСтатус: Підтверждено 🟢",
        'btn_alive': "Я живий!",
        'alive_confirm': "Відмітку прийнято!\nОстання відмітка: ",
        'emergency_msg': "🚨 [ТРИВОГА] Користувач не выходил на зв'язок більше 48 годин! Будь ласка, перевірте."
    },
    'fa': {
        'welcome': "به ربات «من زنده‌ام» خوش آمدید!\nاگر تا ۴۸ ساعت اعلام وضعیت نکنید، یک پیام هشدار به مخاطب اضطراری شما ارسال خواهد شد.\n\nوضعیت فعلی: تایید شده 🟢",
        'btn_alive': "من زنده‌ام!",
        'alive_confirm': "اعلام وضعیت ثبت شد!\nآخرین اعلام وضعیت: ",
        'emergency_msg': "🚨 [اضطراری] کاربر بیش از ۴۸ ساعت است که اعلام وضعیت نکرده است! لطفاً بررسی کنید."
    },
    'zh_cn': {
        'welcome': "欢迎使用“我还活着”机器人！\n如果连续48小时没有生存报告，系统将自动通知您的紧急联系人。\n\n当前状态：签到成功🟢",
        'btn_alive': "生存报告（我还活着！）",
        'alive_confirm': "生存报告已确认！\n最后签到时间: ",
        'emergency_msg': "🚨【紧急情况】用户已连续48小时未进行生存报告！请即刻确认其安全。"
    },
    'zh_tw': {
        'welcome': "歡迎使用「我還活著」機器人！\n如果連續48小時沒有生存報告，系統將自動通知您的緊急聯絡人。\n\n當前狀態：簽到成功🟢",
        'btn_alive': "生存報告（我還活著！）",
        'alive_confirm': "生存報告已確認！\n最後簽到時間: ",
        'emergency_msg': "🚨【緊急情況】用戶已連續48小時未進行生存報告！請即刻確認其安全。"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("日本語 🇯🇵", callback_data='lang_ja'),
         InlineKeyboardButton("English 🇬🇧", callback_data='lang_en')],
        [InlineKeyboardButton("Русский 🇷🇺", callback_data='lang_ru'),
         InlineKeyboardButton("Українська 🇺🇦", callback_data='lang_uk')],
        [InlineKeyboardButton("简体中文 🇨🇳", callback_data='lang_zh_cn'),
         InlineKeyboardButton("繁體中文 🇹🇼", callback_data='lang_zh_tw')],
        [InlineKeyboardButton("فارسی 🇮🇷", callback_data='lang_fa')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please select your language / 言語を選択してください：", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data
    
    if action.startswith('lang_'):
        lang = action.split('_')[1]
        user_data[user_id] = {"lang": lang, "last_checkin": datetime.now()}
        keyboard = [[InlineKeyboardButton(TEXTS[lang]['btn_alive'], callback_data='checkin')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=TEXTS[lang]['welcome'], reply_markup=reply_markup)
        
    elif action == 'checkin':
        lang = user_data.get(user_id, {}).get("lang", "en")
        user_data[user_id]["last_checkin"] = datetime.now()
        
        # 📊 ボタンが押されたので回数を1増やす
        stats_data["total_checkins"] += 1
        
        keyboard = [[InlineKeyboardButton(TEXTS[lang]['btn_alive'], callback_data='checkin')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await query.edit_message_text(text=f"{TEXTS[lang]['alive_confirm']}{now_str}", reply_markup=reply_markup)

# 📊 あなただけが見られる利用状況確認コマンド
async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # 管理者（あなた）のIDと一致する場合のみデータを返す
    if user_id == EMERGENCY_CONTACT_ID:
        active_users = len(user_data)
        total_clicks = stats_data["total_checkins"]
        message = (
            f"📊 【ボット利用状況ステータス】\n\n"
            f"👥 現在の登録ユーザー数: {active_users} 名\n"
            f"👆 総生存報告ボタン押下回数: {total_clicks} 回"
        )
        await update.message.reply_text(message)
    else:
        # 管理者以外には何も返さない（またはエラーを返さないように無視する）
        pass

async def check_survival(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    for user_id, data in user_data.items():
        last_checkin = data.get("last_checkin")
        if last_checkin and (now - last_checkin) > timedelta(hours=48):
            lang = data.get("lang", "en")
            if EMERGENCY_CONTACT_ID != 0:
                try:
                    await context.bot.send_message(chat_id=EMERGENCY_CONTACT_ID, text=TEXTS[lang]['emergency_msg'])
                    logging.info(f"Emergency alert sent for user {user_id}")
                except Exception as e:
                    logging.error(f"Failed to send emergency message: {e}")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

def main():
    threading.Thread(target=run_health_check, daemon=True).start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", get_stats)) # 📊 隠しコマンドを追加
    application.add_handler(CallbackQueryHandler(button_click))
    
    job_queue = application.job_queue
    job_queue.run_repeating(check_survival, interval=300, first=10)
    
    print("管理者コマンド付きボットが起動しました...")
    application.run_polling()

if __name__ == '__main__':
    main()
