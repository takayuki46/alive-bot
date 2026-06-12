import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# ⚠️ あなたのBotトークンを貼り付けてください
# ==========================================
TOKEN = '8924268839:AAG3AKBZfHYkXtXQEzNOpvBddqKgph9tVsc'

# ==========================================
# 🚨 緊急事態の通知先（あなたの友達のTelegram Chat IDなど）
# ==========================================
# テスト用として、まずはご自身のChat ID（または通知したい相手のID）を入れます
EMERGENCY_CONTACT_ID = 0  # 後ほど数字に書き換えます

# ユーザーデータの保存用
user_data = {}

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
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("日本語 🇯🇵", callback_data='lang_ja'),
         InlineKeyboardButton("English 🇬🇧", callback_data='lang_en')]
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
        keyboard = [[InlineKeyboardButton(TEXTS[lang]['btn_alive'], callback_data='checkin')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await query.edit_message_text(text=f"{TEXTS[lang]['alive_confirm']}{now_str}", reply_markup=reply_markup)

# 💡 Renderが5分ごとにこの関数を自動実行し、48時間超過をチェックします
async def check_survival(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    for user_id, data in user_data.items():
        last_checkin = data.get("last_checkin")
        if last_checkin and (now - last_checkin) > timedelta(hours=48):
            lang = data.get("lang", "en")
            # 緊急連絡先（指定したID）にメッセージを飛ばす
            if EMERGENCY_CONTACT_ID != 0:
                try:
                    await context.bot.send_message(chat_id=EMERGENCY_CONTACT_ID, text=TEXTS[lang]['emergency_msg'])
                    logging.info(f"Emergency alert sent for user {user_id}")
                except Exception as e:
                    logging.error(f"Failed to send emergency message: {e}")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    # 5分ごとに生存チェックを行うタイマーを設定
    job_queue = application.job_queue
    job_queue.run_repeating(check_survival, interval=300, first=10)
    
    print("通知機能付きボットが起動しました...")
    application.run_polling()

if __name__ == '__main__':
    main()
