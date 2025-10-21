import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
import json
import random
from datetime import datetime
import asyncio

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')
VERCEL_URL = os.environ.get('VERCEL_URL')
AFFILIATE_LINK = os.environ.get('AFFILIATE_LINK', 'https://mostbet-king.com/5w4F')

# Check required variables
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is required!")
if not ADMIN_CHAT_ID:
    raise ValueError("❌ ADMIN_CHAT_ID environment variable is required!")

print("✅ Environment variables loaded successfully!")

app = Flask(__name__)

# Storage
users = {}
stats = {'total': 0, 'registered': 0, 'deposited': 0}
postback_data = {'registrations': {}, 'deposits': {}, 'approved_deposits': {}}

# ALL 5 LANGUAGES - EXACT TEXT
languages = {
    'en': {
        'name': "English", 'flag': "🇺🇸",
        'welcome': "✅ You selected English!",
        'select_language': "Select your preferred Languages",
        'step1': "🌐 Step 1 - Register",
        'must_new': "‼️ THE ACCOUNT MUST BE NEW", 
        'instructions': """1️⃣ If after clicking the "REGISTER" button you get to the old account, you need to log out of it and click the button again.

2️⃣ Specify a promocode during registration: CLAIM

3️⃣ Make a Minimum deposit atleast 600₹ or 6$ in any currency

✅ After REGISTRATION, click the "CHECK REGISTRATION" button""",
        'enter_player_id': "Please enter your Mostbet Player ID to verify:",
        'how_to_find': """📝 How to find Player ID:
1. Login to Mostbet account
2. Go to Profile Settings
3. Copy Player ID number
4. Paste it here""",
        'enter_player_id_now': "🔢 Enter your Player ID now:",
        'congratulations': "Congratulations, Please Select Your Game Mode For Play:",
        'not_registered': """❌ Sorry, You're Not Registered!

Please click the REGISTER button first and complete your registration using our affiliate link.

After successful registration, come back and enter your Player ID.""",
        'registered_no_deposit': """🎉 Great, you have successfully completed registration!

✅ Your account is synchronized with the bot

💴 To gain access to signals, deposit your account (make a deposit) with at least 600₹ or $6 in any currency

🕹️ After successfully replenishing your account, click on the CHECK DEPOSIT button and gain access""",
        'limit_reached': "You're Reached Your Limited, please try again tommarow for continue prediction or if you want to continue to deposit again atleast 400₹ or 4$ in any currency",
        'checking': "🔍 Checking your registration...",
        'verified': "✅ Verification Successful!",
        'welcome_back': "👋 Welcome back!"
    },
    'hi': {
        'name': "हिंदी", 'flag': "🇮🇳",
        'welcome': "✅ आपने हिंदी चुनी!",
        'select_language': "अपनी पसंदीदा भाषा चुनें",
        'step1': "🌐 स्टेप 1 - रजिस्टर करें",
        'must_new': "‼️ अकाउंट नया होना चाहिए",
        'instructions': """1️⃣ अगर "REGISTER" बटन पर क्लिक करने के बाद आप पुराने अकाउंट में आते हैं, तो लॉग आउट करके फिर से बटन पर क्लिक करें

2️⃣ रजिस्ट्रेशन के दौरान प्रोमोकोड दर्ज करें: CLAIM

3️⃣ न्यूनतम 600₹ या 6$ जमा करें

✅ पंजीकरण के बाद, "CHECK REGISTRATION" बटन पर क्लिक करें""",
        'enter_player_id': "कृपया सत्यापन के लिए अपना Mostbet Player ID दर्ज करें:",
        'how_to_find': """📝 Player ID कैसे ढूंढें:
1. Mostbet अकाउंट में लॉगिन करें
2. प्रोफाइल सेटिंग्स पर जाएं
3. Player ID नंबर कॉपी करें
4. यहां पेस्ट करें""",
        'enter_player_id_now': "🔢 अपना Player ID अब दर्ज करें:",
        'congratulations': "बधाई हो, कृपया खेलने के लिए अपना गेम मोड चुनें:",
        'not_registered': """❌ क्षमा करें, आप रजिस्टर्ड नहीं हैं!

कृपया पहले REGISTER बटन पर क्लिक करें और हमारे एफिलिएट लिंक का उपयोग करके रजिस्ट्रेशन पूरा करें

सफल रजिस्ट्रेशन के बाद वापस आएं और अपना Player ID दर्ज करें""",
        'registered_no_deposit': """🎉 बढ़िया, आपने सफलतापूर्वक रजिस्ट्रेशन पूरा कर लिया है!

✅ आपका अकाउंट बॉट के साथ सिंक हो गया है

💴 सिग्नल तक पहुंच प्राप्त करने के लिए, अपने अकाउंट में कम से कम 600₹ या $6 जमा करें

🕹️ अपना अकाउंट सफलतापूर्वक रिचार्ज करने के बाद, CHECK DEPOSIT बटन पर क्लिक करें और एक्सेस प्राप्त करें""",
        'limit_reached': "आप अपनी सीमा तक पहुँच गए हैं, कृपया कल फिर से कोशिश करें या जारी रखने के लिए फिर से कम से कम 400₹ या 4$ जमा करें",
        'checking': "🔍 आपकी रजिस्ट्रेशन जांची जा रही है...",
        'verified': "✅ सत्यापन सफल!",
        'welcome_back': "👋 वापसी पर स्वागत!"
    },
    'bn': {
        'name': "বাংলা", 'flag': "🇧🇩",
        'welcome': "✅ আপনি বাংলা নির্বাচন করেছেন!",
        'select_language': "আপনার পছন্দের ভাষা নির্বাচন করুন",
        'step1': "🌐 ধাপ 1 - নিবন্ধন করুন",
        'must_new': "‼️ অ্যাকাউন্টটি নতুন হতে হবে",
        'instructions': """1️⃣ "REGISTER" বাটনে ক্লিক করার পরে যদি আপনি পুরানো অ্যাকাউন্টে প্রবেশ করেন, তাহলে আপনাকে লগআউট করে আবার বাটনে ক্লিক করতে হবে

2️⃣ নিবন্ধনের সময় প্রমোকোড নির্দিষ্ট করুন: CLAIM

3️⃣ ন্যূনতম 600₹ বা 6$ জমা করুন

✅ রেজিস্ট্রেশনের পর, "CHECK REGISTRATION" বোতামে ক্লিক করুন।""",
        'enter_player_id': "যাচাই করার জন্য আপনার Mostbet Player ID লিখুন:",
        'how_to_find': """📝 Player ID কিভাবে খুঁজে পাবেন:
1. Mostbet অ্যাকাউন্টে লগইন করুন
2. প্রোফাইল সেটিংসে যান
3. Player ID নম্বর কপি করুন
4. এখানে পেস্ট করুন""",
        'enter_player_id_now': "🔢 এখন আপনার Player ID লিখুন:",
        'congratulations': "অভিনন্দন, খেলার জন্য আপনার গেম মোড নির্বাচন করুন:",
        'not_registered': """❌ দুঃখিত, আপনি নিবন্ধিত নন!

অনুগ্রহ করে প্রথমে REGISTER বাটনে ক্লিক করুন এবং আমাদের অ্যাফিলিয়েট লিঙ্ক ব্যবহার করে নিবন্ধন সম্পূর্ণ করুন

সফল নিবন্ধনের পরে ফিরে আসুন এবং আপনার Player ID লিখুন""",
        'registered_no_deposit': """🎉 দুর্দান্ত, আপনি সফলভাবে নিবন্ধন সম্পূর্ণ করেছেন!

✅ আপনার অ্যাকাউন্ট বটের সাথে সিঙ্ক হয়েছে

💴 সিগন্যাল অ্যাক্সেস পেতে, আপনার অ্যাকাউন্টে কমপক্ষে 600₹ বা $6 জমা করুন

🕹️ আপনার অ্যাকাউন্ট সফলভাবে রিচার্জ করার পরে, CHECK DEPOSIT বাটনে ক্লিক করুন এবং অ্যাক্সেস পান""",
        'limit_reached': "আপনি আপনার সীমায় পৌঁছেছেন, অনুগ্রহ করে আগামীকাল আবার চেষ্টা করুন বা চালিয়ে যেতে আবার কমপক্ষে 400₹ বা 4$ জমা করুন",
        'checking': "🔍 আপনার নিবন্ধন পরীক্ষা করা হচ্ছে...",
        'verified': "✅ যাচাইকরণ সফল!",
        'welcome_back': "👋 ফিরে আসার স্বাগতম!"
    },
    'ur': {
        'name': "اردو", 'flag': "🇵🇰",
        'welcome': "✅ آپ نے اردو منتخب کی!",
        'select_language': "اپنی پسندیدہ زبان منتخب کریں",
        'step1': "🌐 مرحلہ 1 - رجسٹر کریں",
        'must_new': "‼️ اکاؤنٹ نیا ہونا چاہیے",
        'instructions': """1️⃣ اگر "REGISTER" بٹن پر کلک کرنے کے بعد آپ پرانے اکاؤنٹ میں آتے ہیں، تو آپ کو لاگ آؤٹ ہو کر دوبارہ بٹن پر کلک کرنا ہوگا

2️⃣ رجسٹریشن کے دوران پروموکوڈ指定 کریں: CLAIM

3️⃣ کم از کم 600₹ یا 6$ جمع کریں

✅ رجسٹریشن کے بعد، "CHECK REGISTRATION" کے بٹن پر کلک کریں۔""",
        'enter_player_id': "براہ کرم تصدیق کے لیے اپنا Mostbet Player ID درج کریں:",
        'how_to_find': """📝 Player ID کیسے ڈھونڈیں:
1. Mostbet اکاؤنٹ میں لاگ ان کریں
2. پروفائل سیٹنگز پر جائیں
3. Player ID نمبر کاپی کریں
4. یہاں پیسٹ کریں""",
        'enter_player_id_now': "🔢 اب اپنا Player ID درج کریں:",
        'congratulations': "مبارک ہو، براہ کرم کھیلنے کے لیے اپنا گیم موڈ منتخب کریں:",
        'not_registered': """❌ معذرت، آپ رجسٹرڈ نہیں ہیں!

براہ کرم پہلے REGISTER بٹن پر کلک کریں اور ہمارے affiliate link کا استعمال کرتے ہوئے رجسٹریشن مکمل کریں

کامیاب رجسٹریشن کے بعد واپس آئیں اور اپنا Player ID درج کریں""",
        'registered_no_deposit': """🎉 بہت اچھا، آپ نے کامیابی کے ساتھ رجسٹریشن مکمل کر لی ہے!

✅ آپ کا اکاؤنٹ بوٹ کے ساتھ sync ہو گیا ہے

💴 سگنلز تک رسائی حاصل کرنے کے لیے، اپنے اکاؤنٹ میں کم از کم 600₹ یا $6 جمع کریں

🕹️ اپنے اکاؤنٹ کو کامیابی سے ری چارج کرنے کے بعد، CHECK DEPOSIT بٹن پر کلک کریں اور رسائی حاصل کریں""",
        'limit_reached': "آپ اپنی حد تک پہنچ گئے ہیں، براہ کرم کل دوبارہ کوشش کریں یا جاری رکھنے کے لیے دوبارہ کم از کم 400₹ یا 4$ جمع کریں",
        'checking': "🔍 آپ کی رجسٹریشن چیک کی جا رہی ہے...",
        'verified': "✅ تصدیق کامیاب!",
        'welcome_back': "👋 واپسی پر خوش آمدید!"
    },
    'ne': {
        'name': "नेपाली", 'flag': "🇳🇵",
        'welcome': "✅ तपाईंले नेपाली चयन गर्नुभयो!",
        'select_language': "आफ्नो मनपर्ने भाषा चयन गर्नुहोस्",
        'step1': "🌐 चरण 1 - दर्ता गर्नुहोस्",
        'must_new': "‼️ खाता नयाँ हुनुपर्छ",
        'instructions': """1️⃣ यदि "REGISTER" बटन क्लिक गरेपछि तपाईं पुरानो खातामा पुग्नुहुन्छ भने, तपाईंले लगआउट गरेर फेरि बटन क्लिक गर्नुपर्छ

2️⃣ दर्ता समयमा प्रोमोकोड निर्दिष्ट गर्नुहोस्: CLAIM

3️⃣ कम्तिमा 600₹ वा 6$ जम्मा गर्नुहोस्

✅ दर्ता पछि, "CHECK REGISTRATION" बटनमा क्लिक गर्नुहोस्।""",
        'enter_player_id': "कृपया सत्यापन गर्न आफ्नो Mostbet Player ID प्रविष्ट गर्नुहोस्:",
        'how_to_find': """📝 Player ID कसरी खोज्ने:
1. Mostbet खातामा लगइन गर्नुहोस्
2. प्रोफाइल सेटिङहरूमा जानुहोस्
3. Player ID नम्बर कपी गर्नुहोस्
4. यहाँ पेस्ट गर्नुहोस्""",
        'enter_player_id_now': "🔢 अब आफ्नो Player ID प्रविष्ट गर्नुहोस्:",
        'congratulations': "बधाई छ, कृपया खेल्नको लागि आफ्नो खेल मोड चयन गर्नुहोस्:",
        'not_registered': """❌ माफ गर्नुहोस्, तपाईं दर्ता गरिएको छैन!

कृपया पहिले REGISTER बटन क्लिक गर्नुहोस् र हाम्रो एफिलिएट लिङ्क प्रयोग गरेर दर्ता पूरा गर्नुहोस्

सफल दर्ता पछि फर्कनुहोस् र आफ्नो Player ID प्रविष्ट गर्नुहोस्""",
        'registered_no_deposit': """🎉 राम्रो, तपाईंले सफलतापूर्वक दर्ता पूरा गर्नुभयो!

✅ तपाईंको खाता बोटसँग सिङ्क भएको छ

💴 सिग्नलहरू पहुँच प्राप्त गर्न, आफ्नो खातामा कम्तिमा 600₹ वा $6 जम्मा गर्नुहोस्

🕹️ आफ्नो खाता सफलतापूर्वक रिचार्ज गरेपछि, CHECK DEPOSIT बटन क्लिक गर्नुहोस् र पहुँच प्राप्त गर्नुहोस्""",
        'limit_reached': "तपाईं आफ्नो सीमामा पुग्नुभयो, कृपया भोली फेरि प्रयास गर्नुहोस् वा जारी राख्नका लागि फेरि कम्तिमा 400₹ वा 4$ जम्मा गर्नुहोस्",
        'checking': "🔍 तपाईंको दर्ता जाँच गरिदैछ...",
        'verified': "✅ सत्यापन सफल!",
        'welcome_back': "👋 फर्किनुभएकोमा स्वागत!"
    }
}

# ALL PREDICTION IMAGES
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

# Initialize Telegram Bot
application = Application.builder().token(BOT_TOKEN).build()

# 1Win Postback
@app.route('/lwin-postback', methods=['GET'])
def lwin_postback():
    player_id = request.args.get('player_id')
    status = request.args.get('status')
    amount = request.args.get('amount', 0)
    
    print(f'📥 1Win Postback: player_id={player_id}, status={status}, amount={amount}')
    
    if status == 'registration':
        postback_data['registrations'][player_id] = {
            'player_id': player_id,
            'status': 'registered',
            'deposited': False,
            'registered_at': datetime.now().isoformat()
        }
        print(f'✅ Registration recorded: {player_id}')
    elif status == 'fdp':
        postback_data['deposits'][player_id] = {
            'player_id': player_id,
            'status': 'deposited',
            'amount': amount,
            'deposited_at': datetime.now().isoformat()
        }
        
        if player_id in postback_data['registrations']:
            postback_data['registrations'][player_id]['deposited'] = True
            postback_data['registrations'][player_id]['deposit_amount'] = amount
        print(f'💰 Deposit recorded: {player_id}, Amount: {amount}')
    elif status == 'fd_approved':
        postback_data['approved_deposits'][player_id] = {
            'player_id': player_id,
            'status': 'approved',
            'amount': amount,
            'approved_at': datetime.now().isoformat()
        }
        print(f'🎉 Deposit approved: {player_id}, Amount: {amount}')
    
    return jsonify({'success': True, 'player_id': player_id, 'status': status})

# Player verification
@app.route('/verify-player/<player_id>', methods=['GET'])
def verify_player(player_id):
    registration = postback_data['registrations'].get(player_id)
    deposit = postback_data['deposits'].get(player_id)
    approved = postback_data['approved_deposits'].get(player_id)
    
    response = {
        'is_registered': bool(registration),
        'has_deposit': bool(deposit),
        'is_approved': bool(approved),
        'registration_data': registration,
        'deposit_data': deposit,
        'approved_data': approved
    }
    
    print(f'🔍 Player verification: {response}')
    return jsonify(response)

# Admin notification - SYNC VERSION
def send_admin_notification_sync(message):
    try:
        # Run async function in sync context
        async def send_async():
            await application.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"🤖 BOT NOTIFICATION\n{message}\n\n📊 STATS:\nTotal Users: {stats['total']}\nRegistered: {stats['registered']}\nDeposited: {stats['deposited']}"
            )
        
        # Run the async function
        asyncio.run(send_async())
    except Exception as e:
        print(f'Admin notification failed: {e}')

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name or 'User'
    
    if user_id not in users:
        users[user_id] = {
            'id': user_id,
            'language': 'en',
            'registered': False,
            'deposited': False,
            'player_id': None,
            'predictions_used': 0,
            'joined_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        stats['total'] += 1
        # Use sync version for admin notification
        send_admin_notification_sync(f"🆕 NEW USER STARTED\nUser: {user_name}\nID: {user_id}\nTotal Users: {stats['total']}")
    else:
        users[user_id]['last_active'] = datetime.now().isoformat()
    
    user = users[user_id]
    lang = user['language']
    
    # Language selection keyboard
    keyboard = [
        [InlineKeyboardButton(f"{languages['en']['flag']} {languages['en']['name']}", callback_data='lang_en')],
        [InlineKeyboardButton(f"{languages['hi']['flag']} {languages['hi']['name']}", callback_data='lang_hi')],
        [InlineKeyboardButton(f"{languages['bn']['flag']} {languages['bn']['name']}", callback_data='lang_bn')],
        [InlineKeyboardButton(f"{languages['ur']['flag']} {languages['ur']['name']}", callback_data='lang_ur')],
        [InlineKeyboardButton(f"{languages['ne']['flag']} {languages['ne']['name']}", callback_data='lang_ne')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        languages[lang]['select_language'],
        reply_markup=reply_markup
    )

# Handle language selection
async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = query.data
    
    if data.startswith('lang_'):
        lang = data.split('_')[1]
        users[user_id]['language'] = lang
        
        await query.edit_message_text(
            languages[lang]['welcome']
        )
        
        # Send registration image with buttons
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
    
    await query.message.reply_text(
        f"{languages[lang]['enter_player_id']}\n\n{languages[lang]['how_to_find']}\n\n{languages[lang]['enter_player_id_now']}"
    )

# Handle player ID input
async def handle_player_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    player_id = update.message.text
    user = users[user_id]
    lang = user['language']
    
    if player_id.isdigit():
        user['player_id'] = player_id
        
        # Send checking message
        checking_msg = await update.message.reply_text(
            languages[lang]['checking']
        )
        
        try:
            # Verify player with postback data
            registration = postback_data['registrations'].get(player_id)
            deposit = postback_data['deposits'].get(player_id)
            approved = postback_data['approved_deposits'].get(player_id)
            
            # Delete checking message
            await checking_msg.delete()
            
            if registration and deposit:
                # User has registration AND deposit
                if not user['registered']:
                    user['registered'] = True
                    user['deposited'] = True
                    stats['registered'] += 1
                    stats['deposited'] += 1
                    send_admin_notification_sync(f"✅ USER REGISTERED & DEPOSITED\nUser ID: {user_id}\nPlayer ID: {player_id}\nAmount: {deposit.get('amount', 'N/A')}")
                
                keyboard = [
                    [InlineKeyboardButton("🎯 Easy", callback_data='mode_easy')],
                    [InlineKeyboardButton("⚡ Medium", callback_data='mode_medium')],
                    [InlineKeyboardButton("🔥 Hard", callback_data='mode_hard')],
                    [InlineKeyboardButton("💀 Hardcore", callback_data='mode_hardcore')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"{languages[lang]['verified']}\n\n{languages[lang]['congratulations']}",
                    reply_markup=reply_markup
                )
                
            elif registration and not deposit:
                # User has registration but NO deposit
                if not user['registered']:
                    user['registered'] = True
                    stats['registered'] += 1
                    send_admin_notification_sync(f"✅ USER REGISTERED\nUser ID: {user_id}\nPlayer ID: {player_id}")
                
                keyboard = [
                    [InlineKeyboardButton("💳 Deposit", url=AFFILIATE_LINK)],
                    [InlineKeyboardButton("🔍 Check Deposit", callback_data='check_deposit')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    languages[lang]['registered_no_deposit'],
                    reply_markup=reply_markup
                )
                
            else:
                # User NOT registered
                keyboard = [
                    [InlineKeyboardButton("📲 Register Now", url=AFFILIATE_LINK)]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    languages[lang]['not_registered'],
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            await checking_msg.delete()
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data='check_registration')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Verification failed. Please try again.",
                reply_markup=reply_markup
            )

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
        await application.bot.send_photo(
            chat_id=chat_id,
            photo=random_image['url'],
            caption=f"👆 BET 👆\n\n(\"CASH OUT\" at this value or before)\nACCURACY:- {random_image['accuracy']}\n\nStep: {step}/20",
            reply_markup=reply_markup
        )
    except Exception as e:
        # Fallback if image fails
        await application.bot.send_message(
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
            
            await query.message.reply_text(
                languages[lang]['limit_reached'],
                reply_markup=reply_markup
            )
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
        
        await query.message.reply_text(
            languages[lang]['congratulations'],
            reply_markup=reply_markup
        )
    
    elif data == 'check_deposit':
        lang = users[user_id]['language']
        await query.message.reply_text(
            f"{languages[lang]['enter_player_id']}\n\n{languages[lang]['how_to_find']}\n\n{languages[lang]['enter_player_id_now']}"
        )
    
    elif data == 'try_tomorrow':
        await query.message.reply_text("⏰ Come back tomorrow for more predictions!")

# Daily motivational messages - SYNC VERSION
def send_daily_messages():
    messages = {
        'en': "You're missing yours chance to win big /start to get Prediction now",
        'hi': "आप बड़ी जीत का मौका गंवा रहे हैं /start से अभी भविष्यवाणी प्राप्त करें",
        'bn': "আপনি বড় জয়ের সুযোগ হারাচ্ছেন /start দিয়ে এখনই ভবিষ্যদ্বাণী পান",
        'ur': "آپ بڑی جیت کا موقع کھو رہے ہیں /start سے ابھی پیشن گوئی حاصل کریں",
        'ne': "तपाईं ठूलो जितको अवसर गुमाउँदै हुनुहुन्छ /start ले अहिले भविष्यवाणी प्राप्त गर्नुहोस्"
    }
    
    for user_id in list(users.keys()):
        try:
            lang = users[user_id]['language']
            # Run async in sync context
            async def send_msg():
                await application.bot.send_message(chat_id=user_id, text=messages.get(lang, messages['en']))
            
            asyncio.run(send_msg())
        except Exception as e:
            # User might have blocked the bot
            del users[user_id]

# Setup scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_messages, 'cron', hour=9, minute=0)
scheduler.start()

# Stats endpoint
@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'bot_stats': stats,
        'postback_stats': {
            'registrations': len(postback_data['registrations']),
            'deposits': len(postback_data['deposits']),
            'approved': len(postback_data['approved_deposits'])
        },
        'user_stats': {
            'total': len(users),
            'registered': len([u for u in users.values() if u['registered']]),
            'deposited': len([u for u in users.values() if u['deposited']])
        }
    })

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
            'Player verification system',
            'Admin notifications'
        ]
    })

# Webhook setup route - SIMPLE VERSION
@app.route('/set-webhook', methods=['GET'])
def set_webhook():
    try:
        webhook_url = f"{VERCEL_URL}/webhook"
        # Simple sync approach
        result = application.bot.set_webhook(webhook_url)
        return jsonify({
            'success': True,
            'message': f'Webhook set to: {webhook_url}',
            'result': 'True'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Webhook route - SIMPLE VERSION  
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        update = Update.de_json(json_data, application.bot)
        
        # Use run_async for better performance
        application.run_async(update)
        return 'OK'
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'ERROR', 500

# Add handlers with run_async
application.add_handler(CommandHandler('start', start, run_async=True))
application.add_handler(CallbackQueryHandler(handle_language_selection, pattern='^lang_', run_async=True))
application.add_handler(CallbackQueryHandler(handle_check_registration, pattern='^check_registration$', run_async=True))
application.add_handler(CallbackQueryHandler(handle_game_mode, pattern='^(mode_|next_|prediction_menu|check_deposit|try_tomorrow)', run_async=True))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_player_id, run_async=True))

# Initialize the application
application.initialize()

# Vercel के लिए app instance export करें
if __name__ == '__main__':
    # Local development के लिए
    app.run(host='0.0.0.0', port=3000, debug=False)
