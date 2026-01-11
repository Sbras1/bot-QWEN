"""
تحميل جميع الإضافات
"""
from plugins import help, search

def load_all(client):
    """تحميل جميع الإضافات"""
    help.register(client)
    search.register(client)
    print("✅ تم تحميل جميع الإضافات")
