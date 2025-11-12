#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Admin Panel Routes: Data Export Management
==========================================

Routes for managing secure data exports:
- View export logs
- Create new exports
- Download encrypted exports
- Schedule automated exports
- Manage export retention

Usage:
    Include in admin_panel/app.py:
    from routes_data_export import *
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from utils.db_utils import safe_commit
from utils.validators import Validator, validate_form_data
import logging
from datetime import datetime, timedelta
from database.models import db, DataExportLog, Candidate, AuditLog
from data_export.export_system import (
    export_candidate_data,
    export_bot_users,
    export_contributions,
    export_messages,
    export_analytics,
    export_poll_results,
    export_scheduled_exports,
    export_complete_backup,
    schedule_export,
    cleanup_old_exports,
    verify_download_link,
    generate_secure_download_link
)
import os
from werkzeug.utils import secure_filename


def init_data_export_routes(app):
    """Initialize data export routes"""
    
    
logger = logging.getLogger(__name__)

@app.route('/admin/exports')
    def exports_dashboard():
        """داشبورد مدیریت exportها"""
        # لیست exportهای اخیر
        recent_exports = DataExportLog.query.order_by(
            DataExportLog.exported_at.desc()
        ).limit(50).all()
        
        # آمار
        total_exports = DataExportLog.query.count()
        today_exports = DataExportLog.query.filter(
            DataExportLog.exported_at >= datetime.utcnow().date()
        ).count()
        
        # حجم کل exportها
        total_size = db.session.query(
            db.func.sum(DataExportLog.file_size)
        ).scalar() or 0
        total_size_mb = total_size / (1024 * 1024)
        
        return render_template('admin/exports_dashboard.html',
                             recent_exports=recent_exports,
                             total_exports=total_exports,
                             today_exports=today_exports,
                             total_size_mb=round(total_size_mb, 2))
    
    
    @app.route('/admin/exports/create', methods=['GET', 'POST'])
    def create_export():
        """ایجاد export جدید"""
        if request.method == 'GET':
            candidates = Candidate.query.all()
            return render_template('admin/create_export.html', candidates=candidates)
        
        candidate_id = request.form.get('candidate_id', type=int)
        export_type = request.form.get('export_type')
        format_type = request.form.get('format', 'excel')
        
        try:
            candidate = Candidate.query.get_or_404(candidate_id)
            
            # انتخاب تابع مناسب
            if export_type == 'complete':
                file_path = export_complete_backup(candidate_id, format=format_type)
            elif export_type == 'bot_users':
                filters = {
                    'active_only': request.form.get('active_only') == 'on',
                    'date_from': request.form.get('date_from'),
                    'date_to': request.form.get('date_to')
                }
                file_path = export_bot_users(candidate_id, filters=filters, format=format_type)
            elif export_type == 'contributions':
                date_range = {
                    'start': request.form.get('date_from'),
                    'end': request.form.get('date_to')
                }
                status = request.form.get('status_filter')
                file_path = export_contributions(candidate_id, date_range=date_range, 
                                                status=status, format=format_type)
            elif export_type == 'messages':
                date_range = {
                    'start': request.form.get('date_from'),
                    'end': request.form.get('date_to')
                }
                file_path = export_messages(candidate_id, date_range=date_range, format=format_type)
            elif export_type == 'analytics':
                metrics = request.form.getlist('metrics')
                date_range = {
                    'start': request.form.get('date_from'),
                    'end': request.form.get('date_to')
                }
                file_path = export_analytics(candidate_id, metrics=metrics, 
                                            date_range=date_range, format=format_type)
            else:
                file_path = export_candidate_data(candidate_id, format=format_type)
            
            # محاسبه حجم فایل
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            # ثبت در لاگ
            export_log = DataExportLog(
                candidate_id=candidate_id,
                file_type=format_type,
                file_path=file_path,
                file_size=file_size,
                exported_by_ip=request.remote_addr,
                is_encrypted=True  # همه exportها رمز شده هستند
            )
            db.session.add(export_log)
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='data_export_created',
                user_id=session.get("admin_id", 1),  # TODO: Get from session
                user_type='admin',
                ip_address=request.remote_addr,
                details={
                    'candidate_id': candidate_id,
                    'candidate_name': candidate.full_name,
                    'export_type': export_type,
                    'format': format_type,
                    'file_size': file_size
                }
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            # ایجاد لینک دانلود امن
            download_link = generate_secure_download_link(export_log.id, expiry_hours=1)
            
            flash(f'✅ Export با موفقیت ایجاد شد. حجم: {file_size/(1024*1024):.2f} MB', 'success')
            return redirect(url_for('exports_dashboard'))
            
        except Exception as e:
            flash(f'❌ خطا در ایجاد export: {str(e)}', 'danger')
            db.session.rollback()
            return redirect(url_for('create_export'))
    
    
    @app.route('/admin/exports/<int:export_id>/download')
    def download_export(export_id):
        """دانلود فایل export"""
        export_log = DataExportLog.query.get_or_404(export_id)
        
        # بررسی وجود فایل
        if not os.path.exists(export_log.file_path):
            flash('❌ فایل export یافت نشد', 'danger')
            return redirect(url_for('exports_dashboard'))
        
        # ثبت در audit log
        audit = AuditLog(
            event_type='data_export_downloaded',
            user_id=session.get("admin_id", 1),  # TODO: Get from session
            user_type='admin',
            ip_address=request.remote_addr,
            details={
                'export_id': export_id,
                'candidate_id': export_log.candidate_id,
                'file_type': export_log.file_type
            }
        )
        db.session.add(audit)
        safe_commit(db, "Database commit failed")
        
        # ارسال فایل
        return send_file(
            export_log.file_path,
            as_attachment=True,
            download_name=f"export_{export_log.id}_{datetime.now().strftime('%Y%m%d')}.{export_log.file_type}"
        )
    
    
    @app.route('/admin/exports/<int:export_id>/delete', methods=['POST'])
    def delete_export(export_id):
        """حذف export"""
        export_log = DataExportLog.query.get_or_404(export_id)
        
        try:
            # حذف فایل
            if os.path.exists(export_log.file_path):
                os.remove(export_log.file_path)
            
            # حذف از دیتابیس
            db.session.delete(export_log)
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='data_export_deleted',
                user_id=session.get("admin_id", 1),  # TODO: Get from session
                user_type='admin',
                ip_address=request.remote_addr,
                details={'export_id': export_id}
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash('✅ Export حذف شد', 'success')
        except Exception as e:
            flash(f'❌ خطا: {str(e)}', 'danger')
            db.session.rollback()
        
        return redirect(url_for('exports_dashboard'))
    
    
    @app.route('/admin/exports/cleanup', methods=['POST'])
    def cleanup_exports():
        """پاکسازی exportهای قدیمی"""
        days = request.form.get('days', 7, type=int)
        
        try:
            deleted_count = cleanup_old_exports(days=days)
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='exports_cleanup',
                user_id=session.get("admin_id", 1),  # TODO: Get from session
                user_type='admin',
                ip_address=request.remote_addr,
                details={
                    'days': days,
                    'deleted_count': deleted_count
                }
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash(f'✅ {deleted_count} فایل قدیمی‌تر از {days} روز حذف شد', 'success')
        except Exception as e:
            flash(f'❌ خطا: {str(e)}', 'danger')
        
        return redirect(url_for('exports_dashboard'))
    
    
    @app.route('/admin/exports/schedule', methods=['GET', 'POST'])
    def schedule_export_route():
        """برنامه‌ریزی export خودکار"""
        if request.method == 'GET':
            candidates = Candidate.query.all()
            return render_template('admin/schedule_export.html', candidates=candidates)
        
        candidate_id = request.form.get('candidate_id', type=int)
        export_type = request.form.get('export_type')
        schedule_type = request.form.get('schedule_type')  # daily, weekly, monthly
        recipients = request.form.get('recipients')  # email addresses
        
        try:
            schedule_export(
                candidate_id=candidate_id,
                export_type=export_type,
                schedule=schedule_type,
                recipients=recipients.split(',') if recipients else []
            )
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='export_scheduled',
                user_id=session.get("admin_id", 1),  # TODO: Get from session
                user_type='admin',
                ip_address=request.remote_addr,
                details={
                    'candidate_id': candidate_id,
                    'export_type': export_type,
                    'schedule': schedule_type,
                    'recipients': recipients
                }
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash(f'✅ Export {schedule_type} برنامه‌ریزی شد', 'success')
        except Exception as e:
            flash(f'❌ خطا: {str(e)}', 'danger')
        
        return redirect(url_for('exports_dashboard'))
    
    
    @app.route('/admin/exports/candidate/<int:candidate_id>')
    def candidate_exports(candidate_id):
        """لیست exportهای یک کاندید"""
        candidate = Candidate.query.get_or_404(candidate_id)
        exports = DataExportLog.query.filter_by(
            candidate_id=candidate_id
        ).order_by(DataExportLog.exported_at.desc()).all()
        
        # آمار
        total_size = sum(e.file_size for e in exports)
        
        return render_template('admin/candidate_exports.html',
                             candidate=candidate,
                             exports=exports,
                             total_size_mb=total_size/(1024*1024))
    
    
    @app.route('/admin/exports/api/stats')
    def api_export_stats():
        """API: آمار exportها"""
        # آمار کلی
        total = DataExportLog.query.count()
        today = DataExportLog.query.filter(
            DataExportLog.exported_at >= datetime.utcnow().date()
        ).count()
        this_week = DataExportLog.query.filter(
            DataExportLog.exported_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # آمار به تفکیک نوع
        by_type = db.session.query(
            DataExportLog.file_type,
            db.func.count(DataExportLog.id)
        ).group_by(DataExportLog.file_type).all()
        
        # آمار به تفکیک کاندید (Top 10)
        by_candidate = db.session.query(
            Candidate.full_name,
            db.func.count(DataExportLog.id)
        ).join(DataExportLog).group_by(Candidate.id).order_by(
            db.func.count(DataExportLog.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'total': total,
            'today': today,
            'this_week': this_week,
            'by_type': dict(by_type),
            'by_candidate': [
                {'candidate': name, 'count': count}
                for name, count in by_candidate
            ]
        })
    
    
    @app.route('/admin/exports/api/verify-link', methods=['POST'])
    def api_verify_export_link():
        """API: بررسی اعتبار لینک دانلود"""
        token = request.json.get('token')
        
        try:
            export_id = verify_download_link(token)
            export_log = DataExportLog.query.get(export_id)
            
            if not export_log:
                return jsonify({'success': False, 'error': 'Export not found'})
            
            return jsonify({
                'success': True,
                'export_id': export_id,
                'candidate_id': export_log.candidate_id,
                'file_type': export_log.file_type,
                'file_size': export_log.file_size
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    
    @app.route('/admin/exports/bulk-export', methods=['POST'])
    def bulk_export():
        """Export دسته‌جمعی برای چند کاندید"""
        candidate_ids = request.form.getlist('candidate_ids', type=int)
        export_type = request.form.get('export_type', 'complete')
        
        success_count = 0
        errors = []
        
        for candidate_id in candidate_ids:
            try:
                if export_type == 'complete':
                    file_path = export_complete_backup(candidate_id)
                else:
                    file_path = export_candidate_data(candidate_id)
                
                # ثبت در لاگ
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                export_log = DataExportLog(
                    candidate_id=candidate_id,
                    file_type='excel',
                    file_path=file_path,
                    file_size=file_size,
                    exported_by_ip=request.remote_addr,
                    is_encrypted=True
                )
                db.session.add(export_log)
                success_count += 1
            except Exception as e:
                errors.append(f"کاندید {candidate_id}: {str(e)}")
        
        safe_commit(db, "Database commit failed")
        
        # ثبت در audit log
        audit = AuditLog(
            event_type='bulk_export',
            user_id=session.get("admin_id", 1),
            user_type='admin',
            ip_address=request.remote_addr,
            details={
                'candidate_count': len(candidate_ids),
                'success_count': success_count,
                'errors': errors
            }
        )
        db.session.add(audit)
        safe_commit(db, "Database commit failed")
        
        if errors:
            flash(f'⚠️ {success_count} export موفق، {len(errors)} خطا', 'warning')
        else:
            flash(f'✅ {success_count} export با موفقیت ایجاد شد', 'success')
        
        return redirect(url_for('exports_dashboard'))
