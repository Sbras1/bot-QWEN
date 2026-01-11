"""
أوامر الذكاء الاصطناعي 🤖
"""
import os
import asyncio
from telethon import events

# مكتبة Google Gemini
import google.generativeai as genai

def register(client):
    """تسجيل أوامر الذكاء الاصطناعي"""
    
    # تهيئة Gemini
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
    else:
        model = None
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'ذكاء (.+)'))
    async def ai_command(event):
        """سؤال الذكاء الاصطناعي"""
        if not model:
            await event.edit("❌ لم يتم تعيين GEMINI_API_KEY")
            return
        
        question = event.pattern_match.group(1)
        await event.edit("🤔 جاري التفكير...")
        
        try:
            # إرسال السؤال لـ Gemini
            response = model.generate_content(question)
            answer = response.text
            
            # تقصير الرد إذا كان طويلاً جداً
            if len(answer) > 4000:
                answer = answer[:4000] + "..."
            
            await event.edit(f"**🤖 الذكاء الاصطناعي:**\n\n{answer}")
            
        except Exception as e:
            await event.edit(f"❌ خطأ: {str(e)}")
