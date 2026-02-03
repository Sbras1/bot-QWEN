"""
نظام الحفظ التلقائي 📦
يحفظ كل من يرسل في أي مجموعة + إشعارات التغييرات
"""
import os
import re
import asyncio
from datetime import datetime
from telethon import events
import database as db

# الحد الأقصى للاستيراد
MAX_IMPORT_LIMIT = 15000

# تتبع آخر حفظ لمنع التكرار
_last_save = {}
SAVE_COOLDOWN = 60  # ثانية واحدة بين كل حفظ لنفس المستخدم

# القروب المركزي للإشعارات
LOG_GROUP = -1005264933718
log_entity = None  # سيتم تعيينه عند البدء
init_done = False
debug_mode = False  # وضع التشخيص

def register(client):
    """تسجيل نظام الحفظ التلقائي"""
    global log_entity, init_done
    
    owner_id = os.environ.get('OWNER_ID')
    if owner_id:
        owner_id = int(owner_id)
    
    # محاولة الاتصال بالقروب المركزي
    async def init_log_group():
        global log_entity, init_done
        if init_done:
            return
        try:
            # انتظار حتى يتصل البوت
            await asyncio.sleep(5)
            
            # جلب آيدي القروب من قاعدة البيانات
            saved_id = db.get_log_group()
            if saved_id:
                print(f"📋 جلب قروب الإشعارات المحفوظ: {saved_id}")
            
            target_id = saved_id or LOG_GROUP
            
            # جلب كل الدردشات للتعرف على القروب
            async for dialog in client.iter_dialogs():
                chat_id = dialog.id
                # مقارنة الآيدي بطرق مختلفة
                if chat_id == target_id or chat_id == abs(target_id):
                    log_entity = dialog.entity
                    print(f"✅ تم العثور على قروب الإشعارات: {dialog.name}")
                    init_done = True
                    return
            
            if not log_entity:
                print(f"⚠️ لم يتم العثور على قروب الإشعارات")
            init_done = True
        except Exception as e:
            print(f"❌ خطأ في جلب القروب: {e}")
    
    # أمر لتهيئة القروب يدوياً
    @client.on(events.NewMessage(pattern=r'^\.ربط$'))
    async def link_group(event):
        """ربط القروب الحالي كقروب إشعارات"""
        global log_entity
        if not event.out:
            return
        
        if not event.is_group:
            await event.edit("❌ استخدم هذا الأمر داخل القروب المطلوب")
            return
        
        log_entity = await event.get_chat()
        chat_id = event.chat_id
        
        # حفظ في قاعدة البيانات
        db.save_log_group(chat_id)
        
        await event.edit(f"✅ تم ربط وحفظ هذا القروب للإشعارات\n🆔 `{chat_id}`")
    
    # ═══════════════════════════════════════════════════════════
    # الحفظ التلقائي - كل رسالة في أي مجموعة
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage())
    async def auto_save(event):
        """حفظ تلقائي لكل من يرسل"""
        global debug_mode
        
        # تجاهل الرسائل الصادرة والخاصة
        if event.out or not event.is_group:
            return
        
        sender = await event.get_sender()
        if not sender or not hasattr(sender, 'id') or getattr(sender, 'bot', False):
            return
        
        user_id = sender.id
        
        # منع التكرار - لا نحفظ نفس المستخدم كل ثانية
        import time
        now_ts = time.time()
        if user_id in _last_save:
            if now_ts - _last_save[user_id] < SAVE_COOLDOWN:
                return  # تخطي الحفظ
        _last_save[user_id] = now_ts
        
        first_name = getattr(sender, 'first_name', '') or ''
        last_name = getattr(sender, 'last_name', '') or ''
        full_name = f"{first_name} {last_name}".strip() or 'بدون اسم'
        username = getattr(sender, 'username', '') or ''
        
        # وضع التشخيص
        if debug_mode and log_entity:
            try:
                await client.send_message(log_entity, f"🔍 حفظ: {user_id} - {full_name}")
            except:
                pass
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # جلب اسم القروب
        chat = await event.get_chat()
        group_id = event.chat_id
        group_name = getattr(chat, 'title', '') or str(group_id)
        
        # جلب البيانات القديمة
        old_data = db.get_member(user_id)
        
        if old_data:
            # تحديث البيانات
            old_name = old_data.get('full_name', '')
            old_username = old_data.get('username', '')
            
            # تسجيل تغيير الاسم + إشعار
            if old_name and old_name != full_name:
                name_history = old_data.get('name_history', [])
                name_history.append({'name': full_name, 'date': today})
                old_data['name_history'] = name_history
                
                # إرسال إشعار
                try:
                    if log_entity:
                        notify_text = f"""
📝 **تغيير اسم**

🆔 `{user_id}`
👤 القديم: {old_name}
👤 الجديد: {full_name}
📧 @{username if username else 'بدون يوزر'}
📅 {now}
"""
                        await client.send_message(log_entity, notify_text)
                except:
                    pass
            
            # تسجيل تغيير اليوزر + إشعار
            if old_username != username:
                username_history = old_data.get('username_history', [])
                username_history.append({'username': username, 'date': today})
                old_data['username_history'] = username_history
                
                # إرسال إشعار
                try:
                    if log_entity:
                        old_uname = f"@{old_username}" if old_username else "بدون"
                        new_uname = f"@{username}" if username else "بدون"
                        notify_text = f"""
📧 **تغيير يوزر**

🆔 `{user_id}`
👤 {full_name}
📧 القديم: {old_uname}
📧 الجديد: {new_uname}
📅 {now}
"""
                        await client.send_message(log_entity, notify_text)
                except:
                    pass
            
            old_data['full_name'] = full_name
            old_data['first_name'] = first_name
            old_data['last_name'] = last_name
            old_data['username'] = username
            old_data['username_lower'] = username.lower() if username else ''
            old_data['last_seen'] = now
            
            # تحديث قائمة القروبات
            groups_seen = old_data.get('groups_seen', {})
            groups_seen[str(group_id)] = group_name
            old_data['groups_seen'] = groups_seen
            
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
                'username_history': [{'username': username, 'date': today}] if username else [],
                'groups_seen': {str(group_id): group_name}
            }
            db.save_member(user_id, new_data)
    
    # ═══════════════════════════════════════════════════════════
    # أوامر الاختبار
    # ═══════════════════════════════════════════════════════════
    
    @client.on(events.NewMessage(pattern=r'^\.بنق$'))
    async def ping(event):
        """اختبار البوت"""
        if not event.out:
            return
        await event.edit("✅ **شغال!**")
    
    @client.on(events.NewMessage(pattern=r'^\.تست$'))
    async def test_log(event):
        """اختبار إرسال للقروب المركزي"""
        if not event.out:
            return
        
        try:
            if log_entity:
                await client.send_message(log_entity, "🔔 **اختبار الإشعارات**\n\nالبوت متصل بنجاح!")
                await event.edit(f"✅ تم الإرسال للقروب")
            else:
                await event.edit(f"❌ لم يتم العثور على القروب المركزي")
        except Exception as e:
            await event.edit(f"❌ خطأ: {e}")
    
    @client.on(events.NewMessage(pattern=r'^\.دبق$'))
    async def toggle_debug(event):
        """تفعيل/تعطيل وضع التشخيص"""
        global debug_mode
        if not event.out:
            return
        
        debug_mode = not debug_mode
        status = "مفعل ✅" if debug_mode else "معطل ❌"
        await event.edit(f"🔍 وضع التشخيص: {status}")
    
    @client.on(events.NewMessage(pattern=r'^\.فحص$'))
    async def scan_all_groups(event):
        """فحص كل القروبات وحفظ جميع الأعضاء"""
        if not event.out:
            return
        
        msg = await event.edit("⏳ **جاري فحص كل القروبات...**")
        
        total_groups = 0
        total_members = 0
        saved_new = 0
        
        try:
            # جلب كل الدردشات
            async for dialog in client.iter_dialogs():
                if not (dialog.is_group or dialog.is_channel):
                    continue
                
                total_groups += 1
                group_name = dialog.name
                group_id = dialog.id
                
                try:
                    # جلب أعضاء القروب
                    async for user in client.iter_participants(dialog.entity, limit=500):
                        if user.bot:
                            continue
                        
                        total_members += 1
                        user_id = user.id
                        
                        # تحقق إذا موجود
                        existing = db.get_member(user_id)
                        if existing:
                            # تحديث قائمة القروبات فقط
                            groups_seen = existing.get('groups_seen', {})
                            groups_seen[str(group_id)] = group_name
                            existing['groups_seen'] = groups_seen
                            db.save_member(user_id, existing)
                            continue
                        
                        # حفظ عضو جديد
                        first_name = getattr(user, 'first_name', '') or ''
                        last_name = getattr(user, 'last_name', '') or ''
                        full_name = f"{first_name} {last_name}".strip() or 'بدون اسم'
                        username = getattr(user, 'username', '') or ''
                        
                        now = datetime.now().strftime('%Y-%m-%d %H:%M')
                        today = datetime.now().strftime('%Y-%m-%d')
                        
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
                            'username_history': [{'username': username, 'date': today}] if username else [],
                            'groups_seen': {str(group_id): group_name}
                        }
                        db.save_member(user_id, new_data)
                        saved_new += 1
                        
                except Exception as e:
                    # بعض القروبات قد لا نملك صلاحية جلب الأعضاء
                    pass
            
            await msg.edit(f"""
✅ **تم الفحص**

📊 القروبات: **{total_groups}**
👥 الأعضاء: **{total_members}**
💾 جدد محفوظين: **{saved_new}**
""")
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
    @client.on(events.NewMessage(pattern=r'^\.احصائيات$'))
    async def stats(event):
        """إحصائيات الأعضاء المحفوظين"""
        if not event.out:
            return
        
        try:
            count = db.get_members_count()
            await event.edit(f"📊 **الإحصائيات**\n\n👥 الأعضاء المحفوظين: **{count}**")
        except:
            await event.edit("❌ خطأ في جلب الإحصائيات")
    
    @client.on(events.NewMessage(pattern=r'^\.تصدير$'))
    async def export_members(event):
        """تصدير كل الأعضاء في ملف"""
        if not event.out:
            return
        
        await event.edit("⏳ **جاري تصدير الأعضاء...**")
        
        try:
            members = db.get_all_members()
            
            if not members:
                await event.edit("❌ لا يوجد أعضاء محفوظين.")
                return
            
            # إنشاء محتوى الملف
            content = f"📊 تصدير الأعضاء - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            content += f"👥 العدد الإجمالي: {len(members)}\n"
            content += "━" * 40 + "\n\n"
            
            for m in members:
                user_id = m.get('user_id', '؟')
                full_name = m.get('full_name', 'بدون اسم')
                username = m.get('username', '')
                username_text = f"@{username}" if username else "بدون يوزر"
                first_seen = m.get('first_seen', '؟')
                last_seen = m.get('last_seen', '؟')
                
                content += f"🆔 {user_id}\n"
                content += f"👤 {full_name}\n"
                content += f"📧 {username_text}\n"
                content += f"📅 أول ظهور: {first_seen}\n"
                content += f"📅 آخر ظهور: {last_seen}\n"
                
                # تاريخ الأسماء
                name_history = m.get('name_history', [])
                if name_history and len(name_history) > 1:
                    content += "\n📝 تاريخ الأسماء:\n"
                    for entry in name_history:
                        content += f"  • {entry.get('name', '؟')} ({entry.get('date', '؟')})\n"
                
                # تاريخ اليوزرات
                username_history = m.get('username_history', [])
                if username_history and len(username_history) > 1:
                    content += "\n📧 تاريخ اليوزرات:\n"
                    for entry in username_history:
                        uname = entry.get('username') or 'بدون'
                        content += f"  • @{uname} ({entry.get('date', '؟')})\n"
                
                # القروبات
                groups_seen = m.get('groups_seen', {})
                if groups_seen:
                    content += "\n📍 القروبات:\n"
                    for gid, gname in groups_seen.items():
                        content += f"  • {gname} ({gid})\n"
                
                content += "\n" + "━" * 40 + "\n\n"
            
            # حفظ الملف
            filename = f"members_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # إرسال الملف
            await event.delete()
            await client.send_file(
                event.chat_id,
                filename,
                caption=f"📊 **تصدير الأعضاء**\n👥 العدد: **{len(members)}**"
            )
            
            # حذف الملف
            import os
            os.remove(filename)
            
        except Exception as e:
            await event.edit(f"❌ خطأ: {e}")
    
    @client.on(events.NewMessage(pattern=r'^\.تصدير (-?\d+)$'))
    async def export_group_members(event):
        """تصدير أعضاء قروب معين"""
        if not event.out:
            return
        
        group_id = event.pattern_match.group(1)
        await event.edit(f"⏳ **جاري تصدير أعضاء القروب {group_id}...**")
        
        try:
            members = db.get_group_members(group_id)
            
            if not members:
                await event.edit(f"❌ لا يوجد أعضاء محفوظين للقروب {group_id}")
                return
            
            # إنشاء محتوى الملف
            content = f"📊 تصدير أعضاء القروب: {group_id}\n"
            content += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            content += f"👥 العدد: {len(members)}\n"
            content += "━" * 40 + "\n\n"
            
            for m in members:
                user_id = m.get('user_id', '؟')
                full_name = m.get('full_name', 'بدون اسم')
                username = m.get('username', '')
                username_text = f"@{username}" if username else "بدون يوزر"
                first_seen = m.get('first_seen', '؟')
                last_seen = m.get('last_seen', '؟')
                
                content += f"🆔 {user_id}\n"
                content += f"👤 {full_name}\n"
                content += f"📧 {username_text}\n"
                content += f"📅 أول ظهور: {first_seen}\n"
                content += f"📅 آخر ظهور: {last_seen}\n"
                
                # تاريخ الأسماء
                name_history = m.get('name_history', [])
                if name_history and len(name_history) > 1:
                    content += "\n📝 تاريخ الأسماء:\n"
                    for entry in name_history:
                        content += f"  • {entry.get('name', '؟')} ({entry.get('date', '؟')})\n"
                
                # تاريخ اليوزرات
                username_history = m.get('username_history', [])
                if username_history and len(username_history) > 1:
                    content += "\n📧 تاريخ اليوزرات:\n"
                    for entry in username_history:
                        uname = entry.get('username') or 'بدون'
                        content += f"  • @{uname} ({entry.get('date', '؟')})\n"
                
                content += "\n" + "━" * 40 + "\n\n"
            
            # حفظ الملف
            filename = f"group_{group_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # إرسال الملف
            await event.delete()
            await client.send_file(
                event.chat_id,
                filename,
                caption=f"📊 **تصدير أعضاء القروب**\n🆔 `{group_id}`\n👥 العدد: **{len(members)}**"
            )
            
            # حذف الملف
            import os
            os.remove(filename)
            
        except Exception as e:
            await event.edit(f"❌ خطأ: {e}")
    
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
    
    @client.on(events.NewMessage(pattern=r'^\.جلب (.+)$'))
    async def fetch_from_telegram(event):
        """جلب معلومات من تيليجرام مباشرة"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        query = event.pattern_match.group(1).strip()
        msg = await event.reply("⏳ جاري الجلب من تيليجرام...")
        
        try:
            # محاولة جلب المستخدم من تيليجرام
            if query.isdigit():
                user = await client.get_entity(int(query))
            else:
                # إزالة @ إذا موجود
                query = query.replace("@", "")
                user = await client.get_entity(query)
            
            if not user:
                await msg.edit("❌ لم يتم العثور على المستخدم.")
                return
            
            user_id = user.id
            first_name = getattr(user, 'first_name', '') or ''
            last_name = getattr(user, 'last_name', '') or ''
            full_name = f"{first_name} {last_name}".strip() or 'بدون اسم'
            username = getattr(user, 'username', '') or ''
            phone = getattr(user, 'phone', '') or ''
            is_bot = getattr(user, 'bot', False)
            
            username_text = f"@{username}" if username else "بدون يوزر"
            
            # جلب الصورة الشخصية
            has_photo = "✅ نعم" if getattr(user, 'photo', None) else "❌ لا"
            
            # التحقق من قاعدة البيانات
            existing = db.get_member(user_id)
            in_db = "✅ محفوظ" if existing else "❌ غير محفوظ"
            
            text = f"""
**🌐 معلومات من تيليجرام**

🆔 `{user_id}`
👤 {full_name}
📧 {username_text}
📱 {phone if phone else 'مخفي'}
🤖 بوت: {'نعم' if is_bot else 'لا'}
🖼️ صورة: {has_photo}
💾 قاعدة البيانات: {in_db}
"""
            
            # حفظ في قاعدة البيانات إذا غير موجود
            if not existing and not is_bot:
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                today = datetime.now().strftime('%Y-%m-%d')
                
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
                    'username_history': [{'username': username, 'date': today}] if username else [],
                    'groups_seen': {},
                    'fetched': True,
                    'fetch_date': now
                }
                db.save_member(user_id, new_data)
                text += "\n✅ **تم حفظه في قاعدة البيانات!**"
            elif existing:
                # تحديث البيانات
                old_name = existing.get('full_name', '')
                old_username = existing.get('username', '')
                
                updated = False
                
                if old_name != full_name:
                    name_history = existing.get('name_history', [])
                    name_history.append({'name': full_name, 'date': datetime.now().strftime('%Y-%m-%d')})
                    existing['name_history'] = name_history
                    existing['full_name'] = full_name
                    existing['first_name'] = first_name
                    existing['last_name'] = last_name
                    updated = True
                
                if old_username != username:
                    username_history = existing.get('username_history', [])
                    username_history.append({'username': username, 'date': datetime.now().strftime('%Y-%m-%d')})
                    existing['username_history'] = username_history
                    existing['username'] = username
                    existing['username_lower'] = username.lower() if username else ''
                    updated = True
                
                if updated:
                    existing['last_seen'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                    db.save_member(user_id, existing)
                    text += "\n🔄 **تم تحديث البيانات!**"
            
            await msg.edit(text)
            
        except ValueError:
            await msg.edit("❌ يوزر غير صالح أو غير موجود.")
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
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

**🔧 اختبار:**
`.بنق` - تأكد أن البوت شغال
`.احصائيات` - عدد الأعضاء المحفوظين

**👤 استعلام:**
`.عضو 123456` - معلومات عضو
`.سجل 123456` - سجل تغييراته
`.نشاط 123456` - نشاط العضو في القروبات

**🔍 بحث:**
`.بحث 123456` - بحث بالآيدي (قاعدة البيانات)
`.بحث @user` - بحث باليوزر (قاعدة البيانات)
`.جلب @user` - جلب من تيليجرام مباشرة
`.بحث اسم:أحمد` - بحث بالاسم
`.بحث قروب:-123456` - بحث داخل قروب
`.بدون` - أعضاء بدون يوزرنيم
`.مشترك -123 -456` - مشتركين بين قروبين
`.اكثر قروبات` - أعضاء بأكثر قروبات

**📊 ملخص:**
`.ملخص` - ملخص تغييرات اليوم

**📤 تصدير:**
`.تصدير` - تصدير كل الأعضاء
`.تصدير -123456` - تصدير أعضاء قروب

**📥 استيراد:**
`.استيراد` - استيراد من ملف
`.استيراد -123456` - استيراد مع ربط قروب

**💾 نسخ احتياطي:**
`.نسخ` - إنشاء نسخة احتياطية
`.استعادة` - استعادة من نسخة (رد على ملف)

**⚙️ إدارة:**
`.تنظيف` - حذف البيانات القديمة
`.ربط` - ربط القروب للإشعارات
`.دبق` - وضع التشخيص
`.فحص` - فحص كل القروبات
"""
        await event.reply(text)
    
    # ═══════════════════════════════════════════════════════════
    # أوامر جديدة: نشاط، ملخص، بحث متقدم
    # ═══════════════════════════════════════════════════════════
    
    @client.on(events.NewMessage(pattern=r'^\.نشاط (\d+)$'))
    async def member_activity(event):
        """عرض نشاط عضو في القروبات"""
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
        
        groups_seen = member.get('groups_seen', {})
        username = member.get('username', '')
        username_text = f"@{username}" if username else "بدون يوزر"
        
        text = f"""
**📊 نشاط العضو**

🆔 `{user_id}`
👤 {member.get('full_name', 'بدون اسم')}
📧 {username_text}

**📍 القروبات ({len(groups_seen)}):**
"""
        if groups_seen:
            for gid, gname in list(groups_seen.items())[:20]:
                text += f"• {gname}\n  `{gid}`\n"
            if len(groups_seen) > 20:
                text += f"\n... و {len(groups_seen) - 20} قروب آخر"
        else:
            text += "لم يُشاهد في أي قروب بعد."
        
        await event.reply(text)
    
    @client.on(events.NewMessage(pattern=r'^\.ملخص$'))
    async def daily_summary(event):
        """ملخص تغييرات اليوم"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        msg = await event.reply("⏳ جاري جلب الملخص...")
        
        try:
            changes = db.get_today_changes()
            
            text = f"""
**📊 ملخص اليوم**

👥 أعضاء جدد: **{len(changes['new_members'])}**
📝 تغييرات اسم: **{len(changes['name_changes'])}**
📧 تغييرات يوزر: **{len(changes['username_changes'])}**
"""
            # آخر 5 أعضاء جدد
            if changes['new_members']:
                text += "\n**🆕 آخر الأعضاء الجدد:**\n"
                for m in changes['new_members'][:5]:
                    uname = f"@{m.get('username')}" if m.get('username') else ""
                    text += f"• {m.get('full_name')} {uname}\n"
            
            # آخر 5 تغييرات اسم
            if changes['name_changes']:
                text += "\n**📝 تغييرات الاسم:**\n"
                for m in changes['name_changes'][:5]:
                    text += f"• `{m.get('user_id')}` → {m.get('full_name')}\n"
            
            await msg.edit(text)
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
    @client.on(events.NewMessage(pattern=r'^\.بحث اسم:(.+)$'))
    async def search_by_name(event):
        """بحث بالاسم"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        query = event.pattern_match.group(1).strip()
        msg = await event.reply("⏳ جاري البحث...")
        
        try:
            results = db.search_by_name(query)
            
            if not results:
                await msg.edit(f"❌ لم يتم العثور على نتائج للاسم: {query}")
                return
            
            text = f"**🔍 نتائج البحث عن: {query}**\n"
            text += f"📊 عدد النتائج: {len(results)}\n\n"
            
            for m in results[:15]:
                uname = f"@{m.get('username')}" if m.get('username') else "بدون يوزر"
                text += f"🆔 `{m.get('user_id')}`\n👤 {m.get('full_name')}\n📧 {uname}\n\n"
            
            if len(results) > 15:
                text += f"... و {len(results) - 15} نتيجة أخرى"
            
            await msg.edit(text)
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
    @client.on(events.NewMessage(pattern=r'^\.بحث قروب:(-?\d+)(?:\s+(.+))?$'))
    async def search_in_group(event):
        """بحث داخل قروب معين"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        group_id = event.pattern_match.group(1)
        query = event.pattern_match.group(2)
        
        msg = await event.reply("⏳ جاري البحث...")
        
        try:
            results = db.search_in_group(group_id, query)
            
            if not results:
                await msg.edit(f"❌ لم يتم العثور على نتائج في القروب {group_id}")
                return
            
            text = f"**🔍 نتائج البحث في القروب**\n"
            text += f"🆔 `{group_id}`\n"
            if query:
                text += f"🔎 البحث: {query}\n"
            text += f"📊 عدد النتائج: {len(results)}\n\n"
            
            for m in results[:15]:
                uname = f"@{m.get('username')}" if m.get('username') else "بدون يوزر"
                text += f"• `{m.get('user_id')}` - {m.get('full_name')} {uname}\n"
            
            if len(results) > 15:
                text += f"\n... و {len(results) - 15} عضو آخر"
            
            await msg.edit(text)
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
    @client.on(events.NewMessage(pattern=r'^\.بدون$'))
    async def members_without_username(event):
        """أعضاء بدون يوزرنيم"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        msg = await event.reply("⏳ جاري البحث...")
        
        try:
            results = db.get_members_without_username()
            
            if not results:
                await msg.edit("✅ كل الأعضاء لديهم يوزرنيم!")
                return
            
            text = f"**👥 أعضاء بدون يوزرنيم**\n"
            text += f"📊 العدد: {len(results)}\n\n"
            
            for m in results[:20]:
                text += f"🆔 `{m.get('user_id')}` - {m.get('full_name')}\n"
            
            if len(results) > 20:
                text += f"\n... و {len(results) - 20} عضو آخر"
            
            await msg.edit(text)
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
    @client.on(events.NewMessage(pattern=r'^\.مشترك (-?\d+) (-?\d+)$'))
    async def common_members(event):
        """أعضاء مشتركين بين قروبين"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        group1 = event.pattern_match.group(1)
        group2 = event.pattern_match.group(2)
        
        msg = await event.reply("⏳ جاري المقارنة...")
        
        try:
            common = db.get_common_members(group1, group2)
            
            text = f"**🔗 الأعضاء المشتركين**\n"
            text += f"📍 القروب 1: `{group1}`\n"
            text += f"📍 القروب 2: `{group2}`\n"
            text += f"📊 المشتركين: **{len(common)}**\n\n"
            
            for m in common[:20]:
                uname = f"@{m.get('username')}" if m.get('username') else ""
                text += f"• `{m.get('user_id')}` - {m.get('full_name')} {uname}\n"
            
            if len(common) > 20:
                text += f"\n... و {len(common) - 20} عضو آخر"
            
            await msg.edit(text)
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
    @client.on(events.NewMessage(pattern=r'^\.اكثر قروبات$'))
    async def most_groups(event):
        """أعضاء بأكثر قروبات"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        msg = await event.reply("⏳ جاري البحث...")
        
        try:
            results = db.get_members_by_groups_count(20)
            
            if not results:
                await msg.edit("❌ لا توجد بيانات.")
                return
            
            text = "**🏆 أعضاء بأكثر قروبات**\n\n"
            
            for i, (count, m) in enumerate(results, 1):
                uname = f"@{m.get('username')}" if m.get('username') else ""
                text += f"**{i}.** {m.get('full_name')} {uname}\n"
                text += f"   🆔 `{m.get('user_id')}` | 📍 {count} قروب\n\n"
            
            await msg.edit(text)
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # نسخ احتياطي واستعادة
    # ═══════════════════════════════════════════════════════════
    
    @client.on(events.NewMessage(pattern=r'^\.نسخ$'))
    async def create_backup(event):
        """إنشاء نسخة احتياطية"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        msg = await event.reply("⏳ جاري إنشاء النسخة الاحتياطية...")
        
        try:
            backup = db.create_backup()
            
            if not backup:
                await msg.edit("❌ فشل في إنشاء النسخة الاحتياطية.")
                return
            
            # حفظ كملف JSON
            import json
            filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(backup, f, ensure_ascii=False, indent=2)
            
            members_count = len(backup.get('all_members', {}))
            
            await msg.delete()
            await client.send_file(
                event.chat_id,
                filename,
                caption=f"💾 **نسخة احتياطية**\n📅 {backup.get('backup_date')}\n👥 {members_count} عضو"
            )
            
            import os
            os.remove(filename)
            
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
    @client.on(events.NewMessage(pattern=r'^\.استعادة$'))
    async def restore_backup(event):
        """استعادة من نسخة احتياطية"""
        if not owner_id:
            return
        sender = await event.get_sender()
        if sender.id != owner_id and not event.out:
            return
        
        # التحقق من الرد على ملف
        reply = await event.get_reply_message()
        if not reply or not reply.file:
            await event.reply("❌ رد على ملف النسخة الاحتياطية (.json)")
            return
        
        msg = await event.reply("⏳ جاري الاستعادة...")
        
        try:
            import json
            
            # تحميل الملف
            file_data = await reply.download_media(bytes)
            backup = json.loads(file_data.decode('utf-8'))
            
            # التحقق من صحة الملف
            if 'all_members' not in backup:
                await msg.edit("❌ ملف غير صالح!")
                return
            
            # استعادة
            restored = db.restore_backup(backup)
            
            await msg.edit(f"✅ **تم الاستعادة بنجاح!**\n👥 {restored} عضو")
            
        except Exception as e:
            await msg.edit(f"❌ خطأ: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # استيراد الأعضاء من ملف
    # ═══════════════════════════════════════════════════════════
    
    def parse_import_file(content):
        """تحليل ملف الاستيراد بكل الصيغ المدعومة"""
        members = []
        
        # صيغة 1: نفس صيغة التصدير
        # 🆔 123456
        # 👤 Ahmed
        # 📧 @ahmed123
        pattern_export = re.compile(
            r'🆔\s*(\d+)\s*\n'
            r'👤\s*(.+?)\s*\n'
            r'📧\s*(@?\w+|بدون يوزر)',
            re.MULTILINE
        )
        
        for match in pattern_export.finditer(content):
            user_id = match.group(1)
            full_name = match.group(2).strip()
            username = match.group(3).strip()
            if username == 'بدون يوزر' or username.lower() == 'none':
                username = ''
            username = username.replace('@', '')
            members.append({
                'user_id': int(user_id),
                'full_name': full_name,
                'username': username
            })
        
        if members:
            return members
        
        # صيغة 2: CSV بسيط (user_id,name,username)
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('📊') or line.startswith('━'):
                continue
            
            # CSV: 123456,Ahmed,@ahmed123 أو 123456,Ahmed,ahmed123
            if ',' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    try:
                        user_id = int(parts[0].strip())
                        full_name = parts[1].strip() or 'بدون اسم'
                        username = parts[2].strip() if len(parts) > 2 else ''
                        username = username.replace('@', '')
                        if username.lower() in ['none', 'بدون', 'بدون يوزر', '']:
                            username = ''
                        members.append({
                            'user_id': user_id,
                            'full_name': full_name,
                            'username': username
                        })
                    except:
                        pass
                continue
            
            # صيغة 3: سطر واحد آيدي فقط
            if line.isdigit():
                members.append({
                    'user_id': int(line),
                    'full_name': 'بدون اسم',
                    'username': ''
                })
                continue
            
            # صيغة 4: آيدي مع مسافة ثم اسم
            # 123456 Ahmed @ahmed123
            match = re.match(r'^(\d+)\s+(.+?)(?:\s+@(\w+))?$', line)
            if match:
                members.append({
                    'user_id': int(match.group(1)),
                    'full_name': match.group(2).strip(),
                    'username': match.group(3) or ''
                })
        
        return members
    
    @client.on(events.NewMessage(incoming=False))
    async def import_members(event):
        """استيراد الأعضاء من ملف"""
        # تحقق من الكابشن
        if not event.message.file:
            return
        
        caption = event.message.message or ''
        
        # تحقق من أمر الاستيراد
        match = re.match(r'^\.استيراد(?:\s+(-?\d+))?$', caption)
        if not match:
            return
        
        group_id = match.group(1)  # آيدي القروب (اختياري)
        group_name = None
        
        # جلب اسم القروب إذا محدد
        if group_id:
            try:
                entity = await client.get_entity(int(group_id))
                group_name = getattr(entity, 'title', None) or str(group_id)
            except:
                group_name = str(group_id)
        
        msg = await event.reply("⏳ **جاري تحليل الملف...**")
        
        try:
            # تحميل الملف
            file_data = await event.message.download_media(bytes)
            
            # محاولة فك الترميز
            try:
                content = file_data.decode('utf-8')
            except:
                try:
                    content = file_data.decode('utf-8-sig')
                except:
                    content = file_data.decode('latin-1')
            
            # تحليل الملف
            members = parse_import_file(content)
            
            if not members:
                await msg.edit("❌ **لم يتم العثور على أعضاء في الملف!**\n\nالصيغ المدعومة:\n• صيغة التصدير\n• CSV: `id,name,username`\n• سطر لكل آيدي")
                return
            
            if len(members) > MAX_IMPORT_LIMIT:
                await msg.edit(f"❌ **الملف كبير جداً!**\n\nالحد الأقصى: {MAX_IMPORT_LIMIT} عضو\nالملف يحتوي: {len(members)} عضو")
                return
            
            await msg.edit(f"⏳ **جاري استيراد {len(members)} عضو...**")
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M')
            today = datetime.now().strftime('%Y-%m-%d')
            
            imported_new = 0
            updated = 0
            errors = 0
            
            for m in members:
                try:
                    user_id = m['user_id']
                    full_name = m['full_name']
                    username = m['username']
                    
                    # جلب البيانات القديمة
                    existing = db.get_member(user_id)
                    
                    if existing:
                        # تحديث مع حفظ السجل
                        old_name = existing.get('full_name', '')
                        old_username = existing.get('username', '')
                        
                        # تحديث سجل الأسماء
                        if full_name and full_name != 'بدون اسم' and old_name != full_name:
                            name_history = existing.get('name_history', [])
                            name_history.append({'name': full_name, 'date': today})
                            existing['name_history'] = name_history
                            existing['full_name'] = full_name
                        
                        # تحديث سجل اليوزرات
                        if username and old_username != username:
                            username_history = existing.get('username_history', [])
                            username_history.append({'username': username, 'date': today})
                            existing['username_history'] = username_history
                            existing['username'] = username
                            existing['username_lower'] = username.lower()
                        
                        # إضافة القروب
                        if group_id:
                            groups_seen = existing.get('groups_seen', {})
                            groups_seen[str(group_id)] = group_name
                            existing['groups_seen'] = groups_seen
                        
                        existing['last_seen'] = now
                        db.save_member(user_id, existing)
                        updated += 1
                    else:
                        # عضو جديد
                        new_data = {
                            'user_id': user_id,
                            'first_name': full_name.split()[0] if full_name else '',
                            'last_name': ' '.join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else '',
                            'full_name': full_name,
                            'username': username,
                            'username_lower': username.lower() if username else '',
                            'first_seen': now,
                            'last_seen': now,
                            'name_history': [{'name': full_name, 'date': today}],
                            'username_history': [{'username': username, 'date': today}] if username else [],
                            'groups_seen': {str(group_id): group_name} if group_id else {},
                            'imported': True,
                            'import_date': now
                        }
                        db.save_member(user_id, new_data)
                        imported_new += 1
                        
                except Exception as e:
                    errors += 1
            
            # النتيجة
            result = f"""
✅ **تم الاستيراد بنجاح!**

📊 **الملخص:**
• ✅ أعضاء جدد: **{imported_new}**
• 🔄 تم تحديثهم: **{updated}**
• ❌ أخطاء: **{errors}**
"""
            if group_id:
                result += f"\n📍 القروب: `{group_id}`"
            
            await msg.edit(result)
            
        except Exception as e:
            await msg.edit(f"❌ **خطأ:** {e}")
    
    print("✅ نظام الحفظ التلقائي جاهز")
