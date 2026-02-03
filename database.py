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
    
    # جلب من الفهرس إذا موجود
    if _search_index and str(user_id) in _search_index.get('by_id', {}):
        data = _search_index['by_id'][str(user_id)]
        set_cache(f"member_{user_id}", data)
        return data
    
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
    username = username.replace("@", "").lower()
    
    # جلب من الفهرس أولاً (أسرع)
    if _search_index and username in _search_index.get('by_username', {}):
        return _search_index['by_username'][username]
    
    try:
        db = get_db()
        docs = db.collection('all_members').where('username_lower', '==', username).limit(1).get()
        for doc in docs:
            return doc.to_dict()
    except Exception as e:
        print(f"❌ خطأ في البحث: {e}")
    return None

def get_members_count():
    """عدد الأعضاء المحفوظين"""
    # استخدام الفهرس إذا موجود
    if _search_index and _search_index.get('all'):
        return len(_search_index['all'])
    
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

# ═══════════════════════════════════════════════════════════════════
# بحث متقدم (Indexing)
# ═══════════════════════════════════════════════════════════════════

# فهرس محلي للبحث السريع
_search_index = None
_index_time = 0
INDEX_DURATION = 600  # 10 دقائق

def build_search_index():
    """بناء فهرس البحث"""
    global _search_index, _index_time
    
    # استخدام الفهرس المحفوظ إذا حديث
    if _search_index and time.time() - _index_time < INDEX_DURATION:
        return _search_index
    
    try:
        db = get_db()
        docs = db.collection('all_members').get()
        
        _search_index = {
            'by_id': {},
            'by_username': {},
            'by_name': [],
            'no_username': [],
            'by_groups_count': [],
            'all': []
        }
        
        for doc in docs:
            data = doc.to_dict()
            user_id = str(data.get('user_id', doc.id))
            username = data.get('username_lower', '')
            full_name = data.get('full_name', '').lower()
            groups_seen = data.get('groups_seen', {})
            
            _search_index['by_id'][user_id] = data
            _search_index['all'].append(data)
            
            if username:
                _search_index['by_username'][username] = data
            else:
                _search_index['no_username'].append(data)
            
            _search_index['by_name'].append((full_name, data))
            _search_index['by_groups_count'].append((len(groups_seen), data))
        
        # ترتيب حسب عدد القروبات
        _search_index['by_groups_count'].sort(key=lambda x: x[0], reverse=True)
        
        _index_time = time.time()
        print(f"📊 تم بناء فهرس البحث: {len(_search_index['all'])} عضو")
        
    except Exception as e:
        print(f"❌ خطأ في بناء الفهرس: {e}")
        _search_index = {'by_id': {}, 'by_username': {}, 'by_name': [], 'no_username': [], 'by_groups_count': [], 'all': []}
    
    return _search_index

def search_by_name(name_query):
    """بحث بالاسم"""
    index = build_search_index()
    results = []
    query = name_query.lower()
    
    for name, data in index['by_name']:
        if query in name:
            results.append(data)
            if len(results) >= 50:
                break
    
    return results

def get_members_without_username():
    """جلب أعضاء بدون يوزرنيم"""
    index = build_search_index()
    return index['no_username'][:100]

def get_members_by_groups_count(limit=20):
    """جلب أعضاء بأكثر قروبات"""
    index = build_search_index()
    return [(count, data) for count, data in index['by_groups_count'][:limit]]

def search_in_group(group_id, query=None):
    """بحث داخل قروب معين"""
    members = get_group_members(group_id)
    
    if not query:
        return members
    
    query = query.lower()
    results = []
    
    for m in members:
        name = m.get('full_name', '').lower()
        username = m.get('username', '').lower()
        if query in name or query in username:
            results.append(m)
    
    return results

def get_common_members(group1_id, group2_id):
    """جلب الأعضاء المشتركين بين قروبين"""
    members1 = get_group_members(group1_id)
    members2 = get_group_members(group2_id)
    
    ids1 = {str(m.get('user_id')) for m in members1}
    ids2 = {str(m.get('user_id')) for m in members2}
    
    common_ids = ids1 & ids2
    
    # جلب البيانات الكاملة
    common = []
    for m in members1:
        if str(m.get('user_id')) in common_ids:
            common.append(m)
    
    return common

def get_today_changes():
    """جلب تغييرات اليوم"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    index = build_search_index()
    changes = {
        'name_changes': [],
        'username_changes': [],
        'new_members': []
    }
    
    for data in index['all']:
        # تغييرات الاسم
        name_history = data.get('name_history', [])
        for entry in name_history:
            if entry.get('date') == today:
                changes['name_changes'].append(data)
                break
        
        # تغييرات اليوزر
        username_history = data.get('username_history', [])
        for entry in username_history:
            if entry.get('date') == today:
                changes['username_changes'].append(data)
                break
        
        # أعضاء جدد
        first_seen = data.get('first_seen', '')
        if first_seen.startswith(today):
            changes['new_members'].append(data)
    
    return changes

# ═══════════════════════════════════════════════════════════════════
# نسخ احتياطي
# ═══════════════════════════════════════════════════════════════════

def create_backup():
    """إنشاء نسخة احتياطية كاملة"""
    try:
        db = get_db()
        backup = {
            'all_members': {},
            'bot_settings': {},
            'backup_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # نسخ all_members
        docs = db.collection('all_members').get()
        for doc in docs:
            backup['all_members'][doc.id] = doc.to_dict()
        
        # نسخ bot_settings
        docs = db.collection('bot_settings').get()
        for doc in docs:
            backup['bot_settings'][doc.id] = doc.to_dict()
        
        return backup
    except Exception as e:
        print(f"❌ خطأ في النسخ الاحتياطي: {e}")
        return None

def restore_backup(backup_data):
    """استعادة من نسخة احتياطية"""
    try:
        db = get_db()
        restored = 0
        
        # استعادة all_members
        for user_id, data in backup_data.get('all_members', {}).items():
            db.collection('all_members').document(user_id).set(data)
            restored += 1
        
        # استعادة bot_settings
        for doc_id, data in backup_data.get('bot_settings', {}).items():
            db.collection('bot_settings').document(doc_id).set(data)
        
        # مسح الكاش
        clear_cache()
        global _search_index
        _search_index = None
        
        return restored
    except Exception as e:
        print(f"❌ خطأ في الاستعادة: {e}")
        return 0
