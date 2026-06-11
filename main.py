import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# ⚠️ ここにあなたのBotトークンを貼り付けてください
# ==========================================
TOKEN = '8924268839:AAG3AKBZfHYkXtXQEzNOpvBddqKgph9tVsc'

# ユーザーデータの保存用（簡易版）
user_data = {}

# ログ設定（エラーなどを記録する設定）
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# メッセージの多言語辞書
TEXTS = {
    'ja': {
        'welcome': "「生きてるかボット」へようこそ！\nこのボットはあなたの生存を確認します。毎日ボタンを押して生存を報告してください。\n\n現在のステータス：生存確認完了🟢",
        'btn_alive': "生存報告（私は生きてる！）",
        'alive_confirm': "生存報告を確認しました！\n最終確認時刻: ",
        'emergency_set': "🚨 緊急事態！48時間生存報告がありません！"
    },
    'en': {
        'welcome': "Welcome to 'Are You Alive?' Bot!\nThis bot checks your survival. Please press the button every day to report you are alive.\n\nStatus: Checked In 🟢",
        'btn_alive': "I'm Alive!",
        'alive_confirm': "Check-in confirmed!\nLast check-in: ",
        'emergency_set': "🚨 EMERGENCY! No check-in for 48 hours!"
    }
}

# /start コマンドが押された時（言語選択）
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # 最初に日本語か英語かを選ばせるボタンを表示
    keyboard = [
        [InlineKeyboardButton("日本語 🇯🇵", callback_data='lang_ja'),
         InlineKeyboardButton("English 🇬🇧", callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Please select your language / 言語を選択してください：",
        reply_markup=reply_markup
    )

# ボタンが押された時の処理
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action = query.data
    
    # 言語選択のボタンが押された場合
    if action.startswith('lang_'):
        lang = action.split('_')[1]
        user_data[user_id] = {
            "lang": lang,
            "last_checkin": datetime.now()
        }
        
        # 選ばれた言語でメイン画面を表示
        keyboard = [[InlineKeyboardButton(TEXTS[lang]['btn_alive'], callback_data='checkin')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=TEXTS[lang]['welcome'], reply_markup=reply_markup)
        
    # 「生きてる！」ボタンが押された場合
    elif action == 'checkin':
        lang = user_data.get(user_id, {}).get("lang", "en") # 設定がなければ英語
        user_data[user_id]["last_checkin"] = datetime.now()
        
        keyboard = [[InlineKeyboardButton(TEXTS[lang]['btn_alive'], callback_data='checkin')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await query.edit_message_text(
            text=f"{TEXTS[lang]['alive_confirm']}{now_str}",
            reply_markup=reply_markup
        )

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    print("ボットが起動しました...（Ctrl+C で停止）")
    application.run_polling()

if __name__ == '__main__':
    main()
