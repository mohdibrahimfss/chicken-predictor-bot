import os
import logging
from flask import Flask, request, jsonify
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')
VERCEL_URL = os.environ.get('VERCEL_URL')
AFFILIATE_LINK = os.environ.get('AFFILIATE_LINK', 'https://mostbet-king.com/5rTs')

# Initialize
app = Flask(__name__)

try:
    bot = telegram.Bot(token=BOT_TOKEN)
    logger.info("Bot initialized successfully")
except Exception as e:
    logger.error(f"Bot initialization failed: {e}")
    bot = None

# Storage
users = {}
stats = {"total": 0, "registered": 0, "deposited": 0}
postbackData = {"registrations": {}, "deposits": {}, "approvedDeposits": {}}

# Languages - ALL 5 LANGUAGES WITH EXACT TEXT
languages = {
  "en": {
    "name": "English", "flag": "🇺🇸",
    "welcome": "✅ You selected English!",
    "selectLanguage": "Select your preferred Languages",
    "step1": "🌐 Step 1 - Register",
    "mustNew": "‼️ THE ACCOUNT MUST BE NEW",
    "instructions": "1️⃣ If after clicking the \"REGISTER\" button you get to the old account, you need to log out of it and click the button again.\n\n2️⃣ Specify a promocode during registration: CLAIM\n\n3️⃣ Make a Minimum deposit atleast 600₹ or 6$ in any currency",
    "enterPlayerId": "Please enter your Mostbet Player ID to verify:",
    "howToFind": "📝 How to find Player ID:\n1. Login to Mostbet account\n2. Go to Profile Settings\n3. Copy Player ID number\n4. Paste it here",
    "enterPlayerIdNow": "🔢 Enter your Player ID now:",
    "congratulations": "Congratulations, Please Select Your Game Mode For Play:",
    "notRegistered": "❌ Sorry, You're Not Registered!\n\nPlease click the REGISTER button first and complete your registration using our affiliate link.\n\nAfter successful registration, come back and enter your Player ID.",
    "registeredNoDeposit": "🎉 Great, you have successfully completed registration!\n\n✅ Your account is synchronized with the bot\n\n💴 To gain access to signals, deposit your account (make a deposit) with at least 600₹ or $6 in any currency\n\n🕹️ After successfully replenishing your account, click on the CHECK DEPOSIT button and gain access",
    "limitReached": "You're Reached Your Limited, please try again tommarow for continue prediction or if you want to continue to deposit again atleast 400₹ or 4$ in any currency",
    "checking": "🔍 Checking your registration...",
    "verified": "✅ Verification Successful!",
    "welcomeBack": "👋 Welcome back!"
  },
  "hi": {
    "name": "हिंदी", "flag": "🇮🇳",
    "welcome": "✅ आपने हिंदी चुनी!",
    "selectLanguage": "अपनी पसंदीदा भाषा चुनें",
    "step1": "🌐 स्टेप 1 - रजिस्टर करें",
    "mustNew": "‼️ अकाउंट नया होना चाहिए",
    "instructions": "1️⃣ अगर \"REGISTER\" बटन पर क्लिक करने के बाद आप पुराने अकाउंट में आते हैं, तो लॉग आउट करके फिर से बटन पर क्लिक करें\n\n2️⃣ रजिस्ट्रेशन के दौरान प्रोमोकोड दर्ज करें: CLAIM\n\n3️⃣ न्यूनतम 600₹ या 6$ जमा करें",
    "enterPlayerId": "कृपया सत्यापन के लिए अपना Mostbet Player ID दर्ज करें:",
    "howToFind": "📝 Player ID कैसे ढूंढें:\n1. Mostbet अकाउंट में लॉगिन करें\n2. प्रोफाइल सेटिंग्स पर जाएं\n3. Player ID नंबर कॉपी करें\n4. यहां पेस्ट करें",
    "enterPlayerIdNow": "🔢 अपना Player ID अब दर्ज करें:",
    "congratulations": "बधाई हो, कृपया खेलने के लिए अपना गेम मोड चुनें:",
    "notRegistered": "❌ क्षमा करें, आप रजिस्टर्ड नहीं हैं!\n\nकृपया पहले REGISTER बटन पर क्लिक करें और हमारे एफिलिएट लिंक का उपयोग करके रजिस्ट्रेशन पूरा करें\n\nसफल रजिस्ट्रेशन के बाद वापस आएं और अपना Player ID दर्ज करें",
    "registeredNoDeposit": "🎉 बढ़िया, आपने सफलतापूर्वक रजिस्ट्रेशन पूरा कर लिया है!\n\n✅ आपका अकाउंट बॉट के साथ सिंक हो गया है\n\n💴 सिग्नल तक पहुंच प्राप्त करने के लिए, अपने अकाउंट में कम से कम 600₹ या $6 जमा करें\n\n🕹️ अपना अकाउंट सफलतापूर्वक रिचार्ज करने के बाद, CHECK DEPOSIT बटन पर क्लिक करें और एक्सेस प्राप्त करें",
    "limitReached": "आप अपनी सीमा तक पहुँच गए हैं, कृपया कल फिर से कोशिश करें या जारी रखने के लिए फिर से कम से कम 400₹ या 4$ जमा करें",
    "checking": "🔍 आपकी रजिस्ट्रेशन जांची जा रही है...",
    "verified": "✅ सत्यापन सफल!",
    "welcomeBack": "👋 वापसी पर स्वागत!"
  },
  "bn": {
    "name": "বাংলা", "flag": "🇧🇩",
    "welcome": "✅ আপনি বাংলা নির্বাচন করেছেন!",
    "selectLanguage": "আপনার পছন্দের ভাষা নির্বাচন করুন",
    "step1": "🌐 ধাপ 1 - নিবন্ধন করুন",
    "mustNew": "‼️ অ্যাকাউন্টটি নতুন হতে হবে",
    "instructions": "1️⃣ \"REGISTER\" বাটনে ক্লিক করার পরে যদি আপনি পুরানো অ্যাকাউন্টে প্রবেশ করেন, তাহলে আপনাকে লগআউট করে আবার বাটনে ক্লিক করতে হবে\n\n2️⃣ নিবন্ধনের সময় প্রমোকোড নির্দিষ্ট করুন: CLAIM\n\n3️⃣ ন্যূনতম 600₹ বা 6$ জমা করুন",
    "enterPlayerId": "যাচাই করার জন্য আপনার Mostbet Player ID লিখুন:",
    "howToFind": "📝 Player ID কিভাবে খুঁজে পাবেন:\n1. Mostbet অ্যাকাউন্টে লগইন করুন\n2. প্রোফাইল সেটিংসে যান\n3. Player ID নম্বর কপি করুন\n4. এখানে পেস্ট করুন",
    "enterPlayerIdNow": "🔢 এখন আপনার Player ID লিখুন:",
    "congratulations": "অভিনন্দন, খেলার জন্য আপনার গেম মোড নির্বাচন করুন:",
    "notRegistered": "❌ দুঃখিত, আপনি নিবন্ধিত নন!\n\nঅনুগ্রহ করে প্রথমে REGISTER বাটনে ক্লিক করুন এবং আমাদের অ্যাফিলিয়েট লিঙ্ক ব্যবহার করে নিবন্ধন সম্পূর্ণ করুন\n\nসফল নিবন্ধনের পরে ফিরে আসুন এবং আপনার Player ID লিখুন",
    "registeredNoDeposit": "🎉 দুর্দান্ত, আপনি সফলভাবে নিবন্ধন সম্পূর্ণ করেছেন!\n\n✅ আপনার অ্যাকাউন্ট বটের সাথে সিঙ্ক হয়েছে\n\n💴 সিগন্যাল অ্যাক্সেস পেতে, আপনার অ্যাকাউন্টে কমপক্ষে 600₹ বা $6 জমা করুন\n\n🕹️ আপনার অ্যাউন্ট সফলভাবে রিচার্জ করার পরে, CHECK DEPOSIT বাটনে ক্লিক করুন এবং অ্যাক্সেস পান",
    "limitReached": "আপনি আপনার সীমায় পৌঁছেছেন, অনুগ্রহ করে আগামীকাল আবার চেষ্টা করুন বা চালিয়ে যেতে আবার কমপক্ষে 400₹ বা 4$ জমা করুন",
    "checking": "🔍 আপনার নিবন্ধন পরীক্ষা করা হচ্ছে...",
    "verified": "✅ যাচাইকরণ সফল!",
    "welcomeBack": "👋 ফিরে আসার স্বাগতম!"
  },
  "ur": {
    "name": "اردو", "flag": "🇵🇰",
    "welcome": "✅ آپ نے اردو منتخب کی!",
    "selectLanguage": "اپنی پسندیدہ زبان منتخب کریں",
    "step1": "🌐 مرحلہ 1 - رجسٹر کریں",
    "mustNew": "‼️ اکاؤنٹ نیا ہونا چاہیے",
    "instructions": "1️⃣ اگر \"REGISTER\" بٹن پر کلک کرنے کے بعد آپ پرانے اکاؤنٹ میں آتے ہیں، تو آپ کو لاگ آؤٹ ہو کر دوبارہ بٹن پر کلک کرنا ہوگا\n\n2️⃣ رجسٹریشن کے دوران پروموکوڈ指定 کریں: CLAIM\n\n3️⃣ کم از کم 600₹ یا 6$ جمع کریں",
    "enterPlayerId": "براہ کرم تصدیق کے لیے اپنا Mostbet Player ID درج کریں:",
    "howToFind": "📝 Player ID کیسے ڈھونڈیں:\n1. Mostbet اکاؤنٹ میں لاگ ان کریں\n2. پروفائل سیٹنگز پر جائیں\n3. Player ID نمبر کاپی کریں\n4. یہاں پیسٹ کریں",
    "enterPlayerIdNow": "🔢 اب اپنا Player ID درج کریں:",
    "congratulations": "مبارک ہو، براہ کرم کھیلنے کے لیے اپنا گیم موڈ منتخب کریں:",
    "notRegistered": "❌ معذرت، آپ رجسٹرڈ نہیں ہیں!\n\nبراہ کرم پہلے REGISTER بٹن پر کلک کریں اور ہمارے affiliate link کا استعمال کرتے ہوئے رجسٹریشن مکمل کریں\n\nکامیاب رجسٹریشن کے بعد واپس آئیں اور اپنا Player ID درج کریں",
    "registeredNoDeposit": "🎉 بہت اچھا، آپ نے کامیابی کے ساتھ رجسٹریشن مکمل کر لی ہے!\n\n✅ آپ کا اکاؤنٹ بوٹ کے ساتھ sync ہو گیا ہے\n\n💴 سگنلز تک رسائی حاصل کرنے کے لیے، اپنے اکاؤنٹ میں کم از کم 600₹ یا $6 جمع کریں\n\n🕹️ اپنے اکاؤنٹ کو کامیابی سے ری چارج کرنے کے بعد، CHECK DEPOSIT بٹن پر کلک کریں اور رسائی حاصل کریں",
    "limitReached": "آپ اپنی حد تک پہنچ گئے ہیں، براہ کرم کل دوبارہ کوشش کریں یا جاری رکھنے کے لیے دوبارہ کم از کم 400₹ یا 4$ جمع کریں",
    "checking": "🔍 آپ کی رجسٹریشن چیک کی جا رہی ہے...",
    "verified": "✅ تصدیق کامیاب!",
    "welcomeBack": "👋 واپسی پر خوش آمدید!"
  },
  "ne": {
    "name": "नेपाली", "flag": "🇳🇵",
    "welcome": "✅ तपाईंले नेपाली चयन गर्नुभयो!",
    "selectLanguage": "आफ्नो मनपर्ने भाषा चयन गर्नुहोस्",
    "step1": "🌐 चरण 1 - दर्ता गर्नुहोस्",
    "mustNew": "‼️ खाता नयाँ हुनुपर्छ",
    "instructions": "1️⃣ यदि \"REGISTER\" बटन क्लिक गरेपछि तपाईं पुरानो खातामा पुग्नुहुन्छ भने, तपाईंले लगआउट गरेर फेरि बटन क्लिक गर्नुपर्छ\n\n2️⃣ दर्ता समयमा प्रोमोकोड निर्दिष्ट गर्नुहोस्: CLAIM\n\n3️⃣ कम्तिमा 600₹ वा 6$ जम्मा गर्नुहोस्",
    "enterPlayerId": "कृपया सत्यापन गर्न आफ्नो Mostbet Player ID प्रविष्ट गर्नुहोस्:",
    "howToFind": "📝 Player ID कसरी खोज्ने:\n1. Mostbet खातामा लगइन गर्नुहोस्\n2. प्रोफाइल सेटिङहरूमा जानुहोस्\n3. Player ID नम्बर कपी गर्नुहोस्\n4. यहाँ पेस्ट गर्नुहोस्",
    "enterPlayerIdNow": "🔢 अब आफ्नो Player ID प्रविष्ट गर्नुहोस्:",
    "congratulations": "बधाई छ, कृपया खेल्नको लागि आफ्नो खेल मोड चयन गर्नुहोस्:",
    "notRegistered": "❌ माफ गर्नुहोस्, तपाईं दर्ता गरिएको छैन!\n\nकृपया पहिले REGISTER बटन क्लिक गर्नुहोस् र हाम्रो एफिलिएट लिङ्क प्रयोग गरेर दर्ता पूरा गर्नुहोस्\n\nसफल दर्ता पछि फर्कनहोस् र आफ्नो Player ID प्रविष्ट गर्नुहोस्",
    "registeredNoDeposit": "🎉 राम्रो, तपाईंले सफलतापूर्वक दर्ता पूरा गर्नुभयो!\n\n✅ तपाईंको खाता बोटसँग सिङ्क भएको छ\n\n💴 सिग्नलहरूले पहुँच प्राप्त गर्न, आफ्नो खातामा कम्तिमा 600₹ वा $6 जम्मा गर्नुहोस्\n\n🕹️ आफ्नो खाता सफलतापूर्वक रिचार्ज गरेपछि, CHECK DEPOSIT बटन क्लिक गर्नुहोस् र पहुँच प्राप्त गर्नुहोस्",
    "limitReached": "तपाईं आफ्नो सीमामा पुग्नुभयो, कृपया भोली फेरि प्रयास गर्नुहोस् वा जारी राख्नका लागि फेरि कम्तिमा 400₹ वा 4$ जम्मा गर्नुहोस्",
    "checking": "🔍 तपाईंको दर्ता जाँच गरिदैछ...",
    "verified": "✅ सत्यापन सफल!",
    "welcomeBack": "👋 फर्किनुभएकोमा स्वागत!"
  }
}

# ALL PREDICTION IMAGES
predictionImages = {
 "easy": [
   {"url":"https://i.postimg.cc/dQS5pr0N/IMG-20251020-095836-056.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/P5BxR3GJ/IMG-20251020-095841-479.jpg","accuracy":"95%"},
   {"url":"https://i.postimg.cc/QdWN1QBr/IMG-20251020-095848-018.jpg","accuracy":"78%"},
   {"url":"https://i.postimg.cc/gjJmJ89H/IMG-20251020-095902-112.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/QMJ3J0hQ/IMG-20251020-095906-484.jpg","accuracy":"70%"},
   {"url":"https://i.postimg.cc/654xm9BR/IMG-20251020-095911-311.jpg","accuracy":"80%"},
   {"url":"https://i.postimg.cc/NMCZdnVX/IMG-20251020-095916-536.jpg","accuracy":"82%"},
   {"url":"https://i.postimg.cc/8k3qWqLk/IMG-20251020-095921-307.jpg","accuracy":"88%"},
   {"url":"https://i.postimg.cc/pdqSd72R/IMG-20251020-095926-491.jpg","accuracy":"75%"},
   {"url":"https://i.postimg.cc/05T9x6WH/IMG-20251020-095937-768.jpg","accuracy":"90%"}
 ],
 "medium": [
   {"url":"https://i.postimg.cc/JnJPX4J6/IMG-20251020-104414-537.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/ZnHPP9qJ/IMG-20251020-104430-876.jpg","accuracy":"82%"},
   {"url":"https://i.postimg.cc/Z528LzJ2/IMG-20251020-104435-861.jpg","accuracy":"88%"},
   {"url":"https://i.postimg.cc/tJ4njBXg/IMG-20251020-104439-671.jpg","accuracy":"83%"},
   {"url":"https://i.postimg.cc/dVykwkKH/IMG-20251020-104443-615.jpg","accuracy":"87%"}
 ],
 "hard": [
   {"url":"https://i.postimg.cc/4N8qsy1c/IMG-20251020-105355-761.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/tJ4njBXg/IMG-20251020-104439-671.jpg","accuracy":"82%"},
   {"url":"https://i.postimg.cc/8cpXVgJ4/IMG-20251020-105410-692.jpg","accuracy":"88%"},
   {"url":"https://i.postimg.cc/HsLvZH1t/IMG-20251020-105415-479.jpg","accuracy":"83%"},
   {"url":"https://i.postimg.cc/90gb5RH8/IMG-20251020-105424-630.jpg","accuracy":"87%"}
 ],
 "hardcore": [
   {"url":"https://i.postimg.cc/NMcBmFVb/IMG-20251020-110213-026.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/xjgnN0P6/IMG-20251020-110218-479.jpg","accuracy":"82%"},
   {"url":"https://i.postimg.cc/FsBvGD8p/IMG-20251020-110222-741.jpg","accuracy":"88%"},
   {"url":"https://i.postimg.cc/RVj17zSJ/IMG-20251020-105443-517.jpg","accuracy":"83%"},
   {"url":"https://i.postimg.cc/pTRMy75V/IMG-20251020-110240-031.jpg","accuracy":"87%"}
 ]
}

# Keyboards
def register_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 Register", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("🔍 Check Registration", callback_data='check_registration')]
    ])

def prediction_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Easy", callback_data='mode_easy')],
        [InlineKeyboardButton("⚡ Medium", callback_data='mode_medium')],
        [InlineKeyboardButton("🔥 Hard", callback_data='mode_hard')],
        [InlineKeyboardButton("💀 Hardcore", callback_data='mode_hardcore')],
    ])

def next_menu_keyboard(mode):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➡️ Next", callback_data=f'next_{mode}')],
        [InlineKeyboardButton("📋 Menu", callback_data='prediction_menu')]
    ])

# Initialize dispatcher
if bot:
    dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
else:
    dispatcher = None

# /start command
def start(update, context):
    if not bot: return
    
    user_id = str(update.effective_user.id)
    if user_id not in users:
        users[user_id] = {"language": "en", "predictionsUsed": 0}
        stats["total"] += 1
    
    lang = users[user_id]["language"]
    caption = f"{languages[lang]['step1']}\n\n{languages[lang]['mustNew']}\n\n{languages[lang]['instructions']}"
    
    bot.send_photo(
        chat_id=update.effective_chat.id,
        photo="https://i.postimg.cc/4Nh2kPnv/Picsart-25-10-16-14-41-43-751.jpg",
        caption=caption,
        reply_markup=register_keyboard()
    )

# Language command
def language_cmd(update, context):
    if not bot: return
    
    user_id = str(update.effective_user.id)
    lang = users.get(user_id, {}).get("language", "en")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{l['flag']} {l['name']}", callback_data=f'lang_{code}')]
        for code, l in languages.items()
    ])
    
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=languages[lang]['selectLanguage'],
        reply_markup=keyboard
    )

# Callback handler
def callback_handler(update, context):
    if not bot: return
    
    query = update.callback_query
    data = query.data
    user_id = str(query.from_user.id)
    
    if user_id not in users:
        users[user_id] = {"language": "en", "predictionsUsed": 0}
    
    user = users[user_id]
    lang = user.get("language", "en")
    
    try:
        if data.startswith("lang_"):
            new_lang = data.split("_")[1]
            user["language"] = new_lang
            query.edit_message_text(text=languages[new_lang]["welcome"])
            
        elif data == "check_registration":
            bot.send_message(
                chat_id=query.message.chat_id,
                text=f"{languages[lang]['enterPlayerId']}\n\n{languages[lang]['howToFind']}"
            )
            
        elif data.startswith("mode_"):
            mode = data.split("_")[1]
            user["currentMode"] = mode
            user["predictionsUsed"] = 0
            send_prediction(query.message.chat_id, user_id, mode, 1)
            
        elif data.startswith("next_"):
            mode = data.split("_")[1]
            user["predictionsUsed"] = user.get("predictionsUsed", 0) + 1
            
            if user["predictionsUsed"] >= 20:
                bot.send_message(
                    chat_id=query.message.chat_id,
                    text=languages[lang]["limitReached"]
                )
            else:
                send_prediction(query.message.chat_id, user_id, mode, user["predictionsUsed"] + 1)
                
        elif data == "prediction_menu":
            bot.send_message(
                chat_id=query.message.chat_id,
                text=languages[lang]["congratulations"],
                reply_markup=prediction_menu_keyboard()
            )
            
        query.answer()
    except Exception as e:
        logger.error(f"Callback error: {e}")
        try:
            query.answer()
        except:
            pass

# Send prediction
def send_prediction(chat_id, user_id, mode, step):
    if not bot: return
    
    user = users.get(user_id, {})
    lang = user.get("language", "en")
    images = predictionImages.get(mode, [])
    
    if not images:
        bot.send_message(chat_id=chat_id, text="No predictions available")
        return
        
    import random
    img = random.choice(images)
    caption = f"👆 BET 👆\n\nACCURACY: {img['accuracy']}\nStep: {step}/20"
    
    try:
        bot.send_photo(
            chat_id=chat_id,
            photo=img["url"],
            caption=caption,
            reply_markup=next_menu_keyboard(mode)
        )
    except Exception as e:
        bot.send_message(
            chat_id=chat_id,
            text=f"🎯 {mode.upper()} MODE\n\n{caption}",
            reply_markup=next_menu_keyboard(mode)
        )

# Message handler for Player ID
def message_handler(update, context):
    if not bot: return
    
    text = update.message.text.strip()
    if text.isdigit():
        user_id = str(update.message.from_user.id)
        player_id = text
        
        if user_id not in users:
            users[user_id] = {"language": "en", "predictionsUsed": 0}
            
        user = users[user_id]
        lang = user.get("language", "en")
        
        # Simulate verification
        registration = postbackData["registrations"].get(player_id)
        deposit = postbackData["deposits"].get(player_id)
        
        if registration and deposit:
            user["registered"] = True
            user["deposited"] = True
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{languages[lang]['verified']}\n\n{languages[lang]['congratulations']}",
                reply_markup=prediction_menu_keyboard()
            )
        elif registration:
            user["registered"] = True
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=languages[lang]["registeredNoDeposit"]
            )
        else:
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=languages[lang]["notRegistered"],
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📲 Register Now", url=AFFILIATE_LINK)]
                ])
            )

# Add handlers
if dispatcher:
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("language", language_cmd))
    dispatcher.add_handler(CallbackQueryHandler(callback_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

# Flask routes
@app.route('/webhook', methods=['POST'])
def webhook():
    if not bot: return "Bot not initialized", 500
    
    try:
        update = Update.de_json(request.get_json(), bot)
        dispatcher.process_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return "OK"

@app.route('/lwin-postback', methods=['GET'])
def lwin_postback():
    player_id = request.args.get("player_id")
    status = request.args.get("status")
    amount = request.args.get("amount")
    
    if status == "registration":
        postbackData["registrations"][player_id] = {"status": "registered"}
    elif status == "fdp":
        postbackData["deposits"][player_id] = {"status": "deposited", "amount": amount}
    elif status == "fd_approved":
        postbackData["approvedDeposits"][player_id] = {"status": "approved", "amount": amount}
        
    return jsonify(success=True)

@app.route('/setup-webhook', methods=['GET'])
def setup_webhook():
    if not VERCEL_URL or not bot:
        return jsonify(success=False, error="Configuration missing"), 400
        
    try:
        webhook_url = f"{VERCEL_URL}/webhook"
        bot.set_webhook(webhook_url)
        return jsonify(success=True, message=f"Webhook set to {webhook_url}")
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@app.route('/')
def home():
    return jsonify({
        "status": "🚀 Chicken Predictor Bot - WORKING!",
        "users": stats["total"],
        "features": ["5 Languages", "4 Game Modes", "1Win Integration"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
