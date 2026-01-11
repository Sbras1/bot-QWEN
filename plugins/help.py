"""
أوامر المساعدة ❓
"""
from telethon import events

def register(client):
    """تسجيل أوامر المساعدة"""
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'اوامر'))
    async def help_command(event):
        """عرض قائمة الأوامر"""
        help_text = """
**🤖 أوامر البوت**

**🔍 البحث:**
• `بحث 123456789` - البحث عن شخص بالآيدي

**❓ مساعدة:**
• `اوامر` - عرض هذه القائمة
"""
        await event.edit(help_text)
