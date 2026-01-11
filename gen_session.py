"""
سكريبت توليد StringSession
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 35667995
API_HASH = "83178ebc8f0964f44d144764320b29b8"
PHONE = "+966545120178"

async def main():
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    
    # إرسال طلب الكود
    await client.send_code_request(PHONE)
    print("✅ تم إرسال الكود إلى تيليجرام")
    
    # انتظار إدخال الكود
    code = input("أدخل الكود الذي وصلك: ")
    
    try:
        await client.sign_in(PHONE, code)
    except Exception as e:
        if "Two" in str(e):
            password = input("أدخل كلمة مرور التحقق بخطوتين: ")
            await client.sign_in(password=password)
    
    print("\n" + "="*60)
    print("✅ تم توليد الجلسة بنجاح!")
    print("="*60)
    print("\nانسخ هذا النص وضعه في Render كـ SESSION_STRING:\n")
    print(client.session.save())
    print("\n" + "="*60)
    
    await client.disconnect()

asyncio.run(main())
