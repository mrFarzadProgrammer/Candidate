"""
تولید کلیدهای امنیتی تصادفی برای استفاده در Production
"""
import secrets

print("🔐 تولید کلیدهای امنیتی تصادفی")
print("=" * 60)
print("\nبرای استفاده در Environment Variables سرور:\n")

print("ADMIN_SECRET_KEY:")
print(secrets.token_hex(32))

print("\nCANDIDATE_SECRET_KEY:")
print(secrets.token_hex(32))

print("\n" + "=" * 60)
print("💡 این کلیدها را در تنظیمات Render یا Railway وارد کنید")
