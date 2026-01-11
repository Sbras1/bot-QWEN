import os
import threading
import asyncio
from flask import Flask, render_template_string
from telethon import TelegramClient, events

# --- 1. إعدادات الموقع (Flask) ---
app = Flask(__name__)

# مخزن بسيط للبيانات (في الذاكرة)
# سنخزن هنا أسماء المستخدمين والرسائل لعرضها في الموقع
bot_stats = {
    "total_users": set(),  # نستخدم set لعدم تكرار الأسماء
    "messages_log": []     # قائمة سجل الرسائل
}

# تصميم صفحة الويب (HTML بسيط)
HTML_PAGE = """
<!DOCTYPE html>
<html dir="rtl">
<head>
    <title>لوحة تحكم البوت</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h1 { color: #333; }
        .number { font-size: 40px; color: #0088cc; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; border-bottom: 1px solid #ddd; text-align: right; }
        th { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <div class="card">
        <h1>📊 إحصائيات البوت</h1>
        <p>عدد الأشخاص الذين تفاعلوا:</p>
        <div class="number">{{ user_count }}</div>
    </div>

    <div class="card">
        <h2>📝 آخر الرسائل الواردة</h2>
        <table>
            <tr>
                <th>التوقيت (تسلسلي)</th>
                <th>الاسم</th>
                <th>الرسالة</th>
            </tr>
            {% for msg in logs reversed %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ msg.name }}</td>
                <td>{{ msg.text }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_PAGE, 
                                  user_count=len(bot_stats["total_users"]), 
                                  logs=bot_stats["messages_log"])

def run_web_server():
    # تشغيل السيرفر على المنفذ 10000 (مهم لـ Render)
    app.run(host='0.0.0.0', port=10000)

# --- 2. إعدادات البوت (Telethon) ---
# جلب المتغيرات من بيئة النظام (سنضيفها في Render لاحقاً)
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
# ملاحظة: في Render لا نستخدم ملف الجلسة .session، بل نستخدم StringSession (شرحها أسفل)
# لكن للتبسيط الآن سنستخدم الجلسة العادية، قد تطلب منك الكود مرة واحدة عند التشغيل المحلي
client = TelegramClient('my_render_session', int(api_id), api_hash)

@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    # 1. تسجيل البيانات للموقع
    sender = await event.get_sender()
    name = sender.first_name if sender else "مجهول"
    message = event.raw_text
    
    bot_stats["total_users"].add(sender.id)
    bot_stats["messages_log"].append({"name": name, "text": message})
    
    # نحتفظ بآخر 50 رسالة فقط لتوفير الذاكرة
    if len(bot_stats["messages_log"]) > 50:
        bot_stats["messages_log"].pop(0)

    # 2. الرد التلقائي (مثال)
    if "مرحبا" in message:
        await event.reply("أهلاً! أنا أعمل الآن عبر سيرفر Render 🚀")

# --- 3. التشغيل المزدوج ---
if __name__ == '__main__':
    # التأكد من وجود البيانات
    if not api_id or not api_hash:
        print("❌ خطأ: يجب تعيين API_ID و API_HASH")
    else:
        # تشغيل الموقع في خيط منفصل (Thread) حتى لا يوقف البوت
        print("🌍 جاري تشغيل موقع الويب...")
        t = threading.Thread(target=run_web_server)
        t.start()

        # تشغيل البوت في العملية الرئيسية
        print("🤖 جاري تشغيل البوت...")
        client.start()
        client.run_until_disconnected()
