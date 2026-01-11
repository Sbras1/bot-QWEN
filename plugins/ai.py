"""
أوامر الذكاء الاصطناعي 🤖
"""
import os
import httpx
from telethon import events

# رابط Gemini API
GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"

def register(client):
    """تسجيل أوامر الذكاء الاصطناعي"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'ذكاء (.+)'))
    async def ai_command(event):
        """سؤال الذكاء الاصطناعي"""
        if not api_key:
            await event.edit("❌ لم يتم تعيين GEMINI_API_KEY")
            return
        
        question = event.pattern_match.group(1)
        await event.edit("🤔 جاري التفكير...")
        
        try:
            # إرسال الطلب لـ Gemini
            async with httpx.AsyncClient() as http:
                response = await http.post(
                    f"{GEMINI_URL}?key={api_key}",
                    json={
                        "contents": [{
                            "parts": [{"text": question}]
                        }]
                    },
                    timeout=30.0
                )
                
                data = response.json()
                
                if "candidates" in data:
                    answer = data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # تقصير الرد إذا كان طويلاً
                    if len(answer) > 4000:
                        answer = answer[:4000] + "..."
                    
                    await event.edit(f"**🤖 الذكاء الاصطناعي:**\n\n{answer}")
                else:
                    error = data.get("error", {}).get("message", "خطأ غير معروف")
                    await event.edit(f"❌ خطأ: {error}")
            
        except Exception as e:
            await event.edit(f"❌ خطأ: {str(e)}")
