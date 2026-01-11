import os
import threading
import asyncio
from flask import Flask, render_template_string
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.users import GetFullUserRequest

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
    # تشغيل السيرفر على المنفذ 10000 (مهم لـ Render)
    app.run(host='0.0.0.0', port=10000)

# --- 2. إعدادات البوت (Telethon) ---
# جلب المتغيرات من بيئة النظام
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
session_string = os.environ.get('SESSION_STRING')  # جلسة المستخدم

# إنشاء العميل باستخدام StringSession
client = TelegramClient(StringSession(session_string), int(api_id) if api_id else 0, api_hash or '')

# حفظ البيانات الأصلية للاستعادة
original_profile = {
    "first_name": None,
    "last_name": None,
    "bio": None,
    "photo": None
}

# --- أوامر الانتحال (للمزاح) ---

@client.on(events.NewMessage(outgoing=True, pattern=r'\.clone'))
async def clone_command(event):
    """انتحال شخص - رد على رسالته"""
    reply = await event.get_reply_message()
    if not reply:
        await event.edit("❌ رد على رسالة الشخص المراد انتحاله")
        return
    
    await event.edit("⏳ جاري الانتحال...")
    
    try:
        # حفظ بياناتك الأصلية أولاً
        me = await client.get_me()
        full = await client(GetFullUserRequest(me))
        original_profile["first_name"] = me.first_name
        original_profile["last_name"] = me.last_name or ""
        original_profile["bio"] = full.full_user.about or ""
        
        # جلب بيانات الضحية
        target = await reply.get_sender()
        target_full = await client(GetFullUserRequest(target))
        
        # تغيير الاسم والبايو
        await client(UpdateProfileRequest(
            first_name=target.first_name or "",
            last_name=target.last_name or "",
            about=target_full.full_user.about or ""
        ))
        
        # تغيير الصورة
        photos = await client.get_profile_photos(target, limit=1)
        if photos:
            photo = await client.download_media(photos[0])
            await client(UploadProfilePhotoRequest(
                file=await client.upload_file(photo)
            ))
            os.remove(photo)  # حذف الملف المؤقت
        
        await event.edit(f"✅ تم انتحال {target.first_name}!\n\nللعودة: `.reset`")
    except Exception as e:
        await event.edit(f"❌ خطأ: {str(e)}")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.name (.+)'))
async def name_command(event):
    """تغيير الاسم"""
    # حفظ الاسم الأصلي إذا لم يحفظ
    if not original_profile["first_name"]:
        me = await client.get_me()
        original_profile["first_name"] = me.first_name
        original_profile["last_name"] = me.last_name or ""
    
    name = event.pattern_match.group(1)
    parts = name.split(" ", 1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    
    await client(UpdateProfileRequest(first_name=first, last_name=last))
    await event.edit(f"✅ تم تغيير الاسم إلى: {name}")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.bio (.+)'))
async def bio_command(event):
    """تغيير الحالة/البايو"""
    # حفظ البايو الأصلي
    if not original_profile["bio"]:
        me = await client.get_me()
        full = await client(GetFullUserRequest(me))
        original_profile["bio"] = full.full_user.about or ""
    
    bio = event.pattern_match.group(1)
    await client(UpdateProfileRequest(about=bio))
    await event.edit(f"✅ تم تغيير الحالة")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.photo'))
async def photo_command(event):
    """تغيير الصورة - رد على صورة"""
    reply = await event.get_reply_message()
    if not reply or not reply.photo:
        await event.edit("❌ رد على صورة")
        return
    
    await event.edit("⏳ جاري تغيير الصورة...")
    photo = await reply.download_media()
    await client(UploadProfilePhotoRequest(
        file=await client.upload_file(photo)
    ))
    os.remove(photo)
    await event.edit("✅ تم تغيير الصورة")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.reset'))
async def reset_command(event):
    """استعادة البيانات الأصلية"""
    await event.edit("⏳ جاري الاستعادة...")
    
    try:
        # استعادة الاسم والبايو
        if original_profile["first_name"]:
            await client(UpdateProfileRequest(
                first_name=original_profile["first_name"],
                last_name=original_profile["last_name"] or "",
                about=original_profile["bio"] or ""
            ))
        
        await event.edit("✅ تم استعادة بياناتك الأصلية!")
    except Exception as e:
        await event.edit(f"❌ خطأ: {str(e)}")

# --- أوامر المالك (outgoing = أنت فقط) ---

@client.on(events.NewMessage(outgoing=True, pattern=r'\.say (.+)'))
async def say_command(event):
    """أمر الانتحال - يحذف رسالتك ويرسل النص كرسالة عادية"""
    text = event.pattern_match.group(1)
    await event.delete()
    await event.respond(text)

@client.on(events.NewMessage(outgoing=True, pattern=r'\.del'))
async def delete_command(event):
    """حذف الرسالة المردود عليها"""
    reply = await event.get_reply_message()
    if reply:
        await reply.delete()
    await event.delete()

@client.on(events.NewMessage(outgoing=True, pattern=r'\.edit (.+)'))
async def edit_command(event):
    """تعديل الرسالة المردود عليها"""
    text = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if reply and reply.out:
        await reply.edit(text)
    await event.delete()

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

# --- 3. التشغيل المزدوج ---
if __name__ == '__main__':
    # التأكد من وجود البيانات
    if not api_id or not api_hash or not session_string:
        print("❌ خطأ: يجب تعيين API_ID و API_HASH و SESSION_STRING")
    else:
        # تشغيل الموقع في خيط منفصل (Thread) حتى لا يوقف البوت
        print("🌍 جاري تشغيل موقع الويب...")
        t = threading.Thread(target=run_web_server)
        t.start()

        # تشغيل البوت في العملية الرئيسية
        print("🤖 جاري تشغيل اليوزربوت...")
        client.start()
        client.run_until_disconnected()
