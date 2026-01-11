"""
تحميل جميع الإضافات
"""
from plugins import clone, messages, help

def load_all(client):
    """تحميل جميع الإضافات"""
    clone.register(client)
    messages.register(client)
    help.register(client)
    print("✅ تم تحميل جميع الإضافات")
