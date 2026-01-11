"""
أوامر التحكم عن بُعد 🎮
يسمح للمالك بالتحكم بالبوت من حساب آخر
"""
import os
import httpx
from telethon import events

# رابط Groq API
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def register(client):
    """تسجيل أوامر التحكم عن بُعد"""
    
    owner_id = os.environ.get('OWNER_ID')
    groq_key = os.environ.get('GROQ_API_KEY')
    
    if not owner_id:
        print("⚠️ لم يتم تعيين OWNER_ID - التحكم عن بُعد معطل")
        return
    
    owner_id = int(owner_id)
    
    # أمر البحث عن بُعد
    @client.on(events.NewMessage(incoming=True, pattern=r'\.بحث (\d+)'))
    async def remote_search(event):
        """البحث عن شخص بالآيدي - عن بُعد"""
        sender = await event.get_sender()
        if sender.id != owner_id:
            return  # تجاهل إذا ليس المالك
        
        user_id = event.pattern_match.group(1)
        await event.reply("🔍 جاري البحث...")
        
        try:
            user = await client.get_entity(int(user_id))
            
            # جمع المعلومات
            name = getattr(user, 'first_name', '') or ''
            last = getattr(user, 'last_name', '') or ''
            full_name = f"{name} {last}".strip() or "بدون اسم"
            username = f"@{user.username}" if user.username else "لا يوجد"
            bio = ""
            
            try:
                full = await client(GetFullUserRequest(user.id))
                bio = full.full_user.about or "لا يوجد"
            except:
                bio = "غير متاح"
            
            info = f"""
**🔍 نتيجة البحث:**

👤 **الاسم:** {full_name}
🆔 **الآيدي:** `{user.id}`
📧 **اليوزر:** {username}
📝 **البايو:** {bio}
"""
            # إرسال الصورة إذا موجودة
            photos = await client.get_profile_photos(user.id, limit=1)
            if photos:
                await event.reply(info, file=photos[0])
            else:
                await event.reply(info)
                
        except Exception as e:
            await event.reply(f"❌ خطأ: {str(e)}")
    
    # أمر الذكاء الاصطناعي عن بُعد
    @client.on(events.NewMessage(incoming=True, pattern=r'\.ذكاء (.+)'))
    async def remote_ai(event):
        """سؤال الذكاء الاصطناعي - عن بُعد"""
        sender = await event.get_sender()
        if sender.id != owner_id:
            return
        
        if not groq_key:
            await event.reply("❌ لم يتم تعيين GROQ_API_KEY")
            return
        
        question = event.pattern_match.group(1)
        await event.reply("🤔 جاري التفكير...")
        
        try:
            async with httpx.AsyncClient() as http:
                response = await http.post(
                    GROQ_URL,
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": "أنت مساعد ذكي. أجب باللغة العربية بشكل مختصر ومفيد."},
                            {"role": "user", "content": question}
                        ],
                        "max_tokens": 1024
                    },
                    timeout=30.0
                )
                
                data = response.json()
                
                if "choices" in data:
                    answer = data["choices"][0]["message"]["content"]
                    if len(answer) > 4000:
                        answer = answer[:4000] + "..."
                    await event.reply(f"**🤖 الذكاء الاصطناعي:**\n\n{answer}")
                else:
                    error = data.get("error", {}).get("message", "خطأ غير معروف")
                    await event.reply(f"❌ خطأ: {error}")
        except Exception as e:
            await event.reply(f"❌ خطأ: {str(e)}")
    
    # أمر الأوامر عن بُعد
    @client.on(events.NewMessage(incoming=True, pattern=r'\.اوامر'))
    async def remote_help(event):
        """عرض الأوامر - عن بُعد"""
        sender = await event.get_sender()
        if sender.id != owner_id:
            return
        
        help_text = """
**🎮 أوامر التحكم عن بُعد**

**🔍 البحث:**
• `.بحث 123456789` - البحث عن شخص بالآيدي

**🧠 الذكاء الاصطناعي:**
• `.ذكاء سؤالك` - اسأل الذكاء الاصطناعي

**📊 الحالة:**
• `.حالة` - معرفة حالة البوت

**❓ مساعدة:**
• `.اوامر` - عرض هذه القائمة

⚠️ **ملاحظة:** الأوامر تبدأ بنقطة (.)
"""
        await event.reply(help_text)
    
    # أمر حالة البوت
    @client.on(events.NewMessage(incoming=True, pattern=r'\.حالة'))
    async def remote_status(event):
        """حالة البوت - عن بُعد"""
        sender = await event.get_sender()
        if sender.id != owner_id:
            return
        
        me = await client.get_me()
        await event.reply(f"""
**📊 حالة البوت**

✅ البوت يعمل!
👤 الحساب: {me.first_name}
🆔 الآيدي: `{me.id}`
📧 اليوزر: @{me.username or 'لا يوجد'}
""")

    print(f"✅ التحكم عن بُعد مفعل للمالك: {owner_id}")
