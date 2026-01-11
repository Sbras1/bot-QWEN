"""
أوامر الانتحال 🎭
"""
import os
from telethon import events
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.tl.functions.users import GetFullUserRequest

# حفظ البيانات الأصلية للاستعادة
original_profile = {
    "first_name": None,
    "last_name": None,
    "bio": None
}

def register(client):
    """تسجيل أوامر الانتحال"""
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'انتحال'))
    async def clone_command(event):
        """انتحال شخص - رد على رسالته (الاسم والصورة فقط)"""
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("❌ رد على رسالة الشخص المراد انتحاله")
            return
        
        await event.edit("⏳ جاري الانتحال...")
        
        try:
            # حفظ بياناتك الأصلية أولاً
            me = await client.get_me()
            original_profile["first_name"] = me.first_name
            original_profile["last_name"] = me.last_name or ""
            
            # جلب بيانات الضحية
            target = await reply.get_sender()
            
            # تغيير الاسم فقط
            await client(UpdateProfileRequest(
                first_name=target.first_name or "",
                last_name=target.last_name or ""
            ))
            
            # تغيير الصورة
            photos = await client.get_profile_photos(target, limit=1)
            if photos:
                photo = await client.download_media(photos[0])
                await client(UploadProfilePhotoRequest(
                    file=await client.upload_file(photo)
                ))
                os.remove(photo)
            
            await event.edit(f"✅ تم انتحال {target.first_name}!\n\nللعودة اكتب: رجوع")
        except Exception as e:
            await event.edit(f"❌ خطأ: {str(e)}")

    @client.on(events.NewMessage(outgoing=True, pattern=r'اسم (.+)'))
    async def name_command(event):
        """تغيير الاسم"""
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

    @client.on(events.NewMessage(outgoing=True, pattern=r'حالة (.+)'))
    async def bio_command(event):
        """تغيير الحالة/البايو"""
        if not original_profile["bio"]:
            me = await client.get_me()
            full = await client(GetFullUserRequest(me))
            original_profile["bio"] = full.full_user.about or ""
        
        bio = event.pattern_match.group(1)
        await client(UpdateProfileRequest(about=bio))
        await event.edit("✅ تم تغيير الحالة")

    @client.on(events.NewMessage(outgoing=True, pattern=r'صورة'))
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

    @client.on(events.NewMessage(outgoing=True, pattern=r'رجوع'))
    async def reset_command(event):
        """استعادة البيانات الأصلية"""
        await event.edit("⏳ جاري الاستعادة...")
        
        try:
            if original_profile["first_name"]:
                await client(UpdateProfileRequest(
                    first_name=original_profile["first_name"],
                    last_name=original_profile["last_name"] or "",
                    about=original_profile["bio"] or ""
                ))
            
            await event.edit("✅ تم استعادة بياناتك الأصلية!")
        except Exception as e:
            await event.edit(f"❌ خطأ: {str(e)}")
