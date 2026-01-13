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

# ═══════════════════════════════════════════════════════════════════
# دوال المراقبة
# ═══════════════════════════════════════════════════════════════════

# حفظ مجموعة مراقبة
def save_monitored_group(group_id, data):
    """حفظ بيانات مجموعة مراقبة"""
    try:
        db = get_db()
        db.collection('monitored_groups').document(str(group_id)).set(data)
        return True
    except Exception as e:
        print(f"❌ خطأ في حفظ المجموعة: {e}")
        return False

# جلب مجموعة مراقبة
def get_monitored_group(group_id):
    """جلب بيانات مجموعة مراقبة"""
    try:
        db = get_db()
        doc = db.collection('monitored_groups').document(str(group_id)).get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"❌ خطأ في جلب المجموعة: {e}")
    return None

# جلب مجموعة بواسطة آيدي مجموعة المتغيرات
def get_monitored_group_by_log_id(log_group_id):
    """جلب بيانات مجموعة بواسطة آيدي مجموعة المتغيرات"""
    try:
        db = get_db()
        docs = db.collection('monitored_groups').where('log_group_id', '==', log_group_id).get()
        for doc in docs:
            return doc.to_dict()
    except Exception as e:
        print(f"❌ خطأ في البحث: {e}")
    return None

# تحديث مجموعة مراقبة
def update_monitored_group(group_id, data):
    """تحديث بيانات مجموعة"""
    try:
        db = get_db()
        db.collection('monitored_groups').document(str(group_id)).update(data)
        return True
    except Exception as e:
        print(f"❌ خطأ في التحديث: {e}")
        return False

# جلب كل المجموعات المراقبة
def get_all_monitored_groups():
    """جلب كل المجموعات المراقبة"""
    try:
        db = get_db()
        docs = db.collection('monitored_groups').get()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"❌ خطأ في جلب المجموعات: {e}")
    return []

# حفظ عضو
def save_member(group_id, user_id, data):
    """حفظ بيانات عضو"""
    try:
        db = get_db()
        db.collection('members').document(str(group_id)).collection('users').document(str(user_id)).set(data)
        return True
    except Exception as e:
        print(f"❌ خطأ في حفظ العضو: {e}")
        return False

# جلب عضو
def get_member(group_id, user_id):
    """جلب بيانات عضو"""
    try:
        db = get_db()
        doc = db.collection('members').document(str(group_id)).collection('users').document(str(user_id)).get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"❌ خطأ في جلب العضو: {e}")
    return None

# جلب كل أعضاء مجموعة
def get_group_members(group_id):
    """جلب كل أعضاء مجموعة"""
    try:
        db = get_db()
        docs = db.collection('members').document(str(group_id)).collection('users').get()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"❌ خطأ في جلب الأعضاء: {e}")
    return []

# جلب معلومات عضو من أي مجموعة
def get_member_info(user_id):
    """جلب معلومات عضو من أي مجموعة"""
    try:
        db = get_db()
        # البحث في كل المجموعات
        groups = db.collection('members').get()
        for group in groups:
            doc = db.collection('members').document(group.id).collection('users').document(str(user_id)).get()
            if doc.exists:
                return doc.to_dict()
    except Exception as e:
        print(f"❌ خطأ في البحث عن العضو: {e}")
    return None
