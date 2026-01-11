"""
شغّل هذا الملف محلياً مرة واحدة فقط لتوليد StringSession
ثم انسخ النتيجة وضعها في Render كمتغير SESSION_STRING
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = input("أدخل API_ID: ")
api_hash = input("أدخل API_HASH: ")

with TelegramClient(StringSession(), int(api_id), api_hash) as client:
    print("\n" + "="*50)
    print("✅ تم توليد الجلسة بنجاح!")
    print("="*50)
    print("\nانسخ هذا النص وضعه في Render كـ SESSION_STRING:\n")
    print(client.session.save())
    print("\n" + "="*50)
