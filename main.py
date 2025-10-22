import os
import logging
import json
from datetime import datetime
import random

# External Libraries
# Need to install: pip install python-telegram-bot flask requests python-dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from flask import Flask, request, jsonify

# --- Configuration and Storage ---

# Environment variables
# NOTE: Replace with your actual environment variable names if different
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
VERCEL_URL = os.environ.get("VERCEL_URL")
AFFILIATE_LINK = os.environ.get("AFFILIATE_LINK", "https://mostbet-king.com/5rTs")

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory Storage (like in index.js)
users = {}
stats = {"total": 0, "registered": 0, "deposited": 0}
postback_data = {"registrations": {}, "deposits": {}, "approvedDeposits": {}}

# ALL 5 LANGUAGES - EXACT TEXT
languages = {
    # ... (Keep the exact language data block from your index.js here, converted to a Python dictionary) ...
    # Due to space, inserting the full languages dictionary as a placeholder.
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
    # ... (bn, ur, ne follow the exact structure) ...
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
        "registeredNoDeposit": "🎉 দুর্দান্ত, আপনি সফলভাবে নিবন্ধন সম্পূর্ণ করেছেন!\n\n✅ আপনার অ্যাকাউন্ট বটের সাথে সিঙ্ক হয়েছে\n\n💴 সিগন্যাল অ্যাক্সেস পেতে, আপনার অ্যাকাউন্টে কমপক্ষে 600₹ বা $6 জমা করুন\n\n🕹️ আপনার অ্যাকাউন্ট সফলভাবে রিচার্জ করার পরে, CHECK DEPOSIT বাটনে ক্লিক করুন এবং অ্যাক্সেস পান",
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
        "notRegistered": "❌ माफ गर्नुहोस्, तपाईं दर्ता गरिएको छैन!\n\nकृपया पहिले REGISTER बटन क्लिक गर्नुहोस् र हाम्रो एफिलिएट लिङ्क प्रयोग गरेर दर्ता पूरा गर्नुहोस्\n\nसफल दर्ता पछि फर्कनुहोस् र आफ्नो Player ID प्रविष्ट गर्नुहोस्",
        "registeredNoDeposit": "🎉 राम्रो, तपाईंले सफलतापूर्वक दर्ता पूरा गर्नुभयो!\n\n✅ तपाईंको खाता बोटसँग सिङ्क भएको छ\n\n💴 सिग्नलहरू पहुँच प्राप्त गर्न, आफ्नो खातामा कम्तिमा 600₹ वा $6 जम्मा गर्नुहोस्\n\n🕹️ आफ्नो खाता सफलतापूर्वक रिचार्ज गरेपछि, CHECK DEPOSIT बटन क्लिक गर्नुहोस् र पहुँच प्राप्त गर्नुहोस्",
        "limitReached": "तपाईं आफ्नो सीमामा पुग्नुभयो, कृपया भोली फेरि प्रयास गर्नुहोस् वा जारी राख्नका लागि फेरि कम्तिमा 400₹ वा 4$ जम्मा गर्नुहोस्",
        "checking": "🔍 तपाईंको दर्ता जाँच गरिदैछ...",
        "verified": "✅ सत्यापन सफल!",
        "welcomeBack": "👋 फर्किनुभएकोमा स्वागत!"
    }
}


# ALL PREDICTION IMAGES - EXACT LINKS
prediction_images = {
    # ... (Keep the exact prediction_images data block from your index.js here, converted to a Python dictionary) ...
    # Due to space, inserting the full prediction_images dictionary as a placeholder.
    "easy": [
        {"url": "https://i.postimg.cc/dQS5pr0N/IMG-20251020-095836-056.jpg", "accuracy": "85%"},
        {"url": "https://i.postimg.cc/P5BxR3GJ/IMG-20251020-095841-479.jpg", "accuracy": "95%"},
        {"url": "https://i.postimg.cc/QdWN1QBr/IMG-20251020-095848-018.jpg", "accuracy": "78%"},
        {"url": "https://i.postimg.cc/gjJmJ89H/IMG-20251020-095902-112.jpg", "accuracy": "85%"},
        {"url": "https://i.postimg.cc/QMJ3J0hQ/IMG-20251020-095906-484.jpg", "accuracy": "70%"},
        {"url": "https://i.postimg.cc/654xm9BR/IMG-20251020-095911-311.jpg", "accuracy": "80%"},
        {"url": "https://i.postimg.cc/NMCZdnVX/IMG-20251020-095916-536.jpg", "accuracy": "82%"},
        {"url": "https://i.postimg.cc/8k3qWqLk/IMG-20251020-095921-307.jpg", "accuracy": "88%"},
        {"url": "https://i.postimg.cc/pdqSd72R/IMG-20251020-095926-491.jpg", "accuracy": "75%"},
        {"url": "https://i.postimg.cc/05T9x6WH/IMG-20251020-095937-768.jpg", "accuracy": "90%"},
        {"url": "https://i.postimg.cc/CKrV2dnv/IMG-20251020-095949-124.jpg", "accuracy": "83%"},
        {"url": "https://i.postimg.cc/L5dGdP9Y/IMG-20251020-100002-472.jpg", "accuracy": "86%"},
        {"url": "https://i.postimgimg.cc/25MKvWBg/IMG-20251020-100012-671.jpg", "accuracy": "81%"},
        {"url": "https://i.postimg.cc/4ybLrF2D/IMG-20251020-100023-691.jpg", "accuracy": "87%"},
        {"url": "https://i.postimg.cc/vZmqNhrP/IMG-20251020-100033-810.jpg", "accuracy": "84%"},
        {"url": "https://i.postimg.cc/8cDwBmk3/IMG-20251020-100038-185.jpg", "accuracy": "77%"},
        {"url": "https://i.postimg.cc/7YKX0zFL/IMG-20251020-100045-990.jpg", "accuracy": "89%"},
        {"url": "https://i.postimg.cc/ZRzL4xNb/IMG-20251020-100053-162.jpg", "accuracy": "76%"},
        {"url": "https://i.postimg.cc/9QvdYYJb/IMG-20251020-100113-609.jpg", "accuracy": "91%"}
    ],
    "medium": [
        {"url": "https://i.postimg.cc/JnJPX4J6/IMG-20251020-104414-537.jpg", "accuracy": "85%"},
        {"url": "https://i.postimg.cc/ZnHPP9qJ/IMG-20251020-104430-876.jpg", "accuracy": "82%"},
        {"url": "https://i.postimg.cc/Z528LzJ2/IMG-20251020-104435-861.jpg", "accuracy": "88%"},
        {"url": "https://i.postimg.cc/tJ4njBXg/IMG-20251020-104439-671.jpg", "accuracy": "83%"},
        {"url": "https://i.postimg.cc/dVykwkKH/IMG-20251020-104443-615.jpg", "accuracy": "87%"},
        {"url": "https://i.postimg.cc/MHHH4XDw/IMG-20251020-104452-202.jpg", "accuracy": "84%"},
        {"url": "https://i.postimg.cc/6pn3FkdL/IMG-20251020-104458-282.jpg", "accuracy": "86%"},
        {"url": "https://i.postimg.cc/85PzJsqD/IMG-20251020-104509-839.jpg", "accuracy": "81%"},
        {"url": "https://i.postimg.cc/bN2N27Vm/IMG-20251020-104521-438.jpg", "accuracy": "89%"},
        {"url": "https://i.postimg.cc/0NZ8sPrV/IMG-20251020-104526-899.jpg", "accuracy": "85%"},
        {"url": "https://i.postimg.cc/T2KWCHHs/IMG-20251020-104532-810.jpg", "accuracy": "82%"},
        {"url": "https://i.postimg.cc/ZqYW3fdX/IMG-20251020-104537-998.jpg", "accuracy": "88%"},
        {"url": "https://i.postimg.cc/wxR7hR7w/IMG-20251020-104543-014.jpg", "accuracy": "83%"},
        {"url": "https://i.postimg.cc/3x1RKgcx/IMG-20251020-104615-327.jpg", "accuracy": "87%"}
    ],
    "hard": [
        {"url": "https://i.postimg.cc/4N8qsy1c/IMG-20251020-105355-761.jpg", "accuracy": "85%"},
        {"url": "https://i.postimg.cc/tJ4njBXg/IMG-20251020-104439-671.jpg", "accuracy": "82%"},
        {"url": "https://i.postimg.cc/8cpXVgJ4/IMG-20251020-105410-692.jpg", "accuracy": "88%"},
        {"url": "https://i.postimg.cc/HsLvZH1t/IMG-20251020-105415-479.jpg", "accuracy": "83%"},
        {"url": "https://i.postimg.cc/90gb5RH8/IMG-20251020-105424-630.jpg", "accuracy": "87%"},
        {"url": "https://i.postimg.cc/HL12g1F1/IMG-20251020-105428-916.jpg", "accuracy": "84%"},
        {"url": "https://i.postimg.cc/hjpbTzvJ/IMG-20251020-105436-994.jpg", "accuracy": "86%"},
        {"url": "https://i.postimg.cc/RVj17zSJ/IMG-20251020-105443-517.jpg", "accuracy": "81%"},
        {"url": "https://i.postimg.cc/bJN1yygc/IMG-20251020-105450-320.jpg", "accuracy": "89%"},
        {"url": "https://i.postimg.cc/DfSBL6Q8/IMG-20251020-105458-348.jpg", "accuracy": "85%"},
        {"url": "https://i.postimg.cc/zDHFVB5B/IMG-20251020-105512-639.jpg", "accuracy": "82%"}
    ],
    "hardcore": [
        {"url": "https://i.postimg.cc/NMcBmFVb/IMG-20251020-110213-026.jpg", "accuracy": "85%"},
        {"url": "https://i.postimg.cc/xjgnN0P6/IMG-20251020-110218-479.jpg", "accuracy": "82%"},
        {"url": "https://i.postimg.cc/FsBvGD8p/IMG-20251020-110222-741.jpg", "accuracy": "88%"},
        {"url": "https://i.postimg.cc/RVj17zSJ/IMG-20251020-105443-517.jpg", "accuracy": "83%"},
        {"url": "https://i.postimg.cc/pTRMy75V/IMG-20251020-110240-031.jpg", "accuracy": "87%"},
        {"url": "https://i.postimg.cc/VvZxGkGs/IMG-20251020-110255-468.jpg", "accuracy": "84%"}
    ]
}


# --- Utility Functions ---

def get_user_data(user_id):
    """Retrieves or initializes user data."""
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {
            "id": user_id_str,
            "language": "en",
            "registered": False,
            "deposited": False,
            "playerId": None,
            "predictionsUsed": 0,
            "joinedAt": datetime.now().isoformat(),
            "lastActive": datetime.now().isoformat(),
        }
        stats["total"] += 1
    users[user_id_str]["lastActive"] = datetime.now().isoformat()
    return users[user_id_str]

async def send_admin_notification(application, message):
    """Sends a notification to the admin chat ID."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID not set. Skipping admin notification.")
        return

    notification_text = (
        f"🤖 BOT NOTIFICATION\n{message}\n\n"
        f"📊 STATS:\nTotal Users: {stats['total']}\n"
        f"Registered: {stats['registered']}\n"
        f"Deposited: {stats['deposited']}"
    )
    try:
        await application.bot.send_message(
            chat_id=ADMIN_CHAT_ID, text=notification_text
        )
    except Exception as e:
        logger.error(f"Admin notification failed: {e}")

async def send_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, mode, step):
    """Sends a prediction message with an image and controls."""
    chat_id = update.effective_chat.id
    user = users[str(user_id)]
    lang = user["language"]
    mode_images = prediction_images.get(mode, [])
    
    if not mode_images:
        await context.bot.send_message(chat_id, "Error: Invalid game mode.")
        return
        
    random_image = random.choice(mode_images)

    caption = (
        f"👆 BET 👆\n\n(\"CASH OUT\" at this value or before)\n"
        f"ACCURACY:- {random_image['accuracy']}\n\nStep: {step}/20"
    )

    keyboard = [
        [InlineKeyboardButton("➡️ Next", callback_data=f"next_{mode}")],
        [InlineKeyboardButton("📋 Menu", callback_data="prediction_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_photo(
            chat_id, 
            photo=random_image["url"], 
            caption=caption, 
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to send photo: {e}. Sending text fallback.")
        # Fallback if image fails (similar to Node.js code)
        fallback_caption = f"🎯 {mode.upper()} MODE\n\n{caption}"
        await context.bot.send_message(chat_id, fallback_caption, reply_markup=reply_markup)

# --- Telegram Bot Handlers (Replacing Node.js bot.onText and bot.on) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    user = get_user_data(user_id)
    lang = user["language"]
    
    if stats["total"] == 1 and users[str(user_id)]["joinedAt"] == users[str(user_id)]["lastActive"]:
        # New user logic (approximate, since stat count is global)
        await send_admin_notification(
            context.application,
            f"🆕 NEW USER STARTED\nUser: {user_name}\nID: {user_id}\nTotal Users: {stats['total']}",
        )
    
    caption = (
        f"{languages[lang]['step1']}\n\n{languages[lang]['mustNew']}\n\n"
        f"{languages[lang]['instructions']}"
    )
    
    keyboard = [
        [InlineKeyboardButton("📲 Register", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("🔍 Check Registration", callback_data="check_registration")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send registration image with buttons - EXACT FROM YOUR MESSAGE
    await update.message.reply_photo(
        "https://i.postimg.cc/4Nh2kPnv/Picsart-25-10-16-14-41-43-751.jpg",
        caption=caption,
        reply_markup=reply_markup,
    )

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /language command."""
    user_id = str(update.effective_user.id)
    user = get_user_data(user_id)
    lang = user["language"]
    
    keyboard = [
        [InlineKeyboardButton(f"{languages['en']['flag']} {languages['en']['name']}", callback_data="lang_en")],
        [InlineKeyboardButton(f"{languages['hi']['flag']} {languages['hi']['name']}", callback_data="lang_hi")],
        [InlineKeyboardButton(f"{languages['bn']['flag']} {languages['bn']['name']}", callback_data="lang_bn")],
        [InlineKeyboardButton(f"{languages['ur']['flag']} {languages['ur']['name']}", callback_data="lang_ur")],
        [InlineKeyboardButton(f"{languages['ne']['flag']} {languages['ne']['name']}", callback_data="lang_ne")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(languages[lang]["selectLanguage"], reply_markup=reply_markup)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all inline keyboard button presses."""
    query = update.callback_query
    await query.answer() # Acknowledge the query
    data = query.data
    user_id = str(query.from_user.id)
    user = get_user_data(user_id)
    lang = user["language"]
    chat_id = query.message.chat_id

    try:
        if data.startswith("lang_"):
            new_lang = data.split("_")[1]
            user["language"] = new_lang
            
            await query.edit_message_text(languages[new_lang]["welcome"])

            # Send registration image with buttons
            caption = (
                f"{languages[new_lang]['step1']}\n\n{languages[new_lang]['mustNew']}\n\n"
                f"{languages[new_lang]['instructions']}"
            )
            keyboard = [
                [InlineKeyboardButton("📲 Register", url=AFFILIATE_LINK)],
                [InlineKeyboardButton("🔍 Check Registration", callback_data="check_registration")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_photo(
                chat_id,
                "https://i.postimg.cc/4Nh2kPnv/Picsart-25-10-16-14-41-43-751.jpg",
                caption=caption,
                reply_markup=reply_markup,
            )

        elif data == "check_registration" or data == "check_deposit":
            await context.bot.send_message(
                chat_id,
                f"{languages[lang]['enterPlayerId']}\n\n"
                f"{languages[lang]['howToFind']}\n\n"
                f"{languages[lang]['enterPlayerIdNow']}",
            )

        elif data.startswith("mode_"):
            mode = data.split("_")[1]
            user["currentMode"] = mode
            user["predictionsUsed"] = 0
            
            await send_prediction(update, context, user_id, mode, 1)

        elif data.startswith("next_"):
            mode = data.split("_")[1]
            user["predictionsUsed"] += 1
            
            if user["predictionsUsed"] >= 20:
                keyboard = [
                    [InlineKeyboardButton("🕐 Try Tomorrow", callback_data="try_tomorrow")],
                    [InlineKeyboardButton("💳 Deposit Again", url=AFFILIATE_LINK)],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(
                    chat_id, languages[lang]["limitReached"], reply_markup=reply_markup
                )
            else:
                await send_prediction(update, context, user_id, mode, user["predictionsUsed"] + 1)
        
        elif data == 'prediction_menu':
            keyboard = [
                [InlineKeyboardButton("🎯 Easy", callback_data="mode_easy")],
                [InlineKeyboardButton("⚡ Medium", callback_data="mode_medium")],
                [InlineKeyboardButton("🔥 Hard", callback_data="mode_hard")],
                [InlineKeyboardButton("💀 Hardcore", callback_data="mode_hardcore")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id, languages[lang]["congratulations"], reply_markup=reply_markup
            )

        elif data == 'try_tomorrow':
            await context.bot.send_message(chat_id, "⏰ Come back tomorrow for more predictions!")

    except Exception as e:
        logger.error(f"Callback error: {e}")
        # Note: In python-telegram-bot, edit_message_text fails if the content is identical.
        # We rely on query.answer() and subsequent messages for flow.

async def handle_player_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages that look like a Player ID (digits only)."""
    message_text = update.message.text
    if not message_text.isdigit():
        return # Ignore non-digit messages here

    user_id = str(update.effective_user.id)
    player_id = message_text
    user = get_user_data(user_id)
    lang = user["language"]

    user["playerId"] = player_id

    loading_msg = await update.message.reply_text(languages[lang]["checking"])

    try:
        # Verify player with postback data
        registration = postback_data["registrations"].get(player_id)
        deposit = postback_data["deposits"].get(player_id)
        # approved is not strictly used in your Node.js flow here, but kept for completeness
        
        await context.bot.delete_message(update.effective_chat.id, loading_msg.message_id)

        if registration and deposit:
            # User has registration AND deposit
            if not user["registered"]:
                user["registered"] = True
                user["deposited"] = True
                stats["registered"] += 1
                stats["deposited"] += 1
                await send_admin_notification(
                    context.application,
                    f"✅ USER REGISTERED & DEPOSITED\nUser ID: {user_id}\nPlayer ID: {player_id}\nAmount: {deposit.get('amount', 'N/A')}",
                )

            keyboard = [
                [InlineKeyboardButton("🎯 Easy", callback_data="mode_easy")],
                [InlineKeyboardButton("⚡ Medium", callback_data="mode_medium")],
                [InlineKeyboardButton("🔥 Hard", callback_data="mode_hard")],
                [InlineKeyboardButton("💀 Hardcore", callback_data="mode_hardcore")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"{languages[lang]['verified']}\n\n{languages[lang]['congratulations']}",
                reply_markup=reply_markup,
            )

        elif registration and not deposit:
            # User has registration but NO deposit
            if not user["registered"]:
                user["registered"] = True
                stats["registered"] += 1
                await send_admin_notification(
                    context.application,
                    f"✅ USER REGISTERED\nUser ID: {user_id}\nPlayer ID: {player_id}",
                )

            keyboard = [
                [InlineKeyboardButton("💳 Deposit", url=AFFILIATE_LINK)],
                [InlineKeyboardButton("🔍 Check Deposit", callback_data="check_deposit")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                languages[lang]["registeredNoDeposit"], reply_markup=reply_markup
            )

        else:
            # User NOT registered
            keyboard = [
                [InlineKeyboardButton("📲 Register Now", url=AFFILIATE_LINK)],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                languages[lang]["notRegistered"], reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Player ID verification error: {e}")
        await context.bot.delete_message(update.effective_chat.id, loading_msg.message_id)
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data="check_registration")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ Verification failed. Please try again.", reply_markup=reply_markup
        )

# --- Flask Server (Webhooks and Postbacks) ---

app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# Initialize handlers with the application
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("language", language_command))
application.add_handler(CallbackQueryHandler(callback_handler))
# This handles all non-command, non-callback messages that are digits
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_player_id_input))

@app.route("/lwin-postback", methods=["GET"])
def lwin_postback():
    """Handles the 1Win Postback endpoint."""
    player_id = request.args.get("player_id")
    status = request.args.get("status")
    amount = request.args.get("amount")
    
    if not player_id or not status:
        return jsonify({"success": False, "message": "Missing player_id or status"}), 400

    logger.info(f"📥 1Win Postback: {{'player_id': {player_id}, 'status': {status}, 'amount': {amount}}}")

    current_time = datetime.now().isoformat()
    
    if status == "registration":
        postback_data["registrations"][player_id] = {
            "player_id": player_id,
            "status": "registered",
            "deposited": False,
            "registeredAt": current_time,
        }
        logger.info(f"✅ Registration recorded: {player_id}")
    elif status == "fdp":
        postback_data["deposits"][player_id] = {
            "player_id": player_id,
            "status": "deposited",
            "amount": amount or 0,
            "depositedAt": current_time,
        }
        if player_id in postback_data["registrations"]:
            postback_data["registrations"][player_id]["deposited"] = True
            postback_data["registrations"][player_id]["depositAmount"] = amount or 0
        logger.info(f"💰 Deposit recorded: {player_id}, Amount: {amount}")
    elif status == "fd_approved":
        postback_data["approvedDeposits"][player_id] = {
            "player_id": player_id,
            "status": "approved",
            "amount": amount or 0,
            "approvedAt": current_time,
        }
        logger.info(f"🎉 Deposit approved: {player_id}, Amount: {amount}")
    
    return jsonify({"success": True, "player_id": player_id, "status": status})

@app.route("/verify-player/<player_id>", methods=["GET"])
def verify_player(player_id):
    """Player verification endpoint (same as Node.js)."""
    registration = postback_data["registrations"].get(player_id)
    deposit = postback_data["deposits"].get(player_id)
    approved = postback_data["approvedDeposits"].get(player_id)
    
    response = {
        "isRegistered": bool(registration),
        "hasDeposit": bool(deposit),
        "isApproved": bool(approved),
        "registrationData": registration,
        "depositData": deposit,
        "approvedData": approved,
    }
    
    logger.info(f"🔍 Player verification: {response}")
    return jsonify(response)

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Main Telegram Webhook endpoint."""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.update_queue.put(update)
        return jsonify({"status": "ok"})
    return "Method Not Allowed", 405

@app.route("/setup-webhook", methods=["GET"])
async def setup_webhook_route():
    """Manual webhook setup route."""
    if not VERCEL_URL:
        return jsonify({"success": False, "error": "VERCEL_URL not set"}), 500

    webhook_url = f"{VERCEL_URL}/webhook"
    try:
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set: {webhook_url}")
        return jsonify({"success": True, "message": "Webhook set successfully"})
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/stats", methods=["GET"])
def get_stats():
    """Stats endpoint."""
    return jsonify({
        "botStats": stats,
        "postbackStats": {
            "registrations": len(postback_data["registrations"]),
            "deposits": len(postback_data["deposits"]),
            "approved": len(postback_data["approvedDeposits"]),
        },
        "userStats": {
            "total": len(users),
            "registered": len([u for u in users.values() if u["registered"]]),
            "deposited": len([u for u in users.values() if u["deposited"]]),
        }
    })

@app.route("/", methods=["GET"])
def home_route():
    """Home route for health check."""
    return jsonify({
        "status": "🚀 Chicken Predictor Bot - FULLY WORKING (Python/Flask)",
        "message": "All features working with EXACT text from your requirements",
        "features": [
            "5 Languages with exact text",
            "1Win Postback Integration",
            "4 Game Modes with all images",
            "Daily 20 predictions limit (Logic in bot, reset function separate)",
            "Player verification system",
            "Admin notifications",
            "Webhooks via Flask"
        ]
    })

# --- Cron Job / Scheduled Task (Simulated) ---

# Note: Vercel does not reliably run cron jobs. You would typically use a separate
# scheduled service (like cron-job.org or AWS EventBridge/Lambda) to hit a
# dedicated endpoint, or run a separate worker process.
# We include the *logic* here in a function.

async def daily_motivational_messages(application: Application):
    """Sends daily motivational messages."""
    messages = {
        "en": "You're missing yours chance to win big /start to get Prediction now",
        "hi": "आप बड़ी जीत का मौका गंवा रहे हैं /start से अभी भविष्यवाणी प्राप्त करें",
        "bn": "আপনি বড় জয়ের সুযোগ হারাচ্ছেন /start দিয়ে এখনই ভবিষ্যদ্বাণী পান",
        "ur": "آپ بڑی جیت کا موقع کھو رہے ہیں /start سے ابھی پیشن گوئی حاصل کریں",
        "ne": "तपाईं ठूलो जितको अवसर गुमाउँदै हुनुहुन्छ /start ले अहिले भविष्यवाणी प्राप्त गर्नुहोस्"
    }
    
    logger.info("Running daily motivational message sender.")
    
    # Reset predictionsUsed for all users as part of the daily routine
    for user_id in list(users.keys()):
        users[user_id]["predictionsUsed"] = 0 
        
    for user_id, user_data in list(users.items()): # Iterate on a copy in case of deletion
        try:
            lang = user_data["language"]
            message_text = messages.get(lang) or messages["en"]
            await application.bot.send_message(user_id, message_text)
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}. Deleting user. Error: {e}")
            del users[user_id] # User might have blocked the bot

@app.route("/cron-daily-reset-and-message", methods=["GET"])
async def cron_endpoint():
    """A dedicated endpoint to be hit by an external cron service (e.g., at 09:00 UTC)."""
    # This simulates the cron logic from the Node.js code
    await daily_motivational_messages(application)
    return jsonify({"success": True, "message": "Daily cron task completed."})


# --- Initialization (main function) ---

async def init_webhook():
    """Sets up the initial webhook if VERCEL_URL is available."""
    if VERCEL_URL:
        await application.bot.set_webhook(url=f"{VERCEL_URL}/webhook")
        logger.info(f"✅ Webhook set: {VERCEL_URL}/webhook")
    else:
        logger.error("VERCEL_URL not set. Webhook setup skipped.")

# Run the initialization
if VERCEL_URL:
    # Use the asynchronous version of init_webhook before running the app
    import asyncio
    asyncio.run(init_webhook())
    
# NOTE: Vercel requires the app object to be imported and run by its internal server.
# The `application.run_polling()` or `app.run()` part is typically handled by Vercel.
# We just need to expose the `app` object.

# If running locally for testing:
# if __name__ == "__main__":
#     application.run_polling(poll_interval=1.0) # For local polling mode
#     app.run(port=os.environ.get("PORT", 3000)) # For local webhook mode (requires tunneling)
