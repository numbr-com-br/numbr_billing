from functools import wraps
from flask import g
from src.database import SessionLocal


def get_db_session():
    """Get database session for Flask request context"""
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db


def with_db_session(f):
    """Decorator to inject database session into route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db = get_db_session()
        try:
            return f(db=db, *args, **kwargs)
        except Exception:
            db.rollback()
            raise
        finally:
            db.commit()
    return decorated_function