"""
تحميل جميع الإضافات
"""
from plugins import help

def load_all(client):
    """تحميل جميع الإضافات"""
    help.register(client)
    print("✅ تم تحميل جميع الإضافات")
