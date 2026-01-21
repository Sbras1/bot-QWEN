"""
نظام الحفظ التلقائي 📦
يحفظ كل من يرسل في أي مجموعة + إشعارات التغييرات
"""
import os
import asyncio
from datetime import datetime
from telethon import events
import database as db

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
                            'username_history': [{'username': username, 'date': today}] if username else []
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

**🔧 اختبار:**
`.بنق` - تأكد أن البوت شغال
`.احصائيات` - عدد الأعضاء المحفوظين

**👤 استعلام:**
`.عضو 123456` - معلومات عضو
`.سجل 123456` - سجل تغييراته
`.بحث 123456` - بحث بالآيدي
`.بحث @user` - بحث باليوزر

**📤 تصدير:**
`.تصدير` - تصدير كل الأعضاء في ملف

**⚙️ إدارة:**
`.تنظيف` - حذف البيانات القديمة
`.اوامر` - عرض الأوامر

**ℹ️ ملاحظة:**
الحفظ تلقائي + إشعارات التغييرات للقروب المركزي.
"""
        await event.reply(text)
    
    print("✅ نظام الحفظ التلقائي جاهز")
