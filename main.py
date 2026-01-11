"""
البوت الرئيسي مع لوحة التحكم
"""
import os
import threading
from flask import Flask, render_template_string
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import plugins
import database as db

# --- 1. إعدادات الموقع (Flask) ---
app = Flask(__name__)

# مخزن بسيط للبيانات
bot_stats = {
    "total_users": set(),
    "messages_log": []
}

# تصميم صفحة الويب
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
                <th>#</th>
                <th>الاسم</th>
                <th>الرسالة</th>
            </tr>
            {% for msg in logs|reverse %}
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
    app.run(host='0.0.0.0', port=10000)

# --- 2. إعدادات البوت ---
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
session_string = os.environ.get('SESSION_STRING')

client = TelegramClient(StringSession(session_string), int(api_id) if api_id else 0, api_hash or '')

# تسجيل الرسائل الواردة
@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    sender = await event.get_sender()
    
    # التحقق من نوع المرسل (مستخدم أو قناة)
    if hasattr(sender, 'first_name'):
        name = sender.first_name or "مجهول"
        sender_id = sender.id
    elif hasattr(sender, 'title'):
        name = sender.title  # اسم القناة
        sender_id = sender.id
    else:
        name = "مجهول"
        sender_id = 0
    
    message = event.raw_text
    
    bot_stats["total_users"].add(sender_id)
    bot_stats["messages_log"].append({"name": name, "text": message})
    
    if len(bot_stats["messages_log"]) > 50:
        bot_stats["messages_log"].pop(0)

# --- 3. التشغيل ---
if __name__ == '__main__':
    if not api_id or not api_hash or not session_string:
        print("❌ خطأ: يجب تعيين API_ID و API_HASH و SESSION_STRING")
    else:
        # تهيئة قاعدة البيانات
        db.init_firebase()
        
        # تحميل الإضافات
        plugins.load_all(client)
        
        # تشغيل الموقع
        print("🌍 جاري تشغيل موقع الويب...")
        t = threading.Thread(target=run_web_server)
        t.start()

        # تشغيل البوت
        print("🤖 جاري تشغيل اليوزربوت...")
        client.start()
        client.run_until_disconnected()
