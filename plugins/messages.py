"""
أوامر الرسائل 💬
"""
from telethon import events

def register(client):
    """تسجيل أوامر الرسائل"""
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'قل (.+)'))
    async def say_command(event):
        """إرسال رسالة عادية"""
        text = event.pattern_match.group(1)
        await event.delete()
        await event.respond(text)

    @client.on(events.NewMessage(outgoing=True, pattern=r'حذف'))
    async def delete_command(event):
        """حذف الرسالة المردود عليها"""
        reply = await event.get_reply_message()
        if reply:
            await reply.delete()
        await event.delete()

    @client.on(events.NewMessage(outgoing=True, pattern=r'تعديل (.+)'))
    async def edit_command(event):
        """تعديل الرسالة المردود عليها"""
        text = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        if reply and reply.out:
            await reply.edit(text)
        await event.delete()
