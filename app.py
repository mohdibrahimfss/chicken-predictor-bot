# app.py
import os
import logging
import requests
from flask import Flask, request, jsonify

# ----------------------------------------
# Basic setup
# ----------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # required
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # optional, for test notifications
VERCEL_URL = os.environ.get("VERCEL_URL")  # optional but helpful
AFFILIATE_LINK = os.environ.get("AFFILIATE_LINK", "https://mostbet-king.com/5rTs")

if not BOT_TOKEN:
    logger.warning("BOT_TOKEN is not set. Telegram functionality will fail until BOT_TOKEN is provided.")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ----------------------------------------
# Languages & texts (exact as provided)
# ----------------------------------------
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
    "notRegistered": "❌ माफ गर्नुहोस्, तपाईं दर्ता गरिएको छैन!\n\nकृपया पहिले REGISTER बटन क्लिक गर्नुहोस् र हाम्रो एफिलिएट लिङ्क प्रयोग गरेर दर्ता पूरा गर्नुहोस्\n\nसफल दर्ता पछि फर्कनहोस् र आफ्नो Player ID प्रविष्ट गर्नुहोस्",
    "registeredNoDeposit": "🎉 राम्रो, तपाईंले सफलतापूर्वक दर्ता पूरा गर्नुभयो!\n\n✅ तपाईंको खाता बोटसँग सिङ्क भएको छ\n\n💴 सिग्नलहरूले पहुँच प्राप्त गर्न, आफ्नो खातामा कम्तिमा 600₹ वा $6 जम्मा गर्नुहोस्\n\n🕹️ आफ्नो खाता सफलतापूर्वक रिचार्ज गरेपछि, CHECK DEPOSIT बटन क्लिक गर्नुहोस् र पहुँच प्राप्त गर्नुहोस्",
    "limitReached": "तपाईं आफ्नो सीमामा पुग्नुभयो, कृपया भोली फेरि प्रयास गर्नुहोस् वा जारी राख्नका लागि फेरि कम्तिमा 400₹ वा 4$ जम्मा गर्नुहोस्",
    "checking": "🔍 तपाईंको दर्ता जाँच गरिदैछ...",
    "verified": "✅ सत्यापन सफल!",
    "welcomeBack": "👋 फर्किनुभएकोमा स्वागत!"
  }
}

# ----------------------------------------
# Prediction images (as provided)
# ----------------------------------------
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
   {"url":"https://i.postimg.cc/05T9x6WH/IMG-20251020-095937-768.jpg","accuracy":"90%"},
   {"url":"https://i.postimg.cc/CKrV2dnv/IMG-20251020-095949-124.jpg","accuracy":"83%"},
   {"url":"https://i.postimg.cc/L5dGdP9Y/IMG-20251020-095954-011.jpg","accuracy":"79%"},
   {"url":"https://i.postimg.cc/FHF8QN4f/IMG-20251020-100002-472.jpg","accuracy":"86%"},
   {"url":"https://i.postimg.cc/25MKvWBg/IMG-20251020-100012-671.jpg","accuracy":"81%"},
   {"url":"https://i.postimg.cc/4ybLrF2D/IMG-20251020-100023-691.jpg","accuracy":"87%"},
   {"url":"https://i.postimg.cc/vZmqNhrP/IMG-20251020-100033-810.jpg","accuracy":"84%"},
   {"url":"https://i.postimg.cc/8cDwBmk3/IMG-20251020-100038-185.jpg","accuracy":"77%"},
   {"url":"https://i.postimg.cc/7YKX0zFL/IMG-20251020-100045-990.jpg","accuracy":"89%"},
   {"url":"https://i.postimg.cc/ZRzL4xNb/IMG-20251020-100053-162.jpg","accuracy":"76%"},
   {"url":"https://i.postimg.cc/9QvdYYJb/IMG-20251020-100113-609.jpg","accuracy":"91%"}
 ],
 "medium": [
   {"url":"https://i.postimg.cc/JnJPX4J6/IMG-20251020-104414-537.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/ZnHPP9qJ/IMG-20251020-104430-876.jpg","accuracy":"82%"},
   {"url":"https://i.postimg.cc/Z528LzJ2/IMG-20251020-104435-861.jpg","accuracy":"88%"},
   {"url":"https://i.postimg.cc/tJ4njBXg/IMG-20251020-104439-671.jpg","accuracy":"83%"},
   {"url":"https://i.postimg.cc/dVykwkKH/IMG-20251020-104443-615.jpg","accuracy":"87%"},
   {"url":"https://i.postimg.cc/MHHH4XDw/IMG-20251020-104452-202.jpg","accuracy":"84%"},
   {"url":"https://i.postimg.cc/6pn3FkdL/IMG-20251020-104498-282.jpg","accuracy":"86%"},
   {"url":"https://i.postimg.cc/85PzJsqD/IMG-20251020-104509-839.jpg","accuracy":"81%"},
   {"url":"https://i.postimg.cc/bN2N27Vm/IMG-20251020-104521-438.jpg","accuracy":"89%"},
   {"url":"https://i.postimg.cc/0NZ8sPrV/IMG-20251020-104526-899.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/T2KWCHHs/IMG-20251020-104532-810.jpg","accuracy":"82%"},
   {"url":"https://i.postimg.cc/ZqYW3fdX/IMG-20251020-104537-998.jpg","accuracy":"88%"},
   {"url":"https://i.postimg.cc/wxR7hR7w/IMG-20251020-104543-014.jpg","accuracy":"83%"},
   {"url":"https://i.postimg.cc/3x1RKgcx/IMG-20251020-104615-327.jpg","accuracy":"87%"}
 ],
 "hard": [
   {"url":"https://i.postimg.cc/4N8qsy1c/IMG-20251020-105355-761.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/tJ4njBXg/IMG-20251020-104439-671.jpg","accuracy":"82%"},
   {"url":"https://i.postimg.cc/8cpXVgJ4/IMG-20251020-105410-692.jpg","accuracy":"88%"},
   {"url":"https://i.postimg.cc/HsLvZH1t/IMG-20251020-105415-479.jpg","accuracy":"83%"},
   {"url":"https://i.postimg.cc/90gb5RH8/IMG-20251020-105424-630.jpg","accuracy":"87%"},
   {"url":"https://i.postimg.cc/HL12g1F1/IMG-20251020-105428-916.jpg","accuracy":"84%"},
   {"url":"https://i.postimg.cc/hjpbTzvJ/IMG-20251020-105436-994.jpg","accuracy":"86%"},
   {"url":"https://i.postimg.cc/RVj17zSJ/IMG-20251020-105443-517.jpg","accuracy":"81%"},
   {"url":"https://i.postimg.cc/bJN1yygc/IMG-20251020-105450-320.jpg","accuracy":"89%"},
   {"url":"https://i.postimg.cc/DfSBL6Q8/IMG-20251020-105458-348.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/zDHFVB5B/IMG-20251020-105512-639.jpg","accuracy":"82%"}
 ],
 "hardcore": [
   {"url":"https://i.postimg.cc/NMcBmFVb/IMG-20251020-110213-026.jpg","accuracy":"85%"},
   {"url":"https://i.postimg.cc/xjgnN0P6/IMG-20251020-110218-479.jpg","accuracy":"82%"},
   {"url":"https://i.postimg.cc/FsBvGD8p/IMG-20251020-110222-741.jpg","accuracy":"88%"},
   {"url":"https://i.postimg.cc/RVj17zSJ/IMG-20251020-105443-517.jpg","accuracy":"83%"},
   {"url":"https://i.postimg.cc/pTRMy75V/IMG-20251020-110240-031.jpg","accuracy":"87%"},
   {"url":"https://i.postimg.cc/VvZxGkGs/IMG-20251020-110255-468.jpg","accuracy":"84%"}
 ]
}

# ----------------------------------------
# In-memory storage (simple for demo)
# ----------------------------------------
users = {}  # chat_id -> {lang, player_id, registered, deposited}
stats = {"total": 0, "registered": 0, "deposited": 0}
postbackData = {"registrations": {}, "deposits": {}, "approvedDeposits": {}}


# ----------------------------------------
# Telegram helper functions
# ----------------------------------------
def telegram_request(method, payload=None, files=None):
    url = f"{TELEGRAM_API_URL}/{method}"
    try:
        if files:
            r = requests.post(url, data=payload, files=files, timeout=15)
        else:
            r = requests.post(url, json=payload, timeout=15)
        if r.status_code != 200:
            logger.error(f"Telegram API error ({method}): {r.status_code} - {r.text}")
        return r.json()
    except Exception as e:
        logger.exception("Error calling Telegram API: %s", e)
        return None

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram_request("sendMessage", payload)

def send_photo(chat_id, photo_url, caption=None, reply_markup=None):
    payload = {"chat_id": chat_id, "photo": photo_url}
    if caption:
        payload["caption"] = caption
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram_request("sendPhoto", payload)

def edit_message_text(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram_request("editMessageText", payload)

# Utility to build inline keyboards
def build_inline_keyboard(button_rows):
    return {"inline_keyboard": button_rows}

# ----------------------------------------
# Routes: root, test, stats, all-images, setup-webhook
# ----------------------------------------
@app.route("/", methods=["GET"])
def root():
    total_images = sum(len(v) for v in predictionImages.values())
    return (
        f"<h1>Chicken Predictor Bot</h1>"
        f"<p>Status: Running</p>"
        f"<p>Languages: {', '.join([f'{d['flag']} {d['name']}' for d in languages.values()])}</p>"
        f"<p>Prediction images: {total_images}</p>"
        f"<p><a href='/test'>/test</a> <a href='/stats'>/stats</a> <a href='/all-images'>/all-images</a></p>"
    )

@app.route("/test", methods=["GET"])
def route_test():
    if ADMIN_CHAT_ID:
        send_message(ADMIN_CHAT_ID, "✅ Test message: Chicken Predictor Bot is deployed.")
    return jsonify({"success": True, "message": "Test endpoint triggered."})

@app.route("/stats", methods=["GET"])
def route_stats():
    return jsonify({
        "botStats": stats,
        "registered_count": stats["registered"],
        "deposited_count": stats["deposited"],
        "users_count_in_memory": len(users)
    })

@app.route("/all-images", methods=["GET"])
def route_all_images():
    return jsonify({
        "total_images": sum(len(v) for v in predictionImages.values()),
        "images_by_mode": {k: len(v) for k, v in predictionImages.items()},
        "images": predictionImages
    })

@app.route("/setup-webhook", methods=["GET"])
def route_setup_webhook():
    return jsonify({
        "success": True,
        "bot_token_set": bool(BOT_TOKEN),
        "vercel_url": VERCEL_URL,
        "webhook_url": f"{VERCEL_URL}/webhook" if VERCEL_URL else "Set VERCEL_URL"
    })


# ----------------------------------------
# Postback from partner (1Win / Mostbet) - as provided earlier
# ----------------------------------------
@app.route("/lwin-postback", methods=["GET"])
def lwin_postback():
    player_id = request.args.get("player_id")
    status = request.args.get("status")
    amount = request.args.get("amount")

    logger.info(f"Postback received: player_id={player_id} status={status} amount={amount}")

    if status == "registration":
        postbackData["registrations"][player_id] = {"status": "registered", "player_id": player_id}
        stats["registered"] += 1
    elif status == "fdp":
        postbackData["deposits"][player_id] = {"status": "deposited", "amount": amount, "player_id": player_id}
        stats["deposited"] += 1
    elif status == "fd_approved":
        postbackData["approvedDeposits"][player_id] = {"status": "approved", "amount": amount, "player_id": player_id}

    return jsonify({"success": True, "player_id": player_id, "status": status})

@app.route("/verify-player/<player_id>", methods=["GET"])
def verify_player(player_id):
    registration = postbackData["registrations"].get(player_id)
    deposit = postbackData["deposits"].get(player_id)
    approved = postbackData["approvedDeposits"].get(player_id)
    return jsonify({
        "isRegistered": bool(registration),
        "hasDeposit": bool(deposit),
        "isApproved": bool(approved),
        "registration_data": registration,
        "deposit_data": deposit,
        "approved_data": approved
    })


# ----------------------------------------
# Telegram Webhook handling
# ----------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set. Ignoring incoming webhook.")
        return jsonify({"error": "BOT_TOKEN not set on server"}), 500

    update = request.get_json(force=True)
    logger.info(f"Incoming update: {update}")

    # Handle callback_query (inline buttons)
    if "callback_query" in update:
        cb = update["callback_query"]
        data = cb.get("data")
        chat_id = cb["message"]["chat"]["id"]
        message_id = cb["message"]["message_id"]

        # Language selection pattern: "lang:<code>"
        if data and data.startswith("lang:"):
            lang_code = data.split(":", 1)[1]
            users.setdefault(chat_id, {})["lang"] = lang_code
            lang = languages.get(lang_code, languages["en"])
            text = f"{lang['welcome']}\n\n{lang['instructions']}"
            edit_message_text(chat_id, message_id, text)
            # send next step buttons: REGISTER, ENTER ID
            keyboard = build_inline_keyboard([
                [{"text": "REGISTER", "url": AFFILIATE_LINK}],
                [{"text": "I HAVE REGISTERED (Enter Player ID)", "callback_data": "enter_player_id"}],
            ])
            send_message(chat_id, lang["step1"], reply_markup=keyboard)
            return jsonify({"ok": True})

        # Next button to enter player id
        if data == "enter_player_id":
            lang_code = users.get(chat_id, {}).get("lang", "en")
            lang = languages.get(lang_code, languages["en"])
            send_message(chat_id, lang["enterPlayerId"])
            return jsonify({"ok": True})

        # Check deposit
        if data == "check_deposit":
            lang_code = users.get(chat_id, {}).get("lang", "en")
            lang = languages.get(lang_code, languages["en"])
            send_message(chat_id, lang["checking"])
            # In this demo we just reply that deposit is not found unless postback arrived
            player_id = users.get(chat_id, {}).get("player_id")
            if player_id and postbackData["deposits"].get(player_id):
                send_message(chat_id, lang["verified"])
                # Allow game mode selection
                keyboard = build_inline_keyboard([
                    [{"text": "Easy", "callback_data": "mode:easy"}],
                    [{"text": "Medium", "callback_data": "mode:medium"}],
                    [{"text": "Hard", "callback_data": "mode:hard"}],
                    [{"text": "Hardcore", "callback_data": "mode:hardcore"}],
                ])
                send_message(chat_id, lang["congratulations"], reply_markup=keyboard)
            else:
                send_message(chat_id, lang["registeredNoDeposit"])
            return jsonify({"ok": True})

        # Mode selection
        if data and data.startswith("mode:"):
            mode = data.split(":", 1)[1]
            chat_data = users.setdefault(chat_id, {})
            lang_code = chat_data.get("lang", "en")
            lang = languages.get(lang_code, languages["en"])
            send_message(chat_id, f"🔎 Selected mode: {mode}. Sending top 3 predictions...")
            images = predictionImages.get(mode, [])[:3]
            for img in images:
                caption = f"Prediction accuracy: {img.get('accuracy')}"
                send_photo(chat_id, img.get("url"), caption=caption)
            return jsonify({"ok": True})

        # Unknown callback
        logger.info("Unknown callback data: %s", data)
        return jsonify({"ok": True})

    # Handle normal messages
    if "message" in update:
        message = update["message"]
        chat = message["chat"]
        chat_id = chat["id"]
        text = message.get("text", "").strip()

        # Ensure user in memory
        if chat_id not in users:
            users[chat_id] = {"lang": "en", "registered": False, "player_id": None}
            stats["total"] = len(users)

        # Commands
        lower = text.lower()
        if lower == "/start":
            # show language selection keyboard
            keyboard = build_inline_keyboard([
                [{"text": f"{languages['en']['flag']} English", "callback_data": "lang:en"},
                 {"text": f"{languages['hi']['flag']} हिन्दी", "callback_data": "lang:hi"}],
                [{"text": f"{languages['bn']['flag']} বাংলা", "callback_data": "lang:bn"},
                 {"text": f"{languages['ur']['flag']} اردو", "callback_data": "lang:ur"}],
                [{"text": f"{languages['ne']['flag']} नेपाली", "callback_data": "lang:ne"}]
            ])
            send_message(chat_id, "🌐 Select your preferred language / कृपया अपनी भाषा चुनें", reply_markup=keyboard)
            return jsonify({"ok": True})

        if lower == "/help":
            lang_code = users[chat_id].get("lang", "en")
            lang = languages.get(lang_code, languages["en"])
            help_text = (
                f"{lang['selectLanguage']}\n"
                "/start - start\n"
                "/language - change language\n"
                "/register - registration steps\n"
                "/check - check deposit status\n"
                "/modes - show game modes\n"
            )
            send_message(chat_id, help_text)
            return jsonify({"ok": True})

        if lower == "/language":
            keyboard = build_inline_keyboard([
                [{"text": f"{languages['en']['flag']} English", "callback_data": "lang:en"}],
                [{"text": f"{languages['hi']['flag']} हिन्दी", "callback_data": "lang:hi"}],
                [{"text": f"{languages['bn']['flag']} বাংলা", "callback_data": "lang:bn"}],
                [{"text": f"{languages['ur']['flag']} اردو", "callback_data": "lang:ur"}],
                [{"text": f"{languages['ne']['flag']} नेपाली", "callback_data": "lang:ne"}],
            ])
            send_message(chat_id, "🌐 Choose language", reply_markup=keyboard)
            return jsonify({"ok": True})

        if lower == "/register":
            lang_code = users[chat_id].get("lang", "en")
            lang = languages.get(lang_code, languages["en"])
            keyboard = build_inline_keyboard([
                [{"text": "REGISTER", "url": AFFILIATE_LINK}],
                [{"text": "I HAVE REGISTERED", "callback_data": "enter_player_id"}]
            ])
            send_message(chat_id, lang["step1"], reply_markup=keyboard)
            return jsonify({"ok": True})

        if lower == "/check":
            # trigger check_deposit callback flow
            keyboard = build_inline_keyboard([
                [{"text": "CHECK DEPOSIT", "callback_data": "check_deposit"}]
            ])
            send_message(chat_id, "Click to check deposit", reply_markup=keyboard)
            return jsonify({"ok": True})

        if lower.startswith("/setid") or lower.startswith("playerid") or lower.isdigit():
            # allow users to send player id directly. Accept formats:
            # /setid 123456 or 123456
            if lower.startswith("/setid"):
                parts = text.split()
                if len(parts) >= 2:
                    player_id = parts[1]
                else:
                    send_message(chat_id, "Usage: /setid <YourPlayerID>")
                    return jsonify({"ok": True})
            else:
                player_id = text.strip()

            users[chat_id]["player_id"] = player_id
            users[chat_id]["registered"] = True
            postbackData["registrations"].setdefault(player_id, {"status": "registered", "player_id": player_id})
            stats["registered"] = len(postbackData["registrations"])
            lang_code = users[chat_id].get("lang", "en")
            lang = languages.get(lang_code, languages["en"])
            send_message(chat_id, lang["registeredNoDeposit"])
            return jsonify({"ok": True})

        if lower == "/modes":
            keyboard = build_inline_keyboard([
                [{"text": "Easy", "callback_data": "mode:easy"}],
                [{"text": "Medium", "callback_data": "mode:medium"}],
                [{"text": "Hard", "callback_data": "mode:hard"}],
                [{"text": "Hardcore", "callback_data": "mode:hardcore"}]
            ])
            send_message(chat_id, "Choose a game mode:", reply_markup=keyboard)
            return jsonify({"ok": True})

        # If user sends numeric Player ID directly, handle above; otherwise unknown
        send_message(chat_id, "I didn't understand that. Use /help to see commands.")
        return jsonify({"ok": True})

    # default
    return jsonify({"ok": True})

# ----------------------------------------
# Run app (for local testing)
# ----------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)
