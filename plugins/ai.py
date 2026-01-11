"""
أوامر الذكاء الاصطناعي 🤖
"""
import os
import httpx
from telethon import events

# رابط Groq API
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def register(client):
    """تسجيل أوامر الذكاء الاصطناعي"""
    
    api_key = os.environ.get('GROQ_API_KEY')
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'ذكاء (.+)'))
    async def ai_command(event):
        """سؤال الذكاء الاصطناعي"""
        if not api_key:
            await event.edit("❌ لم يتم تعيين GROQ_API_KEY")
            return
        
        question = event.pattern_match.group(1)
        await event.edit("🤔 جاري التفكير...")
        
        try:
            # إرسال الطلب لـ Groq
            async with httpx.AsyncClient() as http:
                response = await http.post(
                    GROQ_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": "أنت مساعد ذكي. أجب باللغة العربية بشكل مختصر ومفيد."},
                            {"role": "user", "content": question}
                        ],
                        "max_tokens": 1024
                    },
                    timeout=30.0
                )
                
                data = response.json()
                
                if "choices" in data:
                    answer = data["choices"][0]["message"]["content"]
                    
                    # تقصير الرد إذا كان طويلاً
                    if len(answer) > 4000:
                        answer = answer[:4000] + "..."
                    
                    await event.edit(f"**🤖 الذكاء الاصطناعي:**\n\n{answer}")
                else:
                    error = data.get("error", {}).get("message", "خطأ غير معروف")
                    await event.edit(f"❌ خطأ: {error}")
            
        except Exception as e:
            await event.edit(f"❌ خطأ: {str(e)}")
