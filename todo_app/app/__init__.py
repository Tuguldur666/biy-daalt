import sqlite3
from flask import Flask, g

def create_app(config=None):
    app = Flask(__name__)
    app.config['DATABASE'] = ':memory:'
    app.config['SECRET_KEY'] = 'test-secret-key-III-VI-IX'
    app.config['TESTING'] = False

    if config:
        app.config.update(config)

    # For :memory: DB we keep ONE persistent connection per app instance
    _conn = sqlite3.connect(app.config['DATABASE'], check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    app._db_conn = _conn

    # Create tables
    _conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            email    TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            done       INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            user_id    INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    _conn.commit()

    from app.routes import bp
    app.register_blueprint(bp)

    return app

def get_db(app):
    return app._db_conn
