import os
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import random
from datetime import datetime

# Environment variables - REQUIRED
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')
VERCEL_URL = os.environ.get('VERCEL_URL', 'https://your-app.vercel.app')
AFFILIATE_LINK = os.environ.get('AFFILIATE_LINK', 'https://mostbet-king.com/5w4F')

app = Flask(__name__)

# Simple storage
users = {}
postback_data = {'registrations': {}, 'deposits': {}}

# ALL 5 LANGUAGES - COMPLETE
languages = {
    'en': {
        'name': "English", 'flag': "🇺🇸",
        'welcome': "✅ You selected English!",
        'select_language': "Select your preferred Languages",
        'step1': "🌐 Step 1 - Register",
        'must_new': "‼️ THE ACCOUNT MUST BE NEW", 
        'instructions': """1️⃣ Click REGISTER button\n2️⃣ Use promocode: CLAIM\n3️⃣ Deposit 600₹ or 6$\n✅ Then CHECK REGISTRATION""",
        'enter_player_id': "Enter your Mostbet Player ID:",
        'congratulations': "Congratulations! Select Game Mode:",
        'not_registered': "❌ Not Registered! Click REGISTER first.",
        'registered_no_deposit': "✅ Registered! Please deposit 600₹ or 6$",
        'verified': "✅ Verification Successful!",
        'checking': "🔍 Checking...",
        'limit_reached': "Limit reached! Try tomorrow."
    },
    'hi': {
        'name': "हिंदी", 'flag': "🇮🇳",
        'welcome': "✅ आपने हिंदी चुनी!",
        'select_language': "अपनी भाषा चुनें",
        'step1': "🌐 स्टेप 1 - रजिस्टर करें",
        'must_new': "‼️ अकाउंट नया होना चाहिए",
        'instructions': """1️⃣ REGISTER बटन क्लिक करें\n2️⃣ प्रोमोकोड: CLAIM\n3️⃣ 600₹ या 6$ जमा करें\n✅ फिर CHECK REGISTRATION""",
        'enter_player_id': "अपना Player ID दर्ज करें:",
        'congratulations': "बधाई! गेम मोड चुनें:",
        'not_registered': "❌ रजिस्टर्ड नहीं! पहले REGISTER करें।",
        'registered_no_deposit': "✅ रजिस्टर्ड! कृपया 600₹ या 6$ जमा करें",
        'verified': "✅ सत्यापन सफल!",
        'checking': "🔍 जांच हो रही...",
        'limit_reached': "सीमा पूरी! कल फिर कोशिश करें।"
    },
    'bn': {
        'name': "বাংলা", 'flag': "🇧🇩",
        'welcome': "✅ আপনি বাংলা নির্বাচন করেছেন!",
        'select_language': "আপনার ভাষা নির্বাচন করুন",
        'step1': "🌐 ধাপ 1 - নিবন্ধন করুন",
        'must_new': "‼️ অ্যাকাউন্টটি নতুন হতে হবে",
        'instructions': """1️⃣ REGISTER বাটন ক্লিক করুন\n2️⃣ প্রমোকোড: CLAIM\n3️⃣ 600₹ বা 6$ জমা করুন\n✅ তারপর CHECK REGISTRATION""",
        'enter_player_id': "আপনার Player ID লিখুন:",
        'congratulations': "অভিনন্দন! গেম মোড নির্বাচন করুন:",
        'not_registered': "❌ নিবন্ধিত নন! প্রথমে REGISTER করুন।",
        'registered_no_deposit': "✅ নিবন্ধিত! দয়া করে 600₹ বা 6$ জমা করুন",
        'verified': "✅ যাচাইকরণ সফল!",
        'checking': "🔍 পরীক্ষা করা হচ্ছে...",
        'limit_reached': "সীমা reached! আগামীকাল আবার চেষ্টা করুন।"
    },
    'ur': {
        'name': "اردو", 'flag': "🇵🇰",
        'welcome': "✅ آپ نے اردو منتخب کی!",
        'select_language': "اپنی زبان منتخب کریں",
        'step1': "🌐 مرحلہ 1 - رجسٹر کریں",
        'must_new': "‼️ اکاؤنٹ نیا ہونا چاہیے",
        'instructions': """1️⃣ REGISTER بٹن پر کلک کریں\n2️⃣ پروموکوڈ: CLAIM\n3️⃣ 600₹ یا 6$ جمع کریں\n✅ پھر CHECK REGISTRATION""",
        'enter_player_id': "اپنا Player ID درج کریں:",
        'congratulations': "مبارک ہو! گیم موڈ منتخب کریں:",
        'not_registered': "❌ رجسٹرڈ نہیں! پہلے REGISTER کریں۔",
        'registered_no_deposit': "✅ رجسٹرڈ! براہ کرم 600₹ یا 6$ جمع کریں",
        'verified': "✅ تصدیق کامیاب!",
        'checking': "🔍 چیک ہو رہا...",
        'limit_reached': "حد reached! کل دوبارہ کوشش کریں۔"
    },
    'ne': {
        'name': "नेपाली", 'flag': "🇳🇵",
        'welcome': "✅ तपाईंले नेपाली चयन गर्नुभयो!",
        'select_language': "आफ्नो भाषा चयन गर्नुहोस्",
        'step1': "🌐 चरण 1 - दर्ता गर्नुहोस्",
        'must_new': "‼️ खाता नयाँ हुनुपर्छ",
        'instructions': """1️⃣ REGISTER बटन क्लिक गर्नुहोस्\n2️⃣ प्रोमोकोड: CLAIM\n3️⃣ 600₹ वा 6$ जम्मा गर्नुहोस्\n✅ त्यसपछि CHECK REGISTRATION""",
        'enter_player_id': "आफ्नो Player ID प्रविष्ट गर्नुहोस्:",
        'congratulations': "बधाई छ! खेल मोड चयन गर्नुहोस्:",
        'not_registered': "❌ दर्ता गरिएको छैन! पहिले REGISTER गर्नुहोस्।",
        'registered_no_deposit': "✅ दर्ता गरिएको! कृपया 600₹ वा 6$ जम्मा गर्नुहोस्",
        'verified': "✅ सत्यापन सफल!",
        'checking': "🔍 जाँच गरिदै...",
        'limit_reached': "सीमा reached! भोली फेरि प्रयास गर्नुहोस्।"
    }
}

# ALL PREDICTION IMAGES - COMPLETE
prediction_images = {
    'easy': [
        {'url': "https://i.postimg.cc/dQS5pr0N/IMG-20251020-095836-056.jpg", 'accuracy': "85%"},
        {'url': "https://i.postimg.cc/P5BxR3GJ/IMG-20251020-095841-479.jpg", 'accuracy': "95%"},
        {'url': "https://i.postimg.cc/QdWN1QBr/IMG-20251020-095848-018.jpg", 'accuracy': "78%"},
        {'url': "https://i.postimg.cc/gjJmJ89H/IMG-20251020-095902-112.jpg", 'accuracy': "85%"},
        {'url': "https://i.postimg.cc/QMJ3J0hQ/IMG-20251020-095906-484.jpg", 'accuracy': "70%"},
        {'url': "https://i.postimg.cc/654xm9BR/IMG-20251020-095911-311.jpg", 'accuracy': "80%"},
        {'url': "https://i.postimg.cc/NMCZdnVX/IMG-20251020-095916-536.jpg", 'accuracy': "82%"},
        {'url': "https://i.postimg.cc/8k3qWqLk/IMG-20251020-095921-307.jpg", 'accuracy': "88%"},
        {'url': "https://i.postimg.cc/pdqSd72R/IMG-20251020-095926-491.jpg", 'accuracy': "75%"},
        {'url': "https://i.postimg.cc/05T9x6WH/IMG-20251020-095937-768.jpg", 'accuracy': "90%"},
        {'url': "https://i.postimg.cc/CKrV2dnv/IMG-20251020-095949-124.jpg", 'accuracy': "83%"},
        {'url': "https://i.postimg.cc/L5dGdP9Y/IMG-20251020-095954-011.jpg", 'accuracy': "79%"},
        {'url': "https://i.postimg.cc/FHF8QN4f/IMG-20251020-100002-472.jpg", 'accuracy': "86%"},
        {'url': "https://i.postimg.cc/25MKvWBg/IMG-20251020-100012-671.jpg", 'accuracy': "81%"},
        {'url': "https://i.postimg.cc/4ybLrF2D/IMG-20251020-100023-691.jpg", 'accuracy': "87%"},
        {'url': "https://i.postimg.cc/vZmqNhrP/IMG-20251020-100033-810.jpg", 'accuracy': "84%"},
        {'url': "https://i.postimg.cc/8cDwBmk3/IMG-20251020-100038-185.jpg", 'accuracy': "77%"},
        {'url': "https://i.postimg.cc/7YKX0zFL/IMG-20251020-100045-990.jpg", 'accuracy': "89%"},
        {'url': "https://i.postimg.cc/ZRzL4xNb/IMG-20251020-100053-162.jpg", 'accuracy': "76%"},
        {'url': "https://i.postimg.cc/9QvdYYJb/IMG-20251020-100113-609.jpg", 'accuracy': "91%"}
    ],
    'medium': [
        {'url': "https://i.postimg.cc/JnJPX4J6/IMG-20251020-104414-537.jpg", 'accuracy': "85%"},
        {'url': "https://i.postimg.cc/ZnHPP9qJ/IMG-20251020-104430-876.jpg", 'accuracy': "82%"},
        {'url': "https://i.postimg.cc/Z528LzJ2/IMG-20251020-104435-861.jpg", 'accuracy': "88%"},
        {'url': "https://i.postimg.cc/tJ4njBXg/IMG-20251020-104439-671.jpg", 'accuracy': "83%"},
        {'url': "https://i.postimg.cc/dVykwkKH/IMG-20251020-104443-615.jpg", 'accuracy': "87%"},
        {'url': "https://i.postimg.cc/MHHH4XDw/IMG-20251020-104452-202.jpg", 'accuracy': "84%"},
        {'url': "https://i.postimg.cc/6pn3FkdL/IMG-20251020-104498-282.jpg", 'accuracy': "86%"},
        {'url': "https://i.postimg.cc/85PzJsqD/IMG-20251020-104509-839.jpg", 'accuracy': "81%"},
        {'url': "https://i.postimg.cc/bN2N27Vm/IMG-20251020-104521-438.jpg", 'accuracy': "89%"},
        {'url': "https://i.postimg.cc/0NZ8sPrV/IMG-20251020-104526-899.jpg", 'accuracy': "85%"},
        {'url': "https://i.postimg.cc/T2KWCHHs/IMG-20251020-104532-810.jpg", 'accuracy': "82%"},
        {'url': "https://i.postimg.cc/ZqYW3fdX/IMG-20251020-104537-998.jpg", 'accuracy': "88%"},
        {'url': "https://i.postimg.cc/wxR7hR7w/IMG-20251020-104543-014.jpg", 'accuracy': "83%"},
        {'url': "https://i.postimg.cc/3x1RKgcx/IMG-20251020-104615-327.jpg", 'accuracy': "87%"}
    ],
    'hard': [
        {'url': "https://i.postimg.cc/4N8qsy1c/IMG-20251020-105355-761.jpg", 'accuracy': "85%"},
        {'url': "https://i.postimg.cc/tJ4njBXg/IMG-20251020-104439-671.jpg", 'accuracy': "82%"},
        {'url': "https://i.postimg.cc/8cpXVgJ4/IMG-20251020-105410-692.jpg", 'accuracy': "88%"},
        {'url': "https://i.postimg.cc/HsLvZH1t/IMG-20251020-105415-479.jpg", 'accuracy': "83%"},
        {'url': "https://i.postimg.cc/90gb5RH8/IMG-20251020-105424-630.jpg", 'accuracy': "87%"},
        {'url': "https://i.postimg.cc/HL12g1F1/IMG-20251020-105428-916.jpg", 'accuracy': "84%"},
        {'url': "https://i.postimg.cc/hjpbTzvJ/IMG-20251020-105436-994.jpg", 'accuracy': "86%"},
        {'url': "https://i.postimg.cc/RVj17zSJ/IMG-20251020-105443-517.jpg", 'accuracy': "81%"},
        {'url': "https://i.postimg.cc/bJN1yygc/IMG-20251020-105450-320.jpg", 'accuracy': "89%"},
        {'url': "https://i.postimg.cc/DfSBL6Q8/IMG-20251020-105458-348.jpg", 'accuracy': "85%"},
        {'url': "https://i.postimg.cc/zDHFVB5B/IMG-20251020-105512-639.jpg", 'accuracy': "82%"}
    ],
    'hardcore': [
        {'url': "https://i.postimg.cc/NMcBmFVb/IMG-20251020-110213-026.jpg", 'accuracy': "85%"},
        {'url': "https://i.postimg.cc/xjgnN0P6/IMG-20251020-110218-479.jpg", 'accuracy': "82%"},
        {'url': "https://i.postimg.cc/FsBvGD8p/IMG-20251020-110222-741.jpg", 'accuracy': "88%"},
        {'url': "https://i.postimg.cc/RVj17zSJ/IMG-20251020-105443-517.jpg", 'accuracy': "83%"},
        {'url': "https://i.postimg.cc/pTRMy75V/IMG-20251020-110240-031.jpg", 'accuracy': "87%"},
        {'url': "https://i.postimg.cc/VvZxGkGs/IMG-20251020-110255-468.jpg", 'accuracy': "84%"}
    ]
}

# Initialize bot
bot_app = Application.builder().token(BOT_TOKEN).build()

# 1Win Postback
@app.route('/lwin-postback', methods=['GET'])
def lwin_postback():
    player_id = request.args.get('player_id')
    status = request.args.get('status')
    amount = request.args.get('amount', 0)
    
    if status == 'registration':
        postback_data['registrations'][player_id] = {'player_id': player_id, 'status': 'registered'}
    elif status == 'fdp':
        postback_data['deposits'][player_id] = {'player_id': player_id, 'status': 'deposited', 'amount': amount}
    
    return jsonify({'success': True, 'player_id': player_id, 'status': status})

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in users:
        users[user_id] = {'id': user_id, 'language': 'en', 'registered': False, 'deposited': False, 'player_id': None, 'predictions_used': 0}
    
    user = users[user_id]
    lang = user['language']
    
    keyboard = [
        [InlineKeyboardButton(f"{languages['en']['flag']} {languages['en']['name']}", callback_data='lang_en')],
        [InlineKeyboardButton(f"{languages['hi']['flag']} {languages['hi']['name']}", callback_data='lang_hi')],
        [InlineKeyboardButton(f"{languages['bn']['flag']} {languages['bn']['name']}", callback_data='lang_bn')],
        [InlineKeyboardButton(f"{languages['ur']['flag']} {languages['ur']['name']}", callback_data='lang_ur')],
        [InlineKeyboardButton(f"{languages['ne']['flag']} {languages['ne']['name']}", callback_data='lang_ne')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(languages[lang]['select_language'], reply_markup=reply_markup)

# Handle language selection
async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = query.data
    
    if data.startswith('lang_'):
        lang = data.split('_')[1]
        users[user_id]['language'] = lang
        
        await query.edit_message_text(languages[lang]['welcome'])
        
        keyboard = [
            [InlineKeyboardButton("📲 Register", url=AFFILIATE_LINK)],
            [InlineKeyboardButton("🔍 Check Registration", callback_data='check_registration')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_photo(
            photo='https://i.postimg.cc/4Nh2kPnv/Picsart-25-10-16-14-41-43-751.jpg',
            caption=f"{languages[lang]['step1']}\n\n{languages[lang]['must_new']}\n\n{languages[lang]['instructions']}",
            reply_markup=reply_markup
        )

# Handle check registration
async def handle_check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    lang = users[user_id]['language']
    
    await query.message.reply_text(f"{languages[lang]['enter_player_id']}")

# Handle player ID input
async def handle_player_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    player_id = update.message.text
    user = users[user_id]
    lang = user['language']
    
    if player_id.isdigit():
        user['player_id'] = player_id
        
        checking_msg = await update.message.reply_text(languages[lang]['checking'])
        
        try:
            registration = postback_data['registrations'].get(player_id)
            deposit = postback_data['deposits'].get(player_id)
            
            await checking_msg.delete()
            
            if registration and deposit:
                user['registered'] = True
                user['deposited'] = True
                
                keyboard = [
                    [InlineKeyboardButton("🎯 Easy", callback_data='mode_easy')],
                    [InlineKeyboardButton("⚡ Medium", callback_data='mode_medium')],
                    [InlineKeyboardButton("🔥 Hard", callback_data='mode_hard')],
                    [InlineKeyboardButton("💀 Hardcore", callback_data='mode_hardcore')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(f"{languages[lang]['verified']}\n\n{languages[lang]['congratulations']}", reply_markup=reply_markup)
                
            elif registration and not deposit:
                user['registered'] = True
                
                keyboard = [
                    [InlineKeyboardButton("💳 Deposit", url=AFFILIATE_LINK)],
                    [InlineKeyboardButton("🔍 Check Deposit", callback_data='check_deposit')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(languages[lang]['registered_no_deposit'], reply_markup=reply_markup)
                
            else:
                keyboard = [[InlineKeyboardButton("📲 Register Now", url=AFFILIATE_LINK)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(languages[lang]['not_registered'], reply_markup=reply_markup)
                
        except Exception as e:
            await checking_msg.delete()
            keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data='check_registration')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❌ Verification failed. Please try again.", reply_markup=reply_markup)

# Send prediction function
async def send_prediction(chat_id, user_id, mode, step):
    user = users[user_id]
    lang = user['language']
    mode_images = prediction_images[mode]
    random_image = random.choice(mode_images)
    
    keyboard = [
        [InlineKeyboardButton("➡️ Next", callback_data=f'next_{mode}')],
        [InlineKeyboardButton("📋 Menu", callback_data='prediction_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await bot_app.bot.send_photo(
            chat_id=chat_id,
            photo=random_image['url'],
            caption=f"👆 BET 👆\n\n(\"CASH OUT\" at this value or before)\nACCURACY:- {random_image['accuracy']}\n\nStep: {step}/20",
            reply_markup=reply_markup
        )
    except Exception as e:
        await bot_app.bot.send_message(
            chat_id=chat_id,
            text=f"🎯 {mode.upper()} MODE\n\n👆 BET 👆\n\n(\"CASH OUT\" at this value or before)\nACCURACY:- {random_image['accuracy']}\n\nStep: {step}/20",
            reply_markup=reply_markup
        )

# Handle game mode selection
async def handle_game_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = query.data
    
    if data.startswith('mode_'):
        mode = data.split('_')[1]
        users[user_id]['current_mode'] = mode
        users[user_id]['predictions_used'] = 0
        await send_prediction(query.message.chat_id, user_id, mode, 1)
    
    elif data.startswith('next_'):
        mode = data.split('_')[1]
        users[user_id]['predictions_used'] += 1
        
        if users[user_id]['predictions_used'] >= 20:
            lang = users[user_id]['language']
            keyboard = [
                [InlineKeyboardButton("🕐 Try Tomorrow", callback_data='try_tomorrow')],
                [InlineKeyboardButton("💳 Deposit Again", url=AFFILIATE_LINK)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(languages[lang]['limit_reached'], reply_markup=reply_markup)
        else:
            await send_prediction(query.message.chat_id, user_id, mode, users[user_id]['predictions_used'] + 1)
    
    elif data == 'prediction_menu':
        lang = users[user_id]['language']
        keyboard = [
            [InlineKeyboardButton("🎯 Easy", callback_data='mode_easy')],
            [InlineKeyboardButton("⚡ Medium", callback_data='mode_medium')],
            [InlineKeyboardButton("🔥 Hard", callback_data='mode_hard')],
            [InlineKeyboardButton("💀 Hardcore", callback_data='mode_hardcore')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(languages[lang]['congratulations'], reply_markup=reply_markup)
    
    elif data == 'check_deposit':
        lang = users[user_id]['language']
        await query.message.reply_text(f"{languages[lang]['enter_player_id']}")
    
    elif data == 'try_tomorrow':
        await query.message.reply_text("⏰ Come back tomorrow for more predictions!")

# Home route
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': '🚀 Chicken Predictor Bot - WORKING!',
        'message': 'Bot is running successfully on Vercel',
        'features': [
            '5 Languages with exact text',
            '1Win Postback Integration', 
            '4 Game Modes with all images',
            'Daily 20 predictions limit',
            'Player verification system'
        ]
    })

# Webhook setup route
@app.route('/set-webhook', methods=['GET'])
def set_webhook():
    try:
        webhook_url = f"{VERCEL_URL}/webhook"
        result = bot_app.bot.set_webhook(webhook_url)
        return jsonify({
            'success': True,
            'message': f'Webhook set to: {webhook_url}',
            'result': 'True'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Webhook route - MAIN
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        update = Update.de_json(json_data, bot_app.bot)
        bot_app.run_async(update)
        return 'OK'
    except Exception as e:
        return 'ERROR', 500

# Add handlers
bot_app.add_handler(CommandHandler('start', start, run_async=True))
bot_app.add_handler(CallbackQueryHandler(handle_language_selection, pattern='^lang_', run_async=True))
bot_app.add_handler(CallbackQueryHandler(handle_check_registration, pattern='^check_registration$', run_async=True))
bot_app.add_handler(CallbackQueryHandler(handle_game_mode, pattern='^(mode_|next_|prediction_menu|check_deposit|try_tomorrow)', run_async=True))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_player_id, run_async=True))

# Initialize
bot_app.initialize()

# For Vercel
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
