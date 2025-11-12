#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Admin Panel Routes: Gradual Plan Release Management
====================================================

Routes for managing gradual release of plans:
- Enable/Disable plans for purchase
- Schedule future releases
- View release history
- Manage beta testers
- Configure discount campaigns

Usage:
    Include in admin_panel/app.py:
    from routes_plan_release import *
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from utils.db_utils import safe_commit
from utils.validators import Validator, validate_form_data
import logging
from datetime import datetime, timedelta
from database.models import db, Plan, AuditLog, BetaTester, DiscountCampaign, Candidate
from plan_management.gradual_release import (
    enable_plan,
    disable_plan,
    schedule_plan_release,
    check_plan_availability,
    get_available_plans,
    update_plan_features,
    migrate_users_to_new_plan,
    get_plan_release_history
)

# توجه: این routeها باید در admin_panel/app.py با decorator 
logger = logging.getLogger(__name__)

@app.route اضافه شوند
# این فایل فقط برای نمایش ساختار است


def init_plan_release_routes(app):
    """Initialize plan release routes"""
    
    @app.route('/admin/plans/release-manager')
    def plan_release_manager():
        """صفحه مدیریت انتشار مرحله‌ای پلن‌ها"""
        plans = Plan.query.order_by(Plan.display_order).all()
        
        # آمار هر پلن
        for plan in plans:
            plan.total_purchases = db.session.query(db.func.count())\
                .select_from(db.text('plan_purchases'))\
                .where(db.text(f'plan_id = {plan.id}'))\
                .scalar() or 0
            
            plan.is_available = check_plan_availability(plan.code)
        
        return render_template('admin/plan_release_manager.html', plans=plans)
    
    
    @app.route('/admin/plans/<int:plan_id>/enable', methods=['POST'])
    def enable_plan_route(plan_id):
        """فعال کردن پلن برای خرید"""
        plan = Plan.query.get_or_404(plan_id)
        
        try:
            # فعال‌سازی پلن
            enable_plan(plan.code, enabled_by=1)  # TODO: Get admin_id from session
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='plan_enabled',
                user_id=session.get("admin_id", 1),  # TODO: Get from session
                user_type='admin',
                ip_address=request.remote_addr,
                details={
                    'plan_id': plan.id,
                    'plan_code': plan.code,
                    'plan_name': plan.name
                }
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash(f'✅ پلن "{plan.name}" با موفقیت فعال شد', 'success')
        except Exception as e:
            flash(f'❌ خطا در فعال‌سازی پلن: {str(e)}', 'danger')
        
        return redirect(url_for('plan_release_manager'))
    
    
    @app.route('/admin/plans/<int:plan_id>/disable', methods=['POST'])
    def disable_plan_route(plan_id):
        """غیرفعال کردن پلن"""
        plan = Plan.query.get_or_404(plan_id)
        reason = request.form.get('reason', 'دستور مدیر سیستم')
        
        try:
            disable_plan(plan.code, reason=reason)
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='plan_disabled',
                user_id=session.get("admin_id", 1),  # TODO: Get from session
                user_type='admin',
                ip_address=request.remote_addr,
                details={
                    'plan_id': plan.id,
                    'plan_code': plan.code,
                    'plan_name': plan.name,
                    'reason': reason
                }
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash(f'⛔ پلن "{plan.name}" غیرفعال شد', 'warning')
        except Exception as e:
            flash(f'❌ خطا در غیرفعال‌سازی پلن: {str(e)}', 'danger')
        
        return redirect(url_for('plan_release_manager'))
    
    
    @app.route('/admin/plans/<int:plan_id>/schedule', methods=['POST'])
    def schedule_plan_route(plan_id):
        """برنامه‌ریزی انتشار آینده پلن"""
        plan = Plan.query.get_or_404(plan_id)
        
        release_date_str = request.form.get('release_date')
        release_time_str = request.form.get('release_time', '00:00')
        release_notes = request.form.get('release_notes', '')
        
        try:
            # تبدیل به datetime
            release_datetime = datetime.strptime(
                f"{release_date_str} {release_time_str}",
                "%Y-%m-%d %H:%M"
            )
            
            # برنامه‌ریزی
            schedule_plan_release(plan.code, release_datetime, release_notes)
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='plan_scheduled',
                user_id=session.get("admin_id", 1),  # TODO: Get from session
                user_type='admin',
                ip_address=request.remote_addr,
                details={
                    'plan_id': plan.id,
                    'plan_code': plan.code,
                    'plan_name': plan.name,
                    'scheduled_for': release_datetime.isoformat(),
                    'notes': release_notes
                }
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash(f'📅 انتشار پلن "{plan.name}" برای {release_date_str} برنامه‌ریزی شد', 'info')
        except Exception as e:
            flash(f'❌ خطا در برنامه‌ریزی: {str(e)}', 'danger')
        
        return redirect(url_for('plan_release_manager'))
    
    
    @app.route('/admin/plans/<int:plan_id>/history')
    def plan_release_history_route(plan_id):
        """تاریخچه انتشار پلن"""
        plan = Plan.query.get_or_404(plan_id)
        
        # دریافت تاریخچه
        history = get_plan_release_history(plan.code)
        
        return render_template('admin/plan_release_history.html', plan=plan, history=history)
    
    
    @app.route('/admin/beta-testers')
    def beta_testers_list():
        """لیست بتا تسترها"""
        testers = BetaTester.query.order_by(BetaTester.added_at.desc()).all()
        candidates = Candidate.query.all()
        
        return render_template('admin/beta_testers.html', testers=testers, candidates=candidates)
    
    
    @app.route('/admin/beta-testers/add', methods=['POST'])
    def add_beta_tester():
        """اضافه کردن بتا تستر"""
        candidate_id = request.form.get('candidate_id', type=int)
        plan_code = request.form.get('plan_code', '')
        
        try:
            # بررسی تکراری نبودن
            existing = BetaTester.query.filter_by(candidate_id=candidate_id).first()
            if existing:
                flash('❌ این کاندید قبلاً به برنامه بتا اضافه شده', 'warning')
                return redirect(url_for('beta_testers_list'))
            
            # اضافه کردن
            tester = BetaTester(
                candidate_id=candidate_id,
                plan_code=plan_code if plan_code else None,
                added_by_admin_id=1  # TODO: Get from session
            )
            db.session.add(tester)
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='beta_tester_added',
                user_id=session.get("admin_id", 1),
                user_type='admin',
                ip_address=request.remote_addr,
                details={'candidate_id': candidate_id, 'plan_code': plan_code}
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash('✅ بتا تستر با موفقیت اضافه شد', 'success')
        except Exception as e:
            flash(f'❌ خطا: {str(e)}', 'danger')
            db.session.rollback()
        
        return redirect(url_for('beta_testers_list'))
    
    
    @app.route('/admin/beta-testers/<int:tester_id>/remove', methods=['POST'])
    def remove_beta_tester(tester_id):
        """حذف بتا تستر"""
        tester = BetaTester.query.get_or_404(tester_id)
        
        try:
            db.session.delete(tester)
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='beta_tester_removed',
                user_id=session.get("admin_id", 1),
                user_type='admin',
                ip_address=request.remote_addr,
                details={'candidate_id': tester.candidate_id}
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash('✅ بتا تستر حذف شد', 'success')
        except Exception as e:
            flash(f'❌ خطا: {str(e)}', 'danger')
            db.session.rollback()
        
        return redirect(url_for('beta_testers_list'))
    
    
    @app.route('/admin/discount-campaigns')
    def discount_campaigns_list():
        """لیست کمپین‌های تخفیف"""
        campaigns = DiscountCampaign.query.order_by(DiscountCampaign.start_date.desc()).all()
        plans = Plan.query.all()
        
        return render_template('admin/discount_campaigns.html', 
                             campaigns=campaigns, 
                             plans=plans,
                             now=datetime.now)
    
    
    @app.route('/admin/discount-campaigns/create', methods=['POST'])
    def create_discount_campaign():
        """ایجاد کمپین تخفیف"""
        plan_code = request.form.get('plan_code')
        discount_percent = request.form.get('discount_percent', type=float)
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            campaign = DiscountCampaign(
                plan_code=plan_code,
                discount_percent=discount_percent,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(campaign)
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='discount_campaign_created',
                user_id=session.get("admin_id", 1),
                user_type='admin',
                ip_address=request.remote_addr,
                details={
                    'plan_code': plan_code,
                    'discount_percent': discount_percent,
                    'start_date': start_date_str,
                    'end_date': end_date_str
                }
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash(f'✅ کمپین تخفیف {discount_percent}% برای {plan_code} ایجاد شد', 'success')
        except Exception as e:
            flash(f'❌ خطا: {str(e)}', 'danger')
            db.session.rollback()
        
        return redirect(url_for('discount_campaigns_list'))
    
    
    @app.route('/admin/discount-campaigns/<int:campaign_id>/toggle', methods=['POST'])
    def toggle_discount_campaign(campaign_id):
        """فعال/غیرفعال کردن کمپین"""
        campaign = DiscountCampaign.query.get_or_404(campaign_id)
        
        try:
            campaign.is_active = not campaign.is_active
            safe_commit(db, "Database commit failed")
            
            status = 'فعال' if campaign.is_active else 'غیرفعال'
            flash(f'✅ کمپین {status} شد', 'success')
        except Exception as e:
            flash(f'❌ خطا: {str(e)}', 'danger')
            db.session.rollback()
        
        return redirect(url_for('discount_campaigns_list'))
    
    
    @app.route('/admin/discount-campaigns/<int:campaign_id>/end', methods=['POST'])
    def end_discount_campaign(campaign_id):
        """پایان دادن به کمپین تخفیف"""
        campaign = DiscountCampaign.query.get_or_404(campaign_id)
        
        try:
            campaign.is_active = False
            campaign.end_date = datetime.now()
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='discount_campaign_ended',
                user_id=session.get("admin_id", 1),  # TODO: Get from session
                user_type='admin',
                ip_address=request.remote_addr,
                details={
                    'campaign_id': campaign.id,
                    'plan_code': campaign.plan_code,
                    'discount_percent': campaign.discount_percent
                }
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash('✅ کمپین تخفیف با موفقیت پایان یافت', 'success')
        except Exception as e:
            flash(f'❌ خطا: {str(e)}', 'danger')
            db.session.rollback()
        
        return redirect(url_for('discount_campaigns_list'))
    
    
    @app.route('/admin/plans/migrate-users', methods=['POST'])
    def migrate_users_route():
        """انتقال دسته‌جمعی کاربران به پلن جدید"""
        old_plan_code = request.form.get('old_plan_code')
        new_plan_code = request.form.get('new_plan_code')
        reason = request.form.get('reason', 'ارتقا توسط مدیر')
        
        try:
            migrated_count = migrate_users_to_new_plan(old_plan_code, new_plan_code, reason)
            
            # ثبت در audit log
            audit = AuditLog(
                event_type='users_migrated',
                user_id=session.get("admin_id", 1),
                user_type='admin',
                ip_address=request.remote_addr,
                details={
                    'old_plan': old_plan_code,
                    'new_plan': new_plan_code,
                    'migrated_count': migrated_count,
                    'reason': reason
                }
            )
            db.session.add(audit)
            safe_commit(db, "Database commit failed")
            
            flash(f'✅ {migrated_count} کاربر از {old_plan_code} به {new_plan_code} منتقل شدند', 'success')
        except Exception as e:
            flash(f'❌ خطا: {str(e)}', 'danger')
        
        return redirect(url_for('plan_release_manager'))
    
    
    @app.route('/admin/plans/api/available')
    def api_available_plans():
        """API: لیست پلن‌های قابل خرید"""
        plans = get_available_plans(for_purchase=True)
        
        return jsonify({
            'success': True,
            'plans': [
                {
                    'id': p.id,
                    'name': p.name,
                    'code': p.code,
                    'price': p.price,
                    'is_available': check_plan_availability(p.code)
                }
                for p in plans
            ]
        })
    
    
    @app.route('/admin/plans/<int:plan_id>/api/check-availability')
    def api_check_plan_availability(plan_id):
        """API: بررسی در دسترس بودن پلن"""
        plan = Plan.query.get_or_404(plan_id)
        
        is_available = check_plan_availability(plan.code)
        
        return jsonify({
            'success': True,
            'plan_code': plan.code,
            'is_available': is_available,
            'release_scheduled_at': plan.release_scheduled_at.isoformat() if plan.release_scheduled_at else None
        })
