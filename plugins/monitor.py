"""
نظام مراقبة المجموعات 👁️
"""
import os
import json
import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.functions.messages import CreateChatRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import database as db

def register(client):
    """تسجيل أوامر المراقبة"""
    
    owner_id = os.environ.get('OWNER_ID')
    if owner_id:
        owner_id = int(owner_id)
    
    # ═══════════════════════════════════════════════════════════
    # أمر تفعيل المراقبة
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, pattern=r'^مراقبة$'))
    async def enable_monitoring(event):
        """تفعيل المراقبة في المجموعة"""
        chat = await event.get_chat()
        
        # التأكد أنها مجموعة
        if not hasattr(chat, 'title'):
            await event.edit("❌ هذا الأمر يعمل في المجموعات فقط!")
            return
        
        chat_id = event.chat_id
        chat_title = chat.title
        
        # التحقق إذا كانت المجموعة مراقبة مسبقاً
        existing = db.get_monitored_group(chat_id)
        if existing and existing.get('is_active'):
            await event.edit("⚠️ هذه المجموعة مراقبة مسبقاً!")
            return
        
        await event.edit("⏳ جاري إنشاء مجموعة المتغيرات...")
        
        try:
            # إنشاء مجموعة المتغيرات
            me = await client.get_me()
            log_group_title = f"متغيرات مجموعة {chat_title}"
            
            # إنشاء المجموعة
            await client(CreateChatRequest(
                users=[me.id],
                title=log_group_title
            ))
            
            # انتظار قليل ثم البحث عن المجموعة في الدردشات
            await asyncio.sleep(1)
            
            log_group_id = None
            dialogs = await client.get_dialogs(limit=10)
            for dialog in dialogs:
                if hasattr(dialog, 'title') and dialog.title == log_group_title:
                    log_group_id = dialog.id
                    break
            
            if not log_group_id:
                await event.edit("❌ تم إنشاء المجموعة لكن لم أستطع الحصول على آيديها. حاول مرة أخرى.")
                return
            
            # حفظ في قاعدة البيانات
            db.save_monitored_group(chat_id, {
                'group_id': chat_id,
                'group_title': chat_title,
                'log_group_id': log_group_id,
                'log_group_title': log_group_title,
                'is_active': True,
                'created_at': datetime.now().isoformat()
            })
            
            # إرسال رسالة ترحيبية في مجموعة المتغيرات
            welcome_msg = f"""
🎉 **تم إنشاء مجموعة المتغيرات**

📍 **المجموعة المراقبة:** {chat_title}
🆔 **آيدي المجموعة:** `{chat_id}`
⏰ **تاريخ التفعيل:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━━━━

سيتم إرسال التنبيهات هنا عند:
• 👋 ظهور عضو جديد
• 📝 تغيير اسم
• 📧 تغيير يوزر
"""
            await client.send_message(log_group_id, welcome_msg)
            
            await event.edit(f"""
✅ **تم تفعيل المراقبة بنجاح!**

📍 المجموعة: {chat_title}
📂 مجموعة المتغيرات: {log_group_title}

سيتم حفظ بيانات كل من يكتب وإرسال التنبيهات.
""")
            
        except Exception as e:
            await event.edit(f"❌ خطأ في إنشاء المجموعة: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════
    # أمر تفعيل المراقبة بالآيدي (يدوي)
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, pattern=r'^مراقبة (-?\d+)$'))
    async def enable_monitoring_by_id(event):
        """تفعيل المراقبة بالآيدي"""
        target_chat_id = int(event.pattern_match.group(1))
        
        await event.edit("⏳ جاري التحقق من المجموعة...")
        
        try:
            # جلب معلومات المجموعة
            chat = await client.get_entity(target_chat_id)
            
            if not hasattr(chat, 'title'):
                await event.edit("❌ هذا ليس مجموعة!")
                return
            
            chat_title = chat.title
            
            # التحقق إذا كانت مراقبة مسبقاً
            existing = db.get_monitored_group(target_chat_id)
            if existing and existing.get('is_active'):
                await event.edit(f"⚠️ المجموعة **{chat_title}** مراقبة مسبقاً!")
                return
            
            await event.edit(f"⏳ جاري إنشاء مجموعة المتغيرات لـ **{chat_title}**...")
            
            # إنشاء مجموعة المتغيرات
            me = await client.get_me()
            log_group_title = f"متغيرات مجموعة {chat_title}"
            
            await client(CreateChatRequest(
                users=[me.id],
                title=log_group_title
            ))
            
            await asyncio.sleep(1)
            
            log_group_id = None
            dialogs = await client.get_dialogs(limit=10)
            for dialog in dialogs:
                if hasattr(dialog, 'title') and dialog.title == log_group_title:
                    log_group_id = dialog.id
                    break
            
            if not log_group_id:
                await event.edit("❌ تم إنشاء المجموعة لكن لم أستطع الحصول على آيديها. حاول مرة أخرى.")
                return
            
            # حفظ في قاعدة البيانات
            db.save_monitored_group(target_chat_id, {
                'group_id': target_chat_id,
                'group_title': chat_title,
                'log_group_id': log_group_id,
                'log_group_title': log_group_title,
                'is_active': True,
                'created_at': datetime.now().isoformat()
            })
            
            # إرسال رسالة ترحيبية
            welcome_msg = f"""
🎉 **تم إنشاء مجموعة المتغيرات**

📍 **المجموعة المراقبة:** {chat_title}
🆔 **آيدي المجموعة:** `{target_chat_id}`
⏰ **تاريخ التفعيل:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━━━━

سيتم إرسال التنبيهات هنا عند:
• 👋 ظهور عضو جديد
• 🚪 انضمام عضو
• 📝 تغيير اسم
• 📧 تغيير يوزر
"""
            await client.send_message(log_group_id, welcome_msg)
            
            await event.edit(f"""
✅ **تم تفعيل المراقبة بنجاح!**

📍 المجموعة: {chat_title}
🆔 الآيدي: `{target_chat_id}`
📂 مجموعة المتغيرات: {log_group_title}

سيتم حفظ بيانات كل من يكتب وإرسال التنبيهات.
""")
            
        except ValueError:
            await event.edit("❌ لم أجد هذه المجموعة. تأكد أنك عضو فيها.")
        except Exception as e:
            await event.edit(f"❌ خطأ: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════
    # أمر إلغاء المراقبة
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, pattern=r'^الغاء مراقبة$'))
    async def disable_monitoring(event):
        """إلغاء المراقبة"""
        chat_id = event.chat_id
        
        group_data = db.get_monitored_group(chat_id)
        if not group_data:
            await event.edit("❌ هذه المجموعة غير مراقبة!")
            return
        
        db.update_monitored_group(chat_id, {'is_active': False})
        
        await event.edit(f"""
✅ **تم إلغاء المراقبة**

📍 المجموعة: {group_data.get('group_title', 'غير معروف')}

ملاحظة: البيانات المحفوظة لم تُحذف.
""")
    
    # ═══════════════════════════════════════════════════════════
    # أمر فحص جميع الأعضاء
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, pattern=r'^فحص اعضاء$'))
    async def scan_all_members(event):
        """فحص وحفظ جميع أعضاء المجموعة"""
        chat_id = event.chat_id
        
        # التحقق من المجموعة
        group_data = db.get_monitored_group(chat_id)
        if not group_data:
            group_data = db.get_monitored_group_by_log_id(chat_id)
            if group_data:
                chat_id = group_data.get('group_id')
            else:
                await event.edit("❌ هذه المجموعة غير مراقبة! فعّل المراقبة أولاً بأمر `مراقبة`")
                return
        
        await event.edit("⏳ **جاري فحص الأعضاء...**\nقد يستغرق بعض الوقت...")
        
        try:
            # جلب جميع الأعضاء
            all_participants = []
            offset = 0
            limit = 100
            
            while True:
                participants = await client(GetParticipantsRequest(
                    chat_id,
                    ChannelParticipantsSearch(''),
                    offset,
                    limit,
                    hash=0
                ))
                
                if not participants.users:
                    break
                
                all_participants.extend(participants.users)
                offset += len(participants.users)
                
                # تحديث الرسالة كل 200 عضو
                if offset % 200 == 0:
                    await event.edit(f"⏳ **جاري فحص الأعضاء...**\nتم جلب {offset} عضو...")
                
                # تأخير لتجنب الحظر
                await asyncio.sleep(0.5)
                
                if len(participants.users) < limit:
                    break
            
            # حفظ الأعضاء
            now = datetime.now().strftime('%Y-%m-%d %H:%M')
            today = datetime.now().strftime('%Y-%m-%d')
            saved_count = 0
            new_count = 0
            
            for user in all_participants:
                if user.bot:  # تجاهل البوتات
                    continue
                
                user_id = user.id
                first_name = getattr(user, 'first_name', '') or ''
                last_name = getattr(user, 'last_name', '') or ''
                full_name = f"{first_name} {last_name}".strip() or 'بدون اسم'
                username = getattr(user, 'username', '') or ''
                
                # التحقق إذا موجود
                existing = db.get_member(chat_id, user_id)
                
                if existing:
                    # تحديث فقط
                    existing['full_name'] = full_name
                    existing['first_name'] = first_name
                    existing['last_name'] = last_name
                    existing['username'] = username
                    existing['last_seen'] = now
                    db.save_member(chat_id, user_id, existing)
                else:
                    # عضو جديد
                    new_member = {
                        'user_id': user_id,
                        'first_name': first_name,
                        'last_name': last_name,
                        'full_name': full_name,
                        'username': username,
                        'first_seen': now,
                        'last_seen': now,
                        'message_count': 0,
                        'name_history': [{'name': full_name, 'date': today}],
                        'username_history': [{'username': username, 'date': today}] if username else []
                    }
                    db.save_member(chat_id, user_id, new_member)
                    new_count += 1
                
                saved_count += 1
            
            await event.edit(f"""
✅ **تم فحص الأعضاء بنجاح!**

📊 **النتائج:**
👥 إجمالي الأعضاء: {len(all_participants)}
✅ تم حفظ/تحديث: {saved_count}
🆕 أعضاء جدد: {new_count}
🤖 بوتات (تم تجاهلها): {len(all_participants) - saved_count}
""")
            
            # إرسال إشعار في مجموعة المتغيرات
            log_group_id = group_data.get('log_group_id')
            if log_group_id:
                try:
                    await client.send_message(log_group_id, f"""
📊 **تم فحص الأعضاء**

👥 إجمالي: {len(all_participants)}
🆕 جدد: {new_count}
⏰ {now}
""")
                except:
                    pass
                    
        except Exception as e:
            await event.edit(f"❌ خطأ في فحص الأعضاء: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════
    # مراقبة الانضمام للمجموعة
    # ═══════════════════════════════════════════════════════════
    @client.on(events.ChatAction())
    async def on_user_join(event):
        """حفظ الأعضاء عند الانضمام"""
        # فقط عند الانضمام
        if not event.user_joined and not event.user_added:
            return
        
        chat_id = event.chat_id
        
        # التحقق إذا المجموعة مراقبة
        group_data = db.get_monitored_group(chat_id)
        if not group_data or not group_data.get('is_active'):
            return
        
        try:
            user = await event.get_user()
            if not user or user.bot:
                return
            
            user_id = user.id
            first_name = getattr(user, 'first_name', '') or ''
            last_name = getattr(user, 'last_name', '') or ''
            full_name = f"{first_name} {last_name}".strip() or 'بدون اسم'
            username = getattr(user, 'username', '') or ''
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M')
            today = datetime.now().strftime('%Y-%m-%d')
            
            # التحقق إذا موجود
            existing = db.get_member(chat_id, user_id)
            
            if not existing:
                # عضو جديد
                new_member = {
                    'user_id': user_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'full_name': full_name,
                    'username': username,
                    'first_seen': now,
                    'last_seen': now,
                    'message_count': 0,
                    'joined_at': now,
                    'name_history': [{'name': full_name, 'date': today}],
                    'username_history': [{'username': username, 'date': today}] if username else []
                }
                db.save_member(chat_id, user_id, new_member)
                
                # إرسال إشعار
                log_group_id = group_data.get('log_group_id')
                if log_group_id:
                    username_text = f"@{username}" if username else "بدون يوزر"
                    alert = f"""
🚪 **انضمام جديد**
━━━━━━━━━━━━━━

🆔 `{user_id}`
👤 {full_name}
📧 {username_text}
⏰ {now}
"""
                    try:
                        await client.send_message(log_group_id, alert)
                    except:
                        pass
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════
    # أمر عرض المجموعات المراقبة
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, pattern=r'^المجموعات$'))
    async def list_groups(event):
        """عرض المجموعات المراقبة"""
        groups = db.get_all_monitored_groups()
        
        if not groups:
            await event.edit("📭 لا توجد مجموعات مراقبة حالياً.")
            return
        
        text = "**📋 المجموعات المراقبة:**\n\n"
        
        for i, group in enumerate(groups, 1):
            status = "🟢" if group.get('is_active') else "🔴"
            text += f"{status} **{i}.** {group.get('group_title', 'بدون اسم')}\n"
            text += f"    🆔 `{group.get('group_id')}`\n"
            text += f"    📂 {group.get('log_group_title', 'غير متاح')}\n\n"
        
        await event.edit(text)
    
    # ═══════════════════════════════════════════════════════════
    # أمر عرض الأعضاء
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, pattern=r'^اعضاء$'))
    async def list_members(event):
        """عرض أعضاء المجموعة المحفوظين"""
        chat_id = event.chat_id
        
        # التحقق من المجموعة (قد تكون المراقبة أو المتغيرات)
        group_data = db.get_monitored_group(chat_id)
        if not group_data:
            # ربما نحن في مجموعة المتغيرات
            group_data = db.get_monitored_group_by_log_id(chat_id)
            if group_data:
                chat_id = group_data.get('group_id')
            else:
                await event.edit("❌ هذه المجموعة غير مراقبة!")
                return
        
        members = db.get_group_members(chat_id)
        
        if not members:
            await event.edit("📭 لا يوجد أعضاء محفوظين بعد.")
            return
        
        text = f"**👥 الأعضاء المحفوظين ({len(members)}):**\n\n"
        
        for i, member in enumerate(members[:50], 1):  # أول 50 فقط
            name = member.get('full_name', 'بدون اسم')
            username = member.get('username', '')
            username_text = f"@{username}" if username else "بدون يوزر"
            text += f"**{i}.** {name}\n"
            text += f"    🆔 `{member.get('user_id')}`\n"
            text += f"    📧 {username_text}\n\n"
        
        if len(members) > 50:
            text += f"\n... و {len(members) - 50} عضو آخر"
        
        await event.edit(text)
    
    # ═══════════════════════════════════════════════════════════
    # أمر عرض تفاصيل عضو
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, pattern=r'^عضو (\d+)$'))
    async def member_info(event):
        """عرض تفاصيل عضو"""
        user_id = int(event.pattern_match.group(1))
        
        member = db.get_member_info(user_id)
        
        if not member:
            await event.edit("❌ لم يتم العثور على هذا العضو في السجلات.")
            return
        
        username = member.get('username', '')
        username_text = f"@{username}" if username else "بدون يوزر"
        
        text = f"""
**👤 معلومات العضو**

🆔 **الآيدي:** `{member.get('user_id')}`
👤 **الاسم:** {member.get('full_name', 'بدون اسم')}
📧 **اليوزر:** {username_text}

📅 **أول ظهور:** {member.get('first_seen', 'غير معروف')}
📅 **آخر ظهور:** {member.get('last_seen', 'غير معروف')}
💬 **عدد الرسائل:** {member.get('message_count', 0)}
"""
        await event.edit(text)
    
    # ═══════════════════════════════════════════════════════════
    # أمر عرض سجل التغييرات
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, pattern=r'^سجل (\d+)$'))
    async def member_history(event):
        """عرض سجل تغييرات عضو"""
        user_id = int(event.pattern_match.group(1))
        
        member = db.get_member_info(user_id)
        
        if not member:
            await event.edit("❌ لم يتم العثور على هذا العضو في السجلات.")
            return
        
        text = f"""
**📜 سجل تغييرات العضو**

🆔 **الآيدي:** `{user_id}`
👤 **الاسم الحالي:** {member.get('full_name', 'بدون اسم')}

"""
        # سجل الأسماء
        name_history = member.get('name_history', [])
        if name_history:
            text += "**📝 سجل الأسماء:**\n"
            for entry in name_history[-10:]:  # آخر 10
                text += f"• {entry.get('name')} ({entry.get('date')})\n"
            text += "\n"
        
        # سجل اليوزرات
        username_history = member.get('username_history', [])
        if username_history:
            text += "**📧 سجل اليوزرات:**\n"
            for entry in username_history[-10:]:
                uname = entry.get('username') or 'بدون يوزر'
                text += f"• @{uname} ({entry.get('date')})\n"
        
        if not name_history and not username_history:
            text += "لا توجد تغييرات مسجلة بعد."
        
        await event.edit(text)
    
    # ═══════════════════════════════════════════════════════════
    # أمر تصدير البيانات
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, pattern=r'^تصدير$'))
    async def export_data(event):
        """تصدير بيانات المجموعة"""
        chat_id = event.chat_id
        
        group_data = db.get_monitored_group(chat_id)
        if not group_data:
            group_data = db.get_monitored_group_by_log_id(chat_id)
            if group_data:
                chat_id = group_data.get('group_id')
            else:
                await event.edit("❌ هذه المجموعة غير مراقبة!")
                return
        
        members = db.get_group_members(chat_id)
        
        if not members:
            await event.edit("📭 لا يوجد أعضاء لتصديرهم.")
            return
        
        await event.edit("⏳ جاري إعداد الملفات...")
        
        group_title = group_data.get('group_title', 'مجموعة')
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # إنشاء ملف TXT
        txt_content = f"مجموعة: {group_title}\n"
        txt_content += f"التاريخ: {date_str}\n"
        txt_content += f"عدد الأعضاء: {len(members)}\n"
        txt_content += "=" * 50 + "\n\n"
        
        for member in members:
            txt_content += f"الآيدي: {member.get('user_id')}\n"
            txt_content += f"الاسم: {member.get('full_name', 'بدون اسم')}\n"
            txt_content += f"اليوزر: @{member.get('username', 'بدون')}\n"
            txt_content += f"أول ظهور: {member.get('first_seen', 'غير معروف')}\n"
            txt_content += f"آخر ظهور: {member.get('last_seen', 'غير معروف')}\n"
            txt_content += f"عدد الرسائل: {member.get('message_count', 0)}\n"
            txt_content += "-" * 30 + "\n"
        
        # حفظ وإرسال الملفات
        txt_filename = f"members_{date_str}.txt"
        json_filename = f"members_{date_str}.json"
        csv_filename = f"members_{date_str}.csv"
        
        # TXT
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        # JSON
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(members, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_content = "الآيدي,الاسم,اليوزر,أول ظهور,آخر ظهور,عدد الرسائل\n"
        for member in members:
            csv_content += f"{member.get('user_id')},"
            csv_content += f"{member.get('full_name', 'بدون اسم')},"
            csv_content += f"@{member.get('username', 'بدون')},"
            csv_content += f"{member.get('first_seen', '')},"
            csv_content += f"{member.get('last_seen', '')},"
            csv_content += f"{member.get('message_count', 0)}\n"
        
        with open(csv_filename, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # إرسال الملفات
        await client.send_file(
            event.chat_id,
            [txt_filename, json_filename, csv_filename],
            caption=f"📊 **تصدير بيانات:** {group_title}\n📅 التاريخ: {date_str}\n👥 عدد الأعضاء: {len(members)}"
        )
        
        await event.delete()
        
        # حذف الملفات المؤقتة
        import os
        os.remove(txt_filename)
        os.remove(json_filename)
        os.remove(csv_filename)
    
    # ═══════════════════════════════════════════════════════════
    # مراقبة الرسائل الواردة (تسجيل الأعضاء)
    # ═══════════════════════════════════════════════════════════
    @client.on(events.NewMessage())
    async def monitor_messages(event):
        """مراقبة الرسائل وتسجيل الأعضاء"""
        # تجاهل الرسائل الصادرة
        if event.out:
            return
        
        chat_id = event.chat_id
        
        # التحقق إذا كانت المجموعة مراقبة
        group_data = db.get_monitored_group(chat_id)
        if not group_data or not group_data.get('is_active'):
            return
        
        sender = await event.get_sender()
        if not sender or not hasattr(sender, 'id'):
            return
        
        user_id = sender.id
        first_name = getattr(sender, 'first_name', '') or ''
        last_name = getattr(sender, 'last_name', '') or ''
        full_name = f"{first_name} {last_name}".strip() or 'بدون اسم'
        username = getattr(sender, 'username', '') or ''
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # جلب البيانات القديمة
        old_data = db.get_member(chat_id, user_id)
        
        if old_data:
            # عضو موجود - تحديث البيانات
            changes = []
            
            old_name = old_data.get('full_name', '')
            old_username = old_data.get('username', '')
            
            # التحقق من تغيير الاسم
            if old_name and old_name != full_name:
                changes.append({
                    'type': 'name',
                    'old': old_name,
                    'new': full_name
                })
                # إضافة للسجل
                name_history = old_data.get('name_history', [])
                name_history.append({'name': full_name, 'date': today})
                old_data['name_history'] = name_history
            
            # التحقق من تغيير اليوزر
            if old_username != username:
                changes.append({
                    'type': 'username',
                    'old': old_username,
                    'new': username
                })
                # إضافة للسجل
                username_history = old_data.get('username_history', [])
                username_history.append({'username': username, 'date': today})
                old_data['username_history'] = username_history
            
            # تحديث البيانات
            old_data['full_name'] = full_name
            old_data['first_name'] = first_name
            old_data['last_name'] = last_name
            old_data['username'] = username
            old_data['last_seen'] = now
            old_data['message_count'] = old_data.get('message_count', 0) + 1
            
            db.save_member(chat_id, user_id, old_data)
            
            # إرسال إشعارات التغيير
            if changes:
                log_group_id = group_data.get('log_group_id')
                if log_group_id:
                    for change in changes:
                        if change['type'] == 'name':
                            alert = f"""
📝 **تغيير اسم**
━━━━━━━━━━━━━━

🆔 `{user_id}`
👤 {change['old']} ← **{change['new']}**
📧 @{username if username else 'بدون يوزر'}
⏰ {now}
"""
                        else:
                            old_u = f"@{change['old']}" if change['old'] else "بدون يوزر"
                            new_u = f"@{change['new']}" if change['new'] else "بدون يوزر"
                            alert = f"""
📧 **تغيير يوزر**
━━━━━━━━━━━━━━

🆔 `{user_id}`
👤 {full_name}
📧 {old_u} ← **{new_u}**
⏰ {now}
"""
                        try:
                            await client.send_message(log_group_id, alert)
                        except:
                            pass
        
        else:
            # عضو جديد
            new_member = {
                'user_id': user_id,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name,
                'username': username,
                'first_seen': now,
                'last_seen': now,
                'message_count': 1,
                'name_history': [{'name': full_name, 'date': today}],
                'username_history': [{'username': username, 'date': today}] if username else []
            }
            
            db.save_member(chat_id, user_id, new_member)
            
            # إرسال إشعار عضو جديد
            log_group_id = group_data.get('log_group_id')
            if log_group_id:
                username_text = f"@{username}" if username else "بدون يوزر"
                alert = f"""
👋 **عضو جديد**
━━━━━━━━━━━━━━

🆔 `{user_id}`
👤 {full_name}
📧 {username_text}
⏰ {now}
"""
                try:
                    await client.send_message(log_group_id, alert)
                except:
                    pass
    
    # ═══════════════════════════════════════════════════════════
    # أوامر التحكم عن بُعد
    # ═══════════════════════════════════════════════════════════
    if owner_id:
        @client.on(events.NewMessage(incoming=True, pattern=r'^\.المجموعات$'))
        async def remote_list_groups(event):
            """عرض المجموعات - عن بُعد"""
            sender = await event.get_sender()
            if sender.id != owner_id:
                return
            
            groups = db.get_all_monitored_groups()
            
            if not groups:
                await event.reply("📭 لا توجد مجموعات مراقبة حالياً.")
                return
            
            text = "**📋 المجموعات المراقبة:**\n\n"
            
            for i, group in enumerate(groups, 1):
                status = "🟢" if group.get('is_active') else "🔴"
                text += f"{status} **{i}.** {group.get('group_title', 'بدون اسم')}\n"
                text += f"    🆔 `{group.get('group_id')}`\n\n"
            
            await event.reply(text)
        
        @client.on(events.NewMessage(incoming=True, pattern=r'^\.اعضاء (-?\d+)$'))
        async def remote_list_members(event):
            """عرض أعضاء مجموعة - عن بُعد"""
            sender = await event.get_sender()
            if sender.id != owner_id:
                return
            
            chat_id = int(event.pattern_match.group(1))
            members = db.get_group_members(chat_id)
            
            if not members:
                await event.reply("📭 لا يوجد أعضاء محفوظين.")
                return
            
            text = f"**👥 الأعضاء ({len(members)}):**\n\n"
            
            for i, member in enumerate(members[:30], 1):
                name = member.get('full_name', 'بدون اسم')
                text += f"**{i}.** {name} - `{member.get('user_id')}`\n"
            
            if len(members) > 30:
                text += f"\n... و {len(members) - 30} عضو آخر"
            
            await event.reply(text)
        
        @client.on(events.NewMessage(incoming=True, pattern=r'^\.عضو (\d+)$'))
        async def remote_member_info(event):
            """تفاصيل عضو - عن بُعد"""
            sender = await event.get_sender()
            if sender.id != owner_id:
                return
            
            user_id = int(event.pattern_match.group(1))
            member = db.get_member_info(user_id)
            
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
📅 أول ظهور: {member.get('first_seen', 'غير معروف')}
📅 آخر ظهور: {member.get('last_seen', 'غير معروف')}
💬 الرسائل: {member.get('message_count', 0)}
"""
            await event.reply(text)
        
        @client.on(events.NewMessage(incoming=True, pattern=r'^\.سجل (\d+)$'))
        async def remote_member_history(event):
            """سجل تغييرات عضو - عن بُعد"""
            sender = await event.get_sender()
            if sender.id != owner_id:
                return
            
            user_id = int(event.pattern_match.group(1))
            member = db.get_member_info(user_id)
            
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
            
            await event.reply(text)
        
        @client.on(events.NewMessage(incoming=True, pattern=r'^\.مراقبة (-?\d+)$'))
        async def remote_enable_monitoring(event):
            """تفعيل المراقبة بالآيدي - عن بُعد"""
            sender = await event.get_sender()
            if sender.id != owner_id:
                return
            
            target_chat_id = int(event.pattern_match.group(1))
            
            msg = await event.reply("⏳ جاري التحقق من المجموعة...")
            
            try:
                # جلب معلومات المجموعة
                chat = await client.get_entity(target_chat_id)
                
                if not hasattr(chat, 'title'):
                    await msg.edit("❌ هذا ليس مجموعة!")
                    return
                
                chat_title = chat.title
                
                # التحقق إذا كانت مراقبة مسبقاً
                existing = db.get_monitored_group(target_chat_id)
                if existing and existing.get('is_active'):
                    await msg.edit(f"⚠️ المجموعة **{chat_title}** مراقبة مسبقاً!")
                    return
                
                await msg.edit(f"⏳ جاري إنشاء مجموعة المتغيرات لـ **{chat_title}**...")
                
                # إنشاء مجموعة المتغيرات
                me = await client.get_me()
                log_group_title = f"متغيرات مجموعة {chat_title}"
                
                await client(CreateChatRequest(
                    users=[me.id],
                    title=log_group_title
                ))
                
                await asyncio.sleep(1)
                
                log_group_id = None
                dialogs = await client.get_dialogs(limit=10)
                for dialog in dialogs:
                    if hasattr(dialog, 'title') and dialog.title == log_group_title:
                        log_group_id = dialog.id
                        break
                
                if not log_group_id:
                    await msg.edit("❌ تم إنشاء المجموعة لكن لم أستطع الحصول على آيديها.")
                    return
                
                # حفظ في قاعدة البيانات
                db.save_monitored_group(target_chat_id, {
                    'group_id': target_chat_id,
                    'group_title': chat_title,
                    'log_group_id': log_group_id,
                    'log_group_title': log_group_title,
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                })
                
                # إرسال رسالة ترحيبية
                welcome_msg = f"""
🎉 **تم إنشاء مجموعة المتغيرات**

📍 **المجموعة المراقبة:** {chat_title}
🆔 **آيدي المجموعة:** `{target_chat_id}`
⏰ **تاريخ التفعيل:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎮 **تم التفعيل عن بُعد**

━━━━━━━━━━━━━━━━━━━━━

سيتم إرسال التنبيهات هنا.
"""
                await client.send_message(log_group_id, welcome_msg)
                
                await msg.edit(f"""
✅ **تم تفعيل المراقبة بنجاح!**

📍 المجموعة: {chat_title}
🆔 الآيدي: `{target_chat_id}`
📂 مجموعة المتغيرات: {log_group_title}
""")
                
            except ValueError:
                await msg.edit("❌ لم أجد هذه المجموعة. تأكد أن الحساب عضو فيها.")
            except Exception as e:
                await msg.edit(f"❌ خطأ: {str(e)}")
        
        @client.on(events.NewMessage(incoming=True, pattern=r'^\.فحص (-?\d+)$'))
        async def remote_scan_members(event):
            """فحص أعضاء مجموعة بالآيدي - عن بُعد"""
            sender = await event.get_sender()
            if sender.id != owner_id:
                return
            
            target_chat_id = int(event.pattern_match.group(1))
            
            # التحقق من المجموعة
            group_data = db.get_monitored_group(target_chat_id)
            if not group_data:
                await event.reply("❌ هذه المجموعة غير مراقبة! فعّل المراقبة أولاً.")
                return
            
            msg = await event.reply("⏳ **جاري فحص الأعضاء...**")
            
            try:
                all_participants = []
                offset = 0
                limit = 100
                
                while True:
                    participants = await client(GetParticipantsRequest(
                        target_chat_id,
                        ChannelParticipantsSearch(''),
                        offset,
                        limit,
                        hash=0
                    ))
                    
                    if not participants.users:
                        break
                    
                    all_participants.extend(participants.users)
                    offset += len(participants.users)
                    await asyncio.sleep(0.5)
                    
                    if len(participants.users) < limit:
                        break
                
                # حفظ الأعضاء
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                today = datetime.now().strftime('%Y-%m-%d')
                saved_count = 0
                new_count = 0
                
                for user in all_participants:
                    if user.bot:
                        continue
                    
                    user_id = user.id
                    first_name = getattr(user, 'first_name', '') or ''
                    last_name = getattr(user, 'last_name', '') or ''
                    full_name = f"{first_name} {last_name}".strip() or 'بدون اسم'
                    username = getattr(user, 'username', '') or ''
                    
                    existing = db.get_member(target_chat_id, user_id)
                    
                    if existing:
                        existing['full_name'] = full_name
                        existing['username'] = username
                        existing['last_seen'] = now
                        db.save_member(target_chat_id, user_id, existing)
                    else:
                        new_member = {
                            'user_id': user_id,
                            'first_name': first_name,
                            'last_name': last_name,
                            'full_name': full_name,
                            'username': username,
                            'first_seen': now,
                            'last_seen': now,
                            'message_count': 0,
                            'name_history': [{'name': full_name, 'date': today}],
                            'username_history': [{'username': username, 'date': today}] if username else []
                        }
                        db.save_member(target_chat_id, user_id, new_member)
                        new_count += 1
                    
                    saved_count += 1
                
                await msg.edit(f"""
✅ **تم فحص الأعضاء!**

👥 إجمالي: {len(all_participants)}
✅ حفظ/تحديث: {saved_count}
🆕 جدد: {new_count}
""")
                
            except Exception as e:
                await msg.edit(f"❌ خطأ: {str(e)}")
    
    print("✅ تم تحميل نظام المراقبة")
