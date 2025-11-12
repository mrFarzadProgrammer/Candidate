# -*- coding: utf-8 -*-
"""
Test AI Features
=================
تست ویژگی‌های هوش مصنوعی
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_services.message_categorization import get_categorizer
from ai_services.sentiment_analyzer import get_sentiment_analyzer

def test_categorization():
    """تست دسته‌بندی"""
    print("=" * 60)
    print("🔬 تست دسته‌بندی خودکار پیام‌ها")
    print("=" * 60)
    
    categorizer = get_categorizer(use_ml=False)
    
    test_cases = [
        ("سلام، چرا خیابون ما آسفالت نشده؟ مشکل داره", "شکایت"),
        ("پیشنهاد می‌کنم پارک محله رو بسازید", "پیشنهاد"),
        ("برنامه‌تون برای حل ترافیک چیه؟", "سوال"),
        ("شما عالی هستید، به شما رای می‌دم", "حمایت"),
        ("متاسفانه با سیاست‌هاتون موافق نیستم", "انتقاد"),
    ]
    
    correct = 0
    for text, expected in test_cases:
        result = categorizer.categorize(text)
        is_correct = result['category'] == expected.lower()
        
        print(f"\n📝 متن: {text}")
        print(f"   ✅ انتظار: {expected}")
        print(f"   🤖 نتیجه: {result['category_fa']} ({result['category']})")
        print(f"   📊 اطمینان: {result['confidence']*100:.0f}%")
        print(f"   ⚡ اولویت: {result['priority']}")
        print(f"   {'✓ صحیح' if is_correct else '✗ اشتباه'}")
        
        if is_correct:
            correct += 1
    
    accuracy = correct / len(test_cases) * 100
    print(f"\n{'='*60}")
    print(f"📊 دقت کلی: {accuracy:.1f}% ({correct}/{len(test_cases)})")
    print(f"{'='*60}\n")
    
    return accuracy


def test_sentiment():
    """تست تحلیل احساسات"""
    print("=" * 60)
    print("🔬 تست تحلیل احساسات")
    print("=" * 60)
    
    analyzer = get_sentiment_analyzer(use_ml=False)
    
    test_cases = [
        ("شما واقعا عالی هستید! موفق باشید", "positive"),
        ("خیلی بد کار می‌کنید", "negative"),
        ("برنامه‌تون رو توضیح بدید", "neutral"),
        ("ممنون از زحماتتون", "positive"),
        ("متاسفانه راضی نیستم", "negative"),
    ]
    
    correct = 0
    for text, expected in test_cases:
        result = analyzer.analyze(text)
        is_correct = result['label'] == expected
        
        print(f"\n📝 متن: {text}")
        print(f"   ✅ انتظار: {expected}")
        print(f"   🤖 نتیجه: {result['label_fa']} ({result['label']})")
        print(f"   📊 نمره: {result['score']}")
        print(f"   💯 اطمینان: {result['confidence']*100:.0f}%")
        print(f"   ❤️  احساسات: {', '.join(result['emotions'])}")
        print(f"   {'✓ صحیح' if is_correct else '✗ اشتباه'}")
        
        if is_correct:
            correct += 1
    
    accuracy = correct / len(test_cases) * 100
    print(f"\n{'='*60}")
    print(f"📊 دقت کلی: {accuracy:.1f}% ({correct}/{len(test_cases)})")
    print(f"{'='*60}\n")
    
    return accuracy


def test_combined():
    """تست ترکیبی"""
    print("=" * 60)
    print("🔬 تست ترکیبی (دسته‌بندی + احساسات)")
    print("=" * 60)
    
    categorizer = get_categorizer(use_ml=False)
    analyzer = get_sentiment_analyzer(use_ml=False)
    
    messages = [
        "سلام، چرا خیابون ما چاله چوله شده؟ خیلی بده",
        "پیشنهاد می‌کنم پارک بسازید، عالی میشه",
        "برنامه شما برای ترافیک چیه؟",
        "شما واقعا عالی هستید، موفق باشید",
        "متاسفانه با سیاست‌های شما موافق نیستم"
    ]
    
    for i, msg in enumerate(messages, 1):
        cat_result = categorizer.categorize(msg)
        sent_result = analyzer.analyze(msg)
        
        print(f"\n{'='*60}")
        print(f"پیام #{i}: {msg}")
        print(f"{'='*60}")
        print(f"🏷️  دسته: {cat_result['category_fa']} | اولویت: {cat_result['priority']}")
        print(f"😊 احساس: {sent_result['label_fa']} | نمره: {sent_result['score']}")
        print(f"📊 اطمینان دسته‌بندی: {cat_result['confidence']*100:.0f}%")
        print(f"💯 اطمینان احساس: {sent_result['confidence']*100:.0f}%")


if __name__ == "__main__":
    print("\n\n")
    print("🚀 " + "="*56 + " 🚀")
    print("   تست سیستم هوش مصنوعی پیام‌های انتخاباتی")
    print("🚀 " + "="*56 + " 🚀")
    print("\n")
    
    cat_accuracy = test_categorization()
    sent_accuracy = test_sentiment()
    test_combined()
    
    print("\n\n")
    print("📊 " + "="*56 + " 📊")
    print("   خلاصه نتایج")
    print("📊 " + "="*56 + " 📊")
    print(f"\n   دقت دسته‌بندی: {cat_accuracy:.1f}%")
    print(f"   دقت تحلیل احساسات: {sent_accuracy:.1f}%")
    print(f"   میانگین کلی: {(cat_accuracy + sent_accuracy) / 2:.1f}%")
    print("\n   ✅ همه سیستم‌ها آماده‌اند!\n")
