# -*- coding: utf-8 -*-
"""
Database Utility Functions
توابع کمکی برای عملیات دیتابیس با transaction safety
"""

import logging
from functools import wraps
from flask import flash

logger = logging.getLogger(__name__)


def safe_commit(db, error_message="خطا در ذخیره اطلاعات"):
    """
    Safe database commit with automatic rollback on error
    
    Usage:
        from utils.db_utils import safe_commit
        
        db.session.add(obj)
        if safe_commit(db):
            flash("عملیات موفق", "success")
        else:
            flash("عملیات ناموفق", "error")
    
    Args:
        db: SQLAlchemy database instance
        error_message: Custom error message (optional)
    
    Returns:
        bool: True if commit successful, False otherwise
    """
    try:
        db.session.commit()
        logger.info("Database commit successful")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database commit failed: {str(e)}", exc_info=True)
        flash(error_message, "error")
        return False


def transaction(db):
    """
    Decorator for wrapping route functions with transaction safety
    
    Usage:
        @app.route('/create', methods=['POST'])
        @login_required
        @transaction(db)
        def create_item():
            item = Item(name=request.form['name'])
            db.session.add(item)
            # commit is automatic, rollback on error
            return redirect(url_for('items'))
    
    Args:
        db: SQLAlchemy database instance
    
    Returns:
        Decorated function with automatic commit/rollback
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                db.session.commit()
                logger.debug(f"Transaction committed for {f.__name__}")
                return result
            except Exception as e:
                db.session.rollback()
                logger.error(f"Transaction failed in {f.__name__}: {str(e)}", exc_info=True)
                flash("خطا در انجام عملیات. لطفاً دوباره تلاش کنید.", "error")
                raise
        return wrapped
    return decorator


def bulk_insert(db, objects, batch_size=100):
    """
    Safely insert multiple objects in batches
    
    Args:
        db: SQLAlchemy database instance
        objects: List of model instances to insert
        batch_size: Number of objects to commit at once
    
    Returns:
        tuple: (success_count, error_count)
    """
    success_count = 0
    error_count = 0
    
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        try:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            success_count += len(batch)
            logger.info(f"Batch {i//batch_size + 1}: {len(batch)} objects inserted")
        except Exception as e:
            db.session.rollback()
            error_count += len(batch)
            logger.error(f"Batch {i//batch_size + 1} failed: {str(e)}")
    
    return success_count, error_count


def safe_delete(db, obj, error_message="خطا در حذف"):
    """
    Safely delete an object from database
    
    Args:
        db: SQLAlchemy database instance
        obj: Object to delete
        error_message: Custom error message
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db.session.delete(obj)
        db.session.commit()
        logger.info(f"Object deleted: {obj.__class__.__name__} id={obj.id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete failed: {str(e)}", exc_info=True)
        flash(error_message, "error")
        return False


def get_or_create(db, model, defaults=None, **kwargs):
    """
    Get an object or create it if it doesn't exist
    
    Args:
        db: SQLAlchemy database instance
        model: Model class
        defaults: Default values for creation
        **kwargs: Filter parameters
    
    Returns:
        tuple: (instance, created) where created is boolean
    """
    instance = model.query.filter_by(**kwargs).first()
    
    if instance:
        return instance, False
    
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    
    instance = model(**params)
    
    try:
        db.session.add(instance)
        db.session.commit()
        logger.info(f"Created new {model.__name__}: {kwargs}")
        return instance, True
    except Exception as e:
        db.session.rollback()
        logger.error(f"get_or_create failed: {str(e)}", exc_info=True)
        # Try to get again in case of race condition
        instance = model.query.filter_by(**kwargs).first()
        if instance:
            return instance, False
        raise
