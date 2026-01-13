"""
أوامر البحث 🔍
"""
import asyncio
from telethon import events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import GetCommonChatsRequest

def register(client):
    """تسجيل أوامر البحث"""
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'بحث (\d+)'))
    async def search_command(event):
        """البحث عن شخص بالـ ID"""
        user_id = int(event.pattern_match.group(1))
        
        await event.edit("⏳ جاري البحث...")
        
        # انتظار 5 ثواني
        await asyncio.sleep(5)
        
        try:
            # جلب معلومات المستخدم
            user = await client.get_entity(user_id)
            full = await client(GetFullUserRequest(user))
            
            # تجميع المعلومات الأساسية
            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "بدون اسم"
            username = f"@{user.username}" if user.username else "لا يوجد"
            bio = full.full_user.about or "لا يوجد"
            
            # المجموعات المشتركة
            try:
                common = await client(GetCommonChatsRequest(user_id=user, max_id=0, limit=100))
                common_count = len(common.chats)
            except:
                common_count = 0
            
            # تحديد الحالة
            if user.bot:
                status = "🤖 بوت"
            elif hasattr(user, 'status'):
                status_type = type(user.status).__name__
                if 'Online' in status_type:
                    status = "🟢 متصل الآن"
                elif 'Recently' in status_type:
                    status = "🟡 شوهد مؤخراً"
                elif 'LastWeek' in status_type:
                    status = "🟠 شوهد هذا الأسبوع"
                elif 'LastMonth' in status_type:
                    status = "🔴 شوهد هذا الشهر"
                else:
                    status = "⚫ غير معروف"
            else:
                status = "⚫ غير معروف"
            
            # معلومات إضافية
            is_premium = "✅" if getattr(user, 'premium', False) else "❌"
            is_verified = "✅" if getattr(user, 'verified', False) else "❌"
            is_scam = "⚠️ نعم!" if getattr(user, 'scam', False) else "❌"
            is_fake = "⚠️ نعم!" if getattr(user, 'fake', False) else "❌"
            is_restricted = "⚠️ نعم" if getattr(user, 'restricted', False) else "❌"
            
            # عرض النتائج
            result = f"""
**🔍 نتائج البحث**

👤 **الاسم:** {name}
🆔 **الآيدي:** `{user_id}`
📧 **اليوزر:** {username}
📝 **البايو:** {bio}

**📊 الحالة:**
{status}

**ℹ️ معلومات إضافية:**
💎 بريميوم: {is_premium}
✅ موثق: {is_verified}
🚫 سكام: {is_scam}
🎭 مزيف: {is_fake}
⛔ مقيد: {is_restricted}
👥 مجموعات مشتركة: {common_count}
"""
            await event.edit(result)
            
            # إرسال صورة البروفايل إذا وجدت
            photos = await client.get_profile_photos(user, limit=1)
            if photos:
                await event.respond(file=photos[0])
                
        except ValueError:
            await event.edit("❌ لم يتم العثور على المستخدم")
        except Exception as e:
            await event.edit(f"❌ خطأ: {str(e)}")
