"""
تحميل جميع الإضافات
"""
from plugins import monitor

def load_all(client):
    """تحميل جميع الإضافات"""
    monitor.register(client)
    print("✅ تم تحميل الإضافات")
