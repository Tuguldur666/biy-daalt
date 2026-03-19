from flask import Blueprint, request, jsonify, g, current_app
from app import get_db
import hashlib, hmac as _hmac, base64, json, time
from functools import wraps

bp = Blueprint('main', __name__)

SECRET = b'III-VI-IX-secret'

def _make_token(user_id):
    payload = json.dumps({'user_id': user_id, 'exp': time.time() + 3600})
    encoded = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = _hmac.new(SECRET, encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{sig}"

def _verify_token(token):
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        encoded, sig = parts
        expected = _hmac.new(SECRET, encoded.encode(), hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(encoded).decode())
        if payload['exp'] < time.time():
            return None
        return payload['user_id']
    except Exception:
        return None

def _hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized - token required'}), 401
        user_id = _verify_token(auth[7:])
        if not user_id:
            return jsonify({'error': 'Unauthorized - invalid or expired token'}), 401
        db = get_db(current_app._get_current_object())
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 401
        g.user = dict(user)
        return f(*args, **kwargs)
    return decorated

# AUTH
@bp.route('/auth/register', methods=['POST'])
def register():
    d = request.get_json(silent=True) or {}
    email = d.get('email', '').strip()
    pw    = d.get('password', '')
    if not email or not pw:
        return jsonify({'error': 'Email and password required'}), 400
    if len(pw) < 6:
        return jsonify({'error': 'Password too short (min 6 chars)'}), 400
    db = get_db(current_app._get_current_object())
    if db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone():
        return jsonify({'error': 'Email already exists'}), 409
    cur = db.execute('INSERT INTO users (email,password) VALUES (?,?)', (email, _hash_pw(pw)))
    db.commit()
    return jsonify({'message': 'Registered', 'user': {'id': cur.lastrowid, 'email': email}}), 201

@bp.route('/auth/login', methods=['POST'])
def login():
    d  = request.get_json(silent=True) or {}
    email = d.get('email', '').strip()
    pw    = d.get('password', '')
    db = get_db(current_app._get_current_object())
    user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    if not user or user['password'] != _hash_pw(pw):
        return jsonify({'error': 'Invalid email or password'}), 401
    return jsonify({'token': _make_token(user['id']), 'user': {'id': user['id'], 'email': user['email']}}), 200

# TASKS
@bp.route('/tasks', methods=['GET'])
@require_auth
def get_tasks():
    db = get_db(current_app._get_current_object())
    rows = db.execute('SELECT * FROM tasks WHERE user_id=? ORDER BY id', (g.user['id'],)).fetchall()
    return jsonify([dict(r) for r in rows]), 200

@bp.route('/tasks', methods=['POST'])
@require_auth
def create_task():
    d     = request.get_json(silent=True) or {}
    title = d.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    db  = get_db(current_app._get_current_object())
    cur = db.execute('INSERT INTO tasks (title,user_id) VALUES (?,?)', (title, g.user['id']))
    db.commit()
    row = db.execute('SELECT * FROM tasks WHERE id=?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@bp.route('/tasks/<int:tid>', methods=['GET'])
@require_auth
def get_task(tid):
    db  = get_db(current_app._get_current_object())
    row = db.execute('SELECT * FROM tasks WHERE id=? AND user_id=?', (tid, g.user['id'])).fetchone()
    if not row:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(dict(row)), 200

@bp.route('/tasks/<int:tid>', methods=['PUT'])
@require_auth
def update_task(tid):
    db  = get_db(current_app._get_current_object())
    row = db.execute('SELECT * FROM tasks WHERE id=? AND user_id=?', (tid, g.user['id'])).fetchone()
    if not row:
        return jsonify({'error': 'Task not found'}), 404
    d     = request.get_json(silent=True) or {}
    title = d.get('title', '').strip() or row['title']
    done  = d.get('done')
    done_val = (1 if done else 0) if done is not None else row['done']
    db.execute('UPDATE tasks SET title=?, done=? WHERE id=?', (title, done_val, tid))
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone())), 200

@bp.route('/tasks/<int:tid>', methods=['DELETE'])
@require_auth
def delete_task(tid):
    db  = get_db(current_app._get_current_object())
    row = db.execute('SELECT id FROM tasks WHERE id=? AND user_id=?', (tid, g.user['id'])).fetchone()
    if not row:
        return jsonify({'error': 'Task not found'}), 404
    db.execute('DELETE FROM tasks WHERE id=?', (tid,))
    db.commit()
    return jsonify({'message': 'Task deleted'}), 200
