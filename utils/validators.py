# -*- coding: utf-8 -*-
"""
Input Validation Utilities
اعتبارسنجی ورودی‌ها برای امنیت و consistency
"""

import re
from datetime import datetime
from flask import flash
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class Validator:
    """Comprehensive input validator"""
    
    @staticmethod
    def validate_required(value, field_name):
        """Check if value is not empty"""
        if not value or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} الزامی است")
        return True
    
    @staticmethod
    def validate_length(value, min_length=None, max_length=None, field_name="فیلد"):
        """Validate string length"""
        if not isinstance(value, str):
            value = str(value)
        
        length = len(value)
        
        if min_length and length < min_length:
            raise ValidationError(
                f"{field_name} باید حداقل {min_length} کاراکتر باشد"
            )
        
        if max_length and length > max_length:
            raise ValidationError(
                f"{field_name} نباید بیشتر از {max_length} کاراکتر باشد"
            )
        
        return True
    
    @staticmethod
    def validate_integer(value, min_val=None, max_val=None, field_name="عدد"):
        """Validate integer value"""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} باید عدد صحیح باشد")
        
        if min_val is not None and int_value < min_val:
            raise ValidationError(f"{field_name} نباید کمتر از {min_val} باشد")
        
        if max_val is not None and int_value > max_val:
            raise ValidationError(f"{field_name} نباید بیشتر از {max_val} باشد")
        
        return int_value
    
    @staticmethod
    def validate_positive_integer(value, field_name="عدد"):
        """Validate positive integer"""
        return Validator.validate_integer(value, min_val=1, field_name=field_name)
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return True  # Optional field
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("فرمت ایمیل صحیح نیست")
        
        return True
    
    @staticmethod
    def validate_phone(phone):
        """Validate Iranian phone number"""
        if not phone:
            return True  # Optional field
        
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Iranian mobile: 09xx xxx xxxx
        mobile_pattern = r'^09[0-9]{9}$'
        # Iranian landline: 0xx xxxx xxxx
        landline_pattern = r'^0[1-9][0-9]{9}$'
        
        if not (re.match(mobile_pattern, phone) or re.match(landline_pattern, phone)):
            raise ValidationError("شماره تلفن معتبر نیست")
        
        return True
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        Validator.validate_required(username, "نام کاربری")
        Validator.validate_length(username, min_length=3, max_length=50, field_name="نام کاربری")
        
        # Only alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("نام کاربری فقط می‌تواند شامل حروف، اعداد و _ باشد")
        
        return True
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        Validator.validate_required(password, "رمز عبور")
        Validator.validate_length(password, min_length=6, field_name="رمز عبور")
        
        # Check for at least one letter and one number (optional, can be stricter)
        # if not re.search(r'[a-zA-Z]', password) or not re.search(r'[0-9]', password):
        #     raise ValidationError("رمز عبور باید شامل حروف و اعداد باشد")
        
        return True
    
    @staticmethod
    def validate_url(url, field_name="URL"):
        """Validate URL format"""
        if not url:
            return True  # Optional
        
        pattern = r'^https?://[^\s<>"]+|www\.[^\s<>"]+'
        if not re.match(pattern, url):
            raise ValidationError(f"{field_name} معتبر نیست")
        
        return True
    
    @staticmethod
    def validate_telegram_token(token):
        """Validate Telegram bot token format"""
        Validator.validate_required(token, "توکن ربات")
        
        # Format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
        pattern = r'^\d{8,10}:[A-Za-z0-9_-]{35}$'
        if not re.match(pattern, token):
            raise ValidationError("فرمت توکن ربات صحیح نیست")
        
        return True
    
    @staticmethod
    def validate_date(date_str, format='%Y-%m-%d'):
        """Validate date string"""
        try:
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            raise ValidationError(f"فرمت تاریخ باید {format} باشد")
    
    @staticmethod
    def validate_choice(value, choices, field_name="انتخاب"):
        """Validate value is in allowed choices"""
        if value not in choices:
            raise ValidationError(
                f"{field_name} باید یکی از مقادیر {', '.join(map(str, choices))} باشد"
            )
        return True
    
    @staticmethod
    def validate_file_extension(filename, allowed_extensions):
        """Validate file extension"""
        if '.' not in filename:
            raise ValidationError("فایل باید پسوند داشته باشد")
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            raise ValidationError(
                f"فقط فایل‌های {', '.join(allowed_extensions)} مجاز هستند"
            )
        
        return True
    
    @staticmethod
    def validate_file_size(file, max_size_mb=16):
        """Validate uploaded file size"""
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset
        
        max_bytes = max_size_mb * 1024 * 1024
        if size > max_bytes:
            raise ValidationError(
                f"حجم فایل نباید بیشتر از {max_size_mb}MB باشد"
            )
        
        return True


def validate_form_data(form_data, rules):
    """
    Validate multiple form fields at once
    
    Usage:
        rules = {
            'username': [
                ('required', 'نام کاربری'),
                ('length', {'min_length': 3, 'max_length': 50})
            ],
            'email': [('email',)],
            'age': [('integer', {'min_val': 18, 'max_val': 120})]
        }
        
        errors = validate_form_data(request.form, rules)
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(...)
    
    Args:
        form_data: Dictionary of form data
        rules: Dictionary of validation rules
    
    Returns:
        List of error messages (empty if valid)
    """
    validator = Validator()
    errors = []
    
    for field, field_rules in rules.items():
        value = form_data.get(field)
        
        for rule in field_rules:
            try:
                rule_name = rule[0]
                rule_args = rule[1] if len(rule) > 1 else {}
                
                method_name = f'validate_{rule_name}'
                if hasattr(validator, method_name):
                    method = getattr(validator, method_name)
                    
                    if isinstance(rule_args, dict):
                        method(value, **rule_args)
                    elif isinstance(rule_args, (list, tuple)):
                        method(value, *rule_args)
                    else:
                        method(value, rule_args)
                else:
                    logger.warning(f"Unknown validation rule: {rule_name}")
                    
            except ValidationError as e:
                errors.append(str(e))
                break  # Stop validating this field on first error
    
    return errors
