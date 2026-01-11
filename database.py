"""
قاعدة البيانات - Firestore
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# تهيئة Firebase
def init_firebase():
    """تهيئة الاتصال بـ Firestore"""
    try:
        # جلب بيانات الاعتماد من المتغير البيئي
        cred_json = os.environ.get('FIREBASE_CREDENTIALS')
        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ تم الاتصال بـ Firestore")
            return True
    except Exception as e:
        print(f"❌ خطأ في الاتصال بـ Firestore: {e}")
    return False

# الحصول على قاعدة البيانات
def get_db():
    """الحصول على كائن Firestore"""
    return firestore.client()

# حفظ بيانات الملف الشخصي الأصلية
def save_original_profile(user_id, data):
    """حفظ البيانات الأصلية للمستخدم"""
    try:
        db = get_db()
        db.collection('profiles').document(str(user_id)).set(data)
        return True
    except Exception as e:
        print(f"❌ خطأ في الحفظ: {e}")
        return False

# جلب بيانات الملف الشخصي الأصلية
def get_original_profile(user_id):
    """جلب البيانات الأصلية للمستخدم"""
    try:
        db = get_db()
        doc = db.collection('profiles').document(str(user_id)).get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"❌ خطأ في الجلب: {e}")
    return None

# حذف بيانات الملف الشخصي
def delete_original_profile(user_id):
    """حذف البيانات الأصلية"""
    try:
        db = get_db()
        db.collection('profiles').document(str(user_id)).delete()
        return True
    except Exception as e:
        print(f"❌ خطأ في الحذف: {e}")
        return False
