"""
نظام الحفظ التلقائي 📦
يحفظ كل من يرسل في أي مجموعة
"""
import os
from datetime import datetime
from telethon import events
import database as db

def register(client):
    """تسجيل نظام الحفظ التلقائي"""
    
    owner_id = os.environ.get('OWNER_ID')
    if owner_id:
        owner_id = int(owner_id)
    
    # ═══════════════════════════════════════════════════════════
    # الحفظ التلقائي - كل رسالة في أي مجموعة
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage())
    async def auto_save(event):
        """حفظ تلقائي لكل من يرسل"""
        # تجاهل الرسائل الصادرة والخاصة
        if event.out or not event.is_group:
            return
        
        sender = await event.get_sender()
        if not sender or not hasattr(sender, 'id') or getattr(sender, 'bot', False):
            return
        
        user_id = sender.id
        first_name = getattr(sender, 'first_name', '') or ''
        last_name = getattr(sender, 'last_name', '') or ''
        full_name = f"{first_name} {last_name}".strip() or 'بدون اسم'
        username = getattr(sender, 'username', '') or ''
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # جلب البيانات القديمة
        old_data = db.get_member(user_id)
        
        if old_data:
            # تحديث البيانات
            old_name = old_data.get('full_name', '')
            old_username = old_data.get('username', '')
            
            # تسجيل تغيير الاسم
            if old_name and old_name != full_name:
                name_history = old_data.get('name_history', [])
                name_history.append({'name': full_name, 'date': today})
                old_data['name_history'] = name_history
            
            # تسجيل تغيير اليوزر
            if old_username != username:
                username_history = old_data.get('username_history', [])
                username_history.append({'username': username, 'date': today})
                old_data['username_history'] = username_history
            
            old_data['full_name'] = full_name
            old_data['first_name'] = first_name
            old_data['last_name'] = last_name
            old_data['username'] = username
            old_data['username_lower'] = username.lower() if username else ''
            old_data['last_seen'] = now
            
            db.save_member(user_id, old_data)
        else:
            # عضو جديد
            new_data = {
                'user_id': user_id,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name,
                'username': username,
                'username_lower': username.lower() if username else '',
                'first_seen': now,
                'last_seen': now,
                'name_history': [{'name': full_name, 'date': today}],
                'username_history': [{'username': username, 'date': today}] if username else []
            }
            db.save_member(user_id, new_data)
    
    # ═══════════════════════════════════════════════════════════
    # أوامر الاستعلام (للمالك فقط)
    # ═══════════════════════════════════════════════════════════
    
    @client.on(events.NewMessage(pattern=r'^\.عضو (\d+)$'))
    async def member_info(event):
        """جلب معلومات عضو"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        user_id = int(event.pattern_match.group(1))
        member = db.get_member(user_id)
        
        if not member:
            await event.reply("❌ لم يتم العثور على هذا العضو.")
            return
        
        username = member.get('username', '')
        username_text = f"@{username}" if username else "بدون يوزر"
        
        text = f"""
**👤 معلومات العضو**

🆔 `{member.get('user_id')}`
👤 {member.get('full_name', 'بدون اسم')}
📧 {username_text}
📅 أول ظهور: {member.get('first_seen', '؟')}
📅 آخر ظهور: {member.get('last_seen', '؟')}
"""
        await event.reply(text)
    
    @client.on(events.NewMessage(pattern=r'^\.سجل (\d+)$'))
    async def member_history(event):
        """سجل تغييرات عضو"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        user_id = int(event.pattern_match.group(1))
        member = db.get_member(user_id)
        
        if not member:
            await event.reply("❌ لم يتم العثور على هذا العضو.")
            return
        
        text = f"**📜 سجل التغييرات**\n🆔 `{user_id}`\n\n"
        
        name_history = member.get('name_history', [])
        if name_history:
            text += "**📝 الأسماء:**\n"
            for entry in name_history[-10:]:
                text += f"• {entry.get('name')} ({entry.get('date')})\n"
            text += "\n"
        
        username_history = member.get('username_history', [])
        if username_history:
            text += "**📧 اليوزرات:**\n"
            for entry in username_history[-10:]:
                uname = entry.get('username') or 'بدون'
                text += f"• @{uname} ({entry.get('date')})\n"
        
        if not name_history and not username_history:
            text += "لا توجد تغييرات."
        
        await event.reply(text)
    
    @client.on(events.NewMessage(pattern=r'^\.بحث (.+)$'))
    async def search_member(event):
        """البحث عن عضو"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        query = event.pattern_match.group(1).strip()
        
        # بحث بالآيدي
        if query.isdigit():
            member = db.get_member(int(query))
        else:
            # بحث باليوزر
            member = db.search_by_username(query)
        
        if not member:
            await event.reply("❌ لم يتم العثور على نتائج.")
            return
        
        username = member.get('username', '')
        username_text = f"@{username}" if username else "بدون يوزر"
        
        text = f"""
**🔍 نتيجة البحث**

🆔 `{member.get('user_id')}`
👤 {member.get('full_name', 'بدون اسم')}
📧 {username_text}
📅 أول ظهور: {member.get('first_seen', '؟')}
📅 آخر ظهور: {member.get('last_seen', '؟')}
"""
        await event.reply(text)
    
    @client.on(events.NewMessage(pattern=r'^\.تنظيف$'))
    async def cleanup(event):
        """حذف البيانات القديمة"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        msg = await event.reply("⏳ جاري حذف البيانات القديمة...")
        
        count = db.cleanup_old_data()
        
        await msg.edit(f"✅ تم حذف {count} سجل قديم.")
    
    @client.on(events.NewMessage(pattern=r'^\.اوامر$'))
    async def show_help(event):
        """عرض الأوامر"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        text = """
**📋 الأوامر**

`.عضو 123456` - معلومات عضو
`.سجل 123456` - سجل تغييراته
`.بحث 123456` - بحث بالآيدي
`.بحث @user` - بحث باليوزر
`.تنظيف` - حذف البيانات القديمة
`.اوامر` - عرض الأوامر

**ℹ️ ملاحظة:**
الحفظ يتم تلقائياً لكل من يرسل في أي مجموعة.
"""
        await event.reply(text)
    
    print("✅ نظام الحفظ التلقائي جاهز")
