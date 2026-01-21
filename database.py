"""
قاعدة البيانات - Firebase Firestore
نظام بسيط للحفظ التلقائي
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# تهيئة Firebase
def init_firebase():
    """تهيئة الاتصال بـ Firestore"""
    try:
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

def get_db():
    """الحصول على كائن Firestore"""
    return firestore.client()

# ═══════════════════════════════════════════════════════════════════
# حفظ وجلب الأعضاء
# ═══════════════════════════════════════════════════════════════════

def save_member(user_id, data):
    """حفظ بيانات عضو"""
    try:
        db = get_db()
        db.collection('all_members').document(str(user_id)).set(data)
        return True
    except Exception as e:
        print(f"❌ خطأ في حفظ العضو: {e}")
        return False

def get_member(user_id):
    """جلب بيانات عضو"""
    try:
        db = get_db()
        doc = db.collection('all_members').document(str(user_id)).get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"❌ خطأ في جلب العضو: {e}")
    return None

def search_by_username(username):
    """البحث عن عضو باليوزرنيم"""
    try:
        db = get_db()
        username = username.replace("@", "").lower()
        docs = db.collection('all_members').where('username_lower', '==', username).limit(1).get()
        for doc in docs:
            return doc.to_dict()
    except Exception as e:
        print(f"❌ خطأ في البحث: {e}")
    return None

def get_members_count():
    """عدد الأعضاء المحفوظين"""
    try:
        db = get_db()
        docs = db.collection('all_members').get()
        return len(docs)
    except:
        return 0

# ═══════════════════════════════════════════════════════════════════
# تنظيف البيانات القديمة
# ═══════════════════════════════════════════════════════════════════

def cleanup_old_data():
    """حذف البيانات القديمة (monitored_groups, settings, members)"""
    try:
        db = get_db()
        deleted_count = 0
        
        # حذف monitored_groups
        docs = db.collection('monitored_groups').get()
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        
        # حذف settings
        docs = db.collection('settings').get()
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        
        # حذف members (البنية القديمة)
        docs = db.collection('members').get()
        for doc in docs:
            # حذف subcollection users
            users = doc.reference.collection('users').get()
            for user in users:
                user.reference.delete()
            doc.reference.delete()
            deleted_count += 1
        
        return deleted_count
    except Exception as e:
        print(f"❌ خطأ في التنظيف: {e}")
        return 0
