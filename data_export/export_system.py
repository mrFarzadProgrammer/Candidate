"""
سیستم ذخیره امن و Export داده‌های کاربران
Data Export & Secure Storage System
"""

import pandas as pd
from io import BytesIO
from datetime import datetime
import os
import zipfile
from cryptography.fernet import Fernet
import json
import csv
from flask import send_file, Response
import logging

logger = logging.getLogger('data_export')


# ============================================================
# 1. DATA COLLECTION از تمام کاربران بات
# ============================================================

class CitizenDataCollector:
    """جمع‌آوری داده‌های تمام شهروندان"""
    
    def __init__(self, candidate_id):
        self.candidate_id = candidate_id
    
    def collect_all_citizen_data(self):
        """
        جمع‌آوری کامل داده‌های شهروندان
        
        Returns:
            dict: داده‌های دسته‌بندی شده
        """
        from database.models import (
            CitizenProfile, CitizenContribution,
            ContributionVote, ContributionComment,
            Message, db
        )
        
        # 1. پروفایل‌های شهروندان
        citizens = db.session.query(CitizenProfile).join(
            CitizenContribution,
            CitizenProfile.telegram_id == CitizenContribution.user_telegram_id
        ).filter(
            CitizenContribution.candidate_id == self.candidate_id
        ).distinct().all()
        
        citizens_data = []
        for citizen in citizens:
            citizens_data.append({
                'telegram_id': citizen.telegram_id,
                'full_name': citizen.full_name,
                'username': citizen.username,
                'phone': citizen.phone,
                'province': citizen.province,
                'city': citizen.city,
                'join_date': citizen.joined_at.isoformat() if citizen.joined_at else None,
                'is_active': citizen.is_active
            })
        
        # 2. مشارکت‌ها
        contributions = CitizenContribution.query.filter_by(
            candidate_id=self.candidate_id
        ).all()
        
        contributions_data = []
        for contrib in contributions:
            contributions_data.append({
                'tracking_code': contrib.tracking_code,
                'citizen_telegram_id': contrib.user_telegram_id,
                'citizen_name': contrib.user_first_name,
                'type': contrib.contribution_type,
                'title': contrib.title,
                'description': contrib.description,
                'category': contrib.category,
                'status': contrib.status,
                'votes_count': contrib.votes_count,
                'comments_count': contrib.comments_count,
                'created_at': contrib.created_at.isoformat(),
                'location': contrib.location_text
            })
        
        # 3. رای‌ها
        votes = db.session.query(ContributionVote).join(
            CitizenContribution,
            ContributionVote.contribution_id == CitizenContribution.id
        ).filter(
            CitizenContribution.candidate_id == self.candidate_id
        ).all()
        
        votes_data = []
        for vote in votes:
            votes_data.append({
                'citizen_telegram_id': vote.user_telegram_id,
                'contribution_id': vote.contribution_id,
                'vote_type': vote.vote_type,
                'voted_at': vote.voted_at.isoformat()
            })
        
        # 4. کامنت‌ها
        comments = db.session.query(ContributionComment).join(
            CitizenContribution,
            ContributionComment.contribution_id == CitizenContribution.id
        ).filter(
            CitizenContribution.candidate_id == self.candidate_id
        ).all()
        
        comments_data = []
        for comment in comments:
            comments_data.append({
                'citizen_telegram_id': comment.user_telegram_id,
                'citizen_name': comment.user_name,
                'contribution_id': comment.contribution_id,
                'comment_text': comment.comment_text,
                'created_at': comment.created_at.isoformat()
            })
        
        # 5. پیام‌های دریافتی
        messages = Message.query.filter_by(
            candidate_id=self.candidate_id
        ).all()
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'sender_name': msg.sender_name,
                'sender_telegram_id': msg.sender_telegram_id,
                'message_text': msg.message_text,
                'received_at': msg.created_at.isoformat(),
                'status': msg.status
            })
        
        return {
            'citizens': citizens_data,
            'contributions': contributions_data,
            'votes': votes_data,
            'comments': comments_data,
            'messages': messages_data,
            'metadata': {
                'candidate_id': self.candidate_id,
                'export_date': datetime.utcnow().isoformat(),
                'total_citizens': len(citizens_data),
                'total_contributions': len(contributions_data),
                'total_votes': len(votes_data),
                'total_comments': len(comments_data),
                'total_messages': len(messages_data)
            }
        }


# ============================================================
# 2. EXPORT به فرمت‌های مختلف
# ============================================================

class DataExporter:
    """Export داده به Excel, CSV, JSON"""
    
    def __init__(self, candidate_id):
        self.candidate_id = candidate_id
        self.collector = CitizenDataCollector(candidate_id)
    
    def export_to_excel(self, encrypted=False):
        """
        Export به Excel با چند sheet
        
        Args:
            encrypted: آیا فایل encrypt شود؟
        
        Returns:
            BytesIO: فایل Excel
        """
        data = self.collector.collect_all_citizen_data()
        
        # ساخت Excel با pandas
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: شهروندان
            if data['citizens']:
                df_citizens = pd.DataFrame(data['citizens'])
                df_citizens.to_excel(writer, sheet_name='شهروندان', index=False)
            
            # Sheet 2: مشارکت‌ها
            if data['contributions']:
                df_contributions = pd.DataFrame(data['contributions'])
                df_contributions.to_excel(writer, sheet_name='مشارکت‌ها', index=False)
            
            # Sheet 3: رای‌ها
            if data['votes']:
                df_votes = pd.DataFrame(data['votes'])
                df_votes.to_excel(writer, sheet_name='رای‌ها', index=False)
            
            # Sheet 4: کامنت‌ها
            if data['comments']:
                df_comments = pd.DataFrame(data['comments'])
                df_comments.to_excel(writer, sheet_name='کامنت‌ها', index=False)
            
            # Sheet 5: پیام‌ها
            if data['messages']:
                df_messages = pd.DataFrame(data['messages'])
                df_messages.to_excel(writer, sheet_name='پیام‌ها', index=False)
            
            # Sheet 6: خلاصه
            df_metadata = pd.DataFrame([data['metadata']])
            df_metadata.to_excel(writer, sheet_name='خلاصه', index=False)
        
        output.seek(0)
        
        # رمزنگاری در صورت نیاز
        if encrypted:
            return self._encrypt_file(output)
        
        logger.info(f'Excel export completed for candidate {self.candidate_id}')
        return output
    
    def export_to_csv_zip(self):
        """
        Export به فایل ZIP حاوی چند CSV
        
        Returns:
            BytesIO: فایل ZIP
        """
        data = self.collector.collect_all_citizen_data()
        
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # CSV برای هر دسته
            for key, items in data.items():
                if key == 'metadata':
                    continue
                
                if items:
                    csv_buffer = BytesIO()
                    df = pd.DataFrame(items)
                    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                    csv_buffer.seek(0)
                    
                    zip_file.writestr(f'{key}.csv', csv_buffer.getvalue())
            
            # فایل metadata
            metadata_json = json.dumps(data['metadata'], ensure_ascii=False, indent=2)
            zip_file.writestr('metadata.json', metadata_json)
        
        zip_buffer.seek(0)
        logger.info(f'CSV ZIP export completed for candidate {self.candidate_id}')
        return zip_buffer
    
    def export_to_json(self, pretty=True):
        """
        Export به JSON
        
        Returns:
            str: JSON string
        """
        data = self.collector.collect_all_citizen_data()
        
        if pretty:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            json_data = json.dumps(data, ensure_ascii=False)
        
        logger.info(f'JSON export completed for candidate {self.candidate_id}')
        return json_data
    
    def _encrypt_file(self, file_buffer):
        """رمزنگاری فایل"""
        from security.security_utils import get_encryption_key
        
        f = Fernet(get_encryption_key())
        encrypted_data = f.encrypt(file_buffer.getvalue())
        
        encrypted_buffer = BytesIO(encrypted_data)
        encrypted_buffer.seek(0)
        
        return encrypted_buffer


# ============================================================
# 3. SECURE STORAGE (ذخیره امن)
# ============================================================

class SecureStorage:
    """ذخیره‌سازی امن فایل‌های export"""
    
    def __init__(self):
        self.storage_path = os.getenv('SECURE_STORAGE_PATH', '/var/secure_exports')
        os.makedirs(self.storage_path, exist_ok=True)
    
    def save_export(self, candidate_id, file_buffer, file_type='excel'):
        """
        ذخیره فایل export به صورت امن
        
        Args:
            candidate_id: ID نامزد
            file_buffer: بافر فایل
            file_type: نوع فایل (excel, csv, json)
        
        Returns:
            str: مسیر فایل ذخیره شده
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'candidate_{candidate_id}_export_{timestamp}.{file_type}'
        filepath = os.path.join(self.storage_path, filename)
        
        # ذخیره با رمزنگاری
        with open(filepath, 'wb') as f:
            f.write(file_buffer.getvalue())
        
        # تنظیم permission (فقط owner)
        os.chmod(filepath, 0o600)
        
        # ثبت در لاگ
        self._log_export(candidate_id, filepath, file_type)
        
        logger.info(f'Secure export saved: {filepath}')
        return filepath
    
    def _log_export(self, candidate_id, filepath, file_type):
        """ثبت export در دیتابیس"""
        from database.models import db, DataExportLog
        
        log = DataExportLog(
            candidate_id=candidate_id,
            file_path=filepath,
            file_type=file_type,
            exported_at=datetime.utcnow(),
            exported_by_ip=None,  # باید از request بگیریم
            file_size=os.path.getsize(filepath)
        )
        
        db.session.add(log)
        db.session.commit()
    
    def get_export_history(self, candidate_id):
        """تاریخچه exportهای نامزد"""
        from database.models import DataExportLog
        
        logs = DataExportLog.query.filter_by(
            candidate_id=candidate_id
        ).order_by(DataExportLog.exported_at.desc()).all()
        
        return [{
            'id': log.id,
            'file_type': log.file_type,
            'file_size_mb': round(log.file_size / (1024*1024), 2),
            'exported_at': log.exported_at.isoformat(),
            'file_path': log.file_path
        } for log in logs]
    
    def delete_old_exports(self, days=30):
        """حذف exportهای قدیمی"""
        from database.models import db, DataExportLog
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_logs = DataExportLog.query.filter(
            DataExportLog.exported_at < cutoff_date
        ).all()
        
        for log in old_logs:
            # حذف فایل
            if os.path.exists(log.file_path):
                os.remove(log.file_path)
            
            # حذف رکورد
            db.session.delete(log)
        
        db.session.commit()
        logger.info(f'Deleted {len(old_logs)} old exports')


# ============================================================
# 4. ANALYTICS & INSIGHTS
# ============================================================

class CitizenAnalytics:
    """تحلیل‌های آماری روی داده‌های شهروندان"""
    
    def __init__(self, candidate_id):
        self.candidate_id = candidate_id
        self.collector = CitizenDataCollector(candidate_id)
    
    def get_demographics(self):
        """توزیع جمعیتی شهروندان"""
        data = self.collector.collect_all_citizen_data()
        
        df = pd.DataFrame(data['citizens'])
        
        if df.empty:
            return {}
        
        analytics = {
            'total_citizens': len(df),
            'by_province': df['province'].value_counts().to_dict() if 'province' in df.columns else {},
            'by_city': df['city'].value_counts().to_dict() if 'city' in df.columns else {},
            'active_percentage': (df['is_active'].sum() / len(df)) * 100 if 'is_active' in df.columns else 0
        }
        
        return analytics
    
    def get_engagement_metrics(self):
        """معیارهای تعامل"""
        data = self.collector.collect_all_citizen_data()
        
        total_citizens = len(data['citizens'])
        total_contributions = len(data['contributions'])
        total_votes = len(data['votes'])
        total_comments = len(data['comments'])
        
        return {
            'avg_contributions_per_citizen': round(total_contributions / total_citizens, 2) if total_citizens > 0 else 0,
            'avg_votes_per_contribution': round(total_votes / total_contributions, 2) if total_contributions > 0 else 0,
            'avg_comments_per_contribution': round(total_comments / total_contributions, 2) if total_contributions > 0 else 0,
            'engagement_rate': round((total_contributions / total_citizens) * 100, 2) if total_citizens > 0 else 0
        }
    
    def get_top_contributors(self, limit=10):
        """برترین مشارکت‌کنندگان"""
        from database.models import db, CitizenContribution
        from sqlalchemy import func
        
        top = db.session.query(
            CitizenContribution.user_telegram_id,
            CitizenContribution.user_first_name,
            func.count(CitizenContribution.id).label('count')
        ).filter(
            CitizenContribution.candidate_id == self.candidate_id,
            CitizenContribution.status == 'approved'
        ).group_by(
            CitizenContribution.user_telegram_id,
            CitizenContribution.user_first_name
        ).order_by(
            func.count(CitizenContribution.id).desc()
        ).limit(limit).all()
        
        return [{
            'telegram_id': t[0],
            'name': t[1],
            'contributions_count': t[2]
        } for t in top]
