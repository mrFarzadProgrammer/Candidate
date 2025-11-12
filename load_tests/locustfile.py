# -*- coding: utf-8 -*-
"""
Load Testing for Election Bot Management System
تست بار برای سیستم مدیریت ربات انتخاباتی

استفاده:
    locust -f locustfile.py --users 1000 --spawn-rate 100 --host http://localhost:5000
    
    یا با UI:
    locust -f locustfile.py
    سپس به http://localhost:8089 بروید
"""

from locust import HttpUser, task, between, events
import random
import json
from datetime import datetime


class CandidatePanelUser(HttpUser):
    """
    شبیه‌سازی کاربران پنل کاندید
    """
    wait_time = between(1, 3)  # صبر بین 1 تا 3 ثانیه بین درخواست‌ها
    
    def on_start(self):
        """اجرا می‌شه وقتی کاربر شروع می‌کنه"""
        self.login()
    
    def login(self):
        """لاگین به پنل کاندید"""
        response = self.client.get("/login")
        
        # استخراج CSRF token (اگر وجود داشته باشه)
        csrf_token = self.extract_csrf_token(response.text)
        
        # لاگین
        login_data = {
            "username": f"candidate_{random.randint(0, 9)}",
            "password": "Pass123"
        }
        
        if csrf_token:
            login_data["csrf_token"] = csrf_token
        
        response = self.client.post(
            "/login",
            data=login_data,
            catch_response=True
        )
        
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code}")
    
    def extract_csrf_token(self, html):
        """استخراج CSRF token از HTML"""
        try:
            start = html.find('name="csrf_token" value="') + len('name="csrf_token" value="')
            if start > len('name="csrf_token" value="') - 1:
                end = html.find('"', start)
                return html[start:end]
        except:
            pass
        return None
    
    @task(10)
    def view_dashboard(self):
        """مشاهده داشبورد (محبوب‌ترین صفحه)"""
        self.client.get("/dashboard", name="Dashboard")
    
    @task(5)
    def view_messages(self):
        """مشاهده پیام‌ها"""
        self.client.get("/messages", name="Messages List")
    
    @task(3)
    def view_users(self):
        """مشاهده کاربران"""
        self.client.get("/users", name="Users List")
    
    @task(2)
    def view_profile(self):
        """مشاهده پروفایل"""
        self.client.get("/profile", name="Profile")
    
    @task(2)
    def view_plans(self):
        """مشاهده پلن‌ها"""
        self.client.get("/plans", name="Plans")
    
    @task(1)
    def view_bot_settings(self):
        """مشاهده تنظیمات بات"""
        self.client.get("/bot/settings", name="Bot Settings")


class BroadcastUser(HttpUser):
    """
    شبیه‌سازی ارسال broadcast
    """
    wait_time = between(5, 10)
    
    def on_start(self):
        self.login()
    
    def login(self):
        """لاگین"""
        response = self.client.get("/login")
        csrf_token = self.extract_csrf_token(response.text)
        
        login_data = {
            "username": f"candidate_{random.randint(0, 4)}",
            "password": "Pass123"
        }
        
        if csrf_token:
            login_data["csrf_token"] = csrf_token
        
        self.client.post("/login", data=login_data)
    
    def extract_csrf_token(self, html):
        try:
            start = html.find('name="csrf_token" value="') + len('name="csrf_token" value="')
            if start > len('name="csrf_token" value="') - 1:
                end = html.find('"', start)
                return html[start:end]
        except:
            pass
        return None
    
    @task(1)
    def send_broadcast(self):
        """ارسال broadcast"""
        response = self.client.get("/broadcast")
        csrf_token = self.extract_csrf_token(response.text)
        
        broadcast_data = {
            "message": f"پیام تست {random.randint(1000, 9999)}",
            "target": "all"
        }
        
        if csrf_token:
            broadcast_data["csrf_token"] = csrf_token
        
        self.client.post(
            "/broadcast/send",
            data=broadcast_data,
            name="Send Broadcast"
        )


class MessageReadUser(HttpUser):
    """
    شبیه‌سازی خواندن پیام‌ها
    """
    wait_time = between(2, 5)
    
    def on_start(self):
        self.login()
    
    def login(self):
        response = self.client.get("/login")
        csrf_token = self.extract_csrf_token(response.text)
        
        login_data = {
            "username": f"candidate_{random.randint(0, 9)}",
            "password": "Pass123"
        }
        
        if csrf_token:
            login_data["csrf_token"] = csrf_token
        
        self.client.post("/login", data=login_data)
    
    def extract_csrf_token(self, html):
        try:
            start = html.find('name="csrf_token" value="') + len('name="csrf_token" value="')
            if start > len('name="csrf_token" value="') - 1:
                end = html.find('"', start)
                return html[start:end]
        except:
            pass
        return None
    
    @task(5)
    def read_messages(self):
        """خواندن پیام‌ها"""
        # فرض کنیم message_id از 1 تا 1000
        message_id = random.randint(1, 1000)
        
        response = self.client.get(f"/message/{message_id}")
        csrf_token = self.extract_csrf_token(response.text)
        
        # مارک کردن به عنوان خوانده شده
        mark_data = {}
        if csrf_token:
            mark_data["csrf_token"] = csrf_token
        
        self.client.post(
            f"/message/{message_id}/read",
            data=mark_data,
            name="Mark Message as Read"
        )


class AdminPanelUser(HttpUser):
    """
    شبیه‌سازی کاربران پنل ادمین
    """
    wait_time = between(2, 5)
    
    def on_start(self):
        self.login()
    
    def login(self):
        """لاگین به پنل ادمین"""
        response = self.client.get("/admin/login")
        csrf_token = self.extract_csrf_token(response.text)
        
        login_data = {
            "username": "admin_test",
            "password": "AdminPass123"
        }
        
        if csrf_token:
            login_data["csrf_token"] = csrf_token
        
        self.client.post("/admin/login", data=login_data)
    
    def extract_csrf_token(self, html):
        try:
            start = html.find('name="csrf_token" value="') + len('name="csrf_token" value="')
            if start > len('name="csrf_token" value="') - 1:
                end = html.find('"', start)
                return html[start:end]
        except:
            pass
        return None
    
    @task(5)
    def view_admin_dashboard(self):
        """مشاهده داشبورد ادمین"""
        self.client.get("/admin/dashboard", name="Admin Dashboard")
    
    @task(3)
    def view_candidates(self):
        """مشاهده لیست کاندیدها"""
        self.client.get("/admin/candidates", name="Candidates List")
    
    @task(2)
    def view_plans(self):
        """مشاهده پلن‌ها"""
        self.client.get("/admin/plans", name="Admin Plans")
    
    @task(1)
    def view_plan_release(self):
        """مشاهده صفحه انتشار پلن"""
        self.client.get("/admin/plans/release", name="Plan Release")


class DatabaseIntensiveUser(HttpUser):
    """
    شبیه‌سازی عملیات سنگین دیتابیس
    """
    wait_time = between(3, 7)
    
    def on_start(self):
        self.login()
    
    def login(self):
        response = self.client.get("/login")
        csrf_token = self.extract_csrf_token(response.text)
        
        login_data = {
            "username": f"candidate_{random.randint(0, 4)}",
            "password": "Pass123"
        }
        
        if csrf_token:
            login_data["csrf_token"] = csrf_token
        
        self.client.post("/login", data=login_data)
    
    def extract_csrf_token(self, html):
        try:
            start = html.find('name="csrf_token" value="') + len('name="csrf_token" value="')
            if start > len('name="csrf_token" value="') - 1:
                end = html.find('"', start)
                return html[start:end]
        except:
            pass
        return None
    
    @task(2)
    def view_analytics(self):
        """مشاهده آنالیتیکس (query های سنگین)"""
        self.client.get("/analytics", name="Analytics")
    
    @task(1)
    def export_data(self):
        """درخواست export داده (عملیات سنگین)"""
        response = self.client.get("/export")
        csrf_token = self.extract_csrf_token(response.text)
        
        export_data = {
            "type": random.choice(["users", "messages", "analytics"]),
            "format": random.choice(["json", "csv", "excel"]),
            "encryption_password": "TestPass123"
        }
        
        if csrf_token:
            export_data["csrf_token"] = csrf_token
        
        self.client.post(
            "/export/create",
            data=export_data,
            name="Create Export"
        )


# Event listeners برای آمار
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "="*50)
    print("🚀 Load Test شروع شد")
    print(f"⏰ زمان شروع: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*50)
    print("🏁 Load Test تمام شد")
    print(f"⏰ زمان پایان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    
    # آمار کلی
    stats = environment.stats
    print("\n📊 خلاصه آمار:")
    print(f"   Total Requests: {stats.total.num_requests}")
    print(f"   Failed Requests: {stats.total.num_failures}")
    print(f"   Average Response Time: {stats.total.avg_response_time:.2f} ms")
    print(f"   Max Response Time: {stats.total.max_response_time:.2f} ms")
    print(f"   Min Response Time: {stats.total.min_response_time:.2f} ms")
    print(f"   Requests/sec: {stats.total.total_rps:.2f}")
    
    # چک کردن موفقیت تست
    failure_rate = stats.total.fail_ratio
    if failure_rate > 0.01:  # بیش از 1% شکست
        print(f"\n⚠️ WARNING: Failure rate is {failure_rate*100:.2f}%")
    else:
        print(f"\n✅ SUCCESS: Failure rate is {failure_rate*100:.2f}%")
    
    # چک کردن response time
    avg_response = stats.total.avg_response_time
    if avg_response > 2000:  # بیش از 2 ثانیه
        print(f"⚠️ WARNING: Average response time is {avg_response:.2f} ms")
    else:
        print(f"✅ SUCCESS: Average response time is {avg_response:.2f} ms")


# تنظیمات پیشفرض
if __name__ == "__main__":
    import os
    os.system("locust -f locustfile.py")
