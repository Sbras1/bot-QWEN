"""
أوامر البحث 🔍
"""
import asyncio
from telethon import events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import GetCommonChatsRequest

def register(client):
    """تسجيل أوامر البحث"""
    
    async def do_search(event, query):
        """دالة البحث الموحدة"""
        await event.edit("⏳ جاري البحث...")
        await asyncio.sleep(2)
        
        try:
            # جلب معلومات المستخدم (بالآيدي أو اليوزر)
            user = await client.get_entity(query)
            full = await client(GetFullUserRequest(user))
            
            # تجميع المعلومات الأساسية
            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "بدون اسم"
            username = f"@{user.username}" if user.username else "لا يوجد"
            bio = full.full_user.about or "لا يوجد"
            user_id = user.id
            
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
            
            # رابط المحادثة المباشر
            direct_link = f"tg://openmessage?user_id={user_id}"
            
            # عرض النتائج
            result = f"""
**🔍 نتائج البحث**

👤 **الاسم:** {name}
🆔 **الآيدي:** `{user_id}`
📧 **اليوزر:** {username}
📝 **البايو:** {bio}
🔗 **رابط مباشر:** [اضغط هنا]({direct_link})

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
            await event.edit("""❌ **لم يتم العثور على المستخدم**

💡 **ملاحظة:** البحث بالآيدي يعمل فقط إذا:
• تفاعلت معه من قبل
• في مجموعة مشتركة معك
• بحثت عنه باليوزر أولاً

جرب: `بحث @username`""")
        except Exception as e:
            error_msg = str(e)
            if "Could not find the input entity" in error_msg:
                await event.edit("""❌ **لم أجد هذا الشخص**

💡 **السبب:** لم تتفاعل مع هذا الحساب من قبل.

**الحل:** ابحث باليوزر أولاً:
`بحث @username`

ثم يمكنك البحث بالآيدي لاحقاً.""")
            else:
                await event.edit(f"❌ خطأ: {error_msg}")
    
    # البحث بالآيدي
    @client.on(events.NewMessage(outgoing=True, pattern=r'^بحث (\d+)$'))
    async def search_by_id(event):
        """البحث عن شخص بالـ ID"""
        user_id = int(event.pattern_match.group(1))
        await do_search(event, user_id)
    
    # البحث باليوزر
    @client.on(events.NewMessage(outgoing=True, pattern=r'^بحث @?([a-zA-Z][a-zA-Z0-9_]{3,})$'))
    async def search_by_username(event):
        """البحث عن شخص باليوزر"""
        username = event.pattern_match.group(1)
        await do_search(event, username)
