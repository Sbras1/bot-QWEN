"""
قاعدة البيانات - Firebase Firestore
نظام بسيط للحفظ التلقائي مع تخزين مؤقت
"""
import os
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore

# ═══════════════════════════════════════════════════════════════════
# التخزين المؤقت (Cache) لتقليل طلبات Firebase
# ═══════════════════════════════════════════════════════════════════
_cache = {}
_cache_time = {}
CACHE_DURATION = 300  # 5 دقائق

def get_cached(key):
    """جلب من الكاش"""
    if key in _cache:
        if time.time() - _cache_time.get(key, 0) < CACHE_DURATION:
            return _cache[key]
    return None

def set_cache(key, value):
    """حفظ في الكاش"""
    _cache[key] = value
    _cache_time[key] = time.time()

def clear_cache(key=None):
    """مسح الكاش"""
    if key:
        _cache.pop(key, None)
        _cache_time.pop(key, None)
    else:
        _cache.clear()
        _cache_time.clear()

# ═══════════════════════════════════════════════════════════════════
# تهيئة Firebase
# ═══════════════════════════════════════════════════════════════════

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
        # تحديث الكاش
        set_cache(f"member_{user_id}", data)
        return True
    except Exception as e:
        print(f"❌ خطأ في حفظ العضو: {e}")
        return False

def get_member(user_id):
    """جلب بيانات عضو مع كاش"""
    # جلب من الكاش أولاً
    cached = get_cached(f"member_{user_id}")
    if cached:
        return cached
    
    try:
        db = get_db()
        doc = db.collection('all_members').document(str(user_id)).get()
        if doc.exists:
            data = doc.to_dict()
            set_cache(f"member_{user_id}", data)
            return data
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
# إعدادات القروب المركزي
# ═══════════════════════════════════════════════════════════════════

def save_log_group(chat_id):
    """حفظ آيدي قروب الإشعارات"""
    try:
        db = get_db()
        db.collection('bot_settings').document('log_group').set({
            'chat_id': chat_id
        })
        return True
    except:
        return False

def get_log_group():
    """جلب آيدي قروب الإشعارات"""
    try:
        db = get_db()
        doc = db.collection('bot_settings').document('log_group').get()
        if doc.exists:
            return doc.to_dict().get('chat_id')
    except:
        pass
    return None

def get_group_members(group_id):
    """جلب أعضاء قروب معين من البنية القديمة والجديدة"""
    members = {}
    db = get_db()
    group_id_str = str(group_id).replace('-100', '-100')  # تنظيف الآيدي
    
    try:
        # 1. جلب من البنية القديمة members/{group_id}/users
        users = db.collection('members').document(str(group_id)).collection('users').get()
        for user in users:
            data = user.to_dict()
            user_id = str(data.get('user_id', user.id))
            members[user_id] = data
        
        # 2. جلب من all_members اللي عندهم هذا القروب
        all_docs = db.collection('all_members').get()
        for doc in all_docs:
            data = doc.to_dict()
            groups_seen = data.get('groups_seen', {})
            if str(group_id) in groups_seen or str(abs(int(group_id))) in groups_seen:
                user_id = str(data.get('user_id', doc.id))
                # الأولوية للبيانات الجديدة
                members[user_id] = data
    except Exception as e:
        print(f"❌ خطأ في جلب أعضاء القروب: {e}")
    
    return list(members.values())

def get_all_members():
    """جلب كل الأعضاء من البنية الجديدة والقديمة"""
    all_members = {}
    db = get_db()
    
    try:
        # 1. جلب من all_members (الجديد)
        docs = db.collection('all_members').get()
        print(f"📊 all_members: {len(docs)} عضو")
        for doc in docs:
            data = doc.to_dict()
            user_id = str(data.get('user_id', doc.id))
            all_members[user_id] = data
        
        # 2. جلب من members/{group}/users (القديم)
        groups = db.collection('members').get()
        print(f"📊 مجموعات قديمة: {len(groups)}")
        for group in groups:
            group_id = group.id
            users = group.reference.collection('users').get()
            print(f"  - المجموعة {group_id}: {len(users)} عضو")
            for user in users:
                data = user.to_dict()
                user_id = str(data.get('user_id', user.id))
                # إذا موجود بالجديد، لا نستبدله
                if user_id not in all_members:
                    all_members[user_id] = data
        
        print(f"📊 المجموع: {len(all_members)} عضو")
    except Exception as e:
        print(f"❌ خطأ في جلب الأعضاء: {e}")
    
    return list(all_members.values())

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
