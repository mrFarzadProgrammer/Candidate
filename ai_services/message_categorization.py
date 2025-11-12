# -*- coding: utf-8 -*-
"""
Message Categorization Service
===============================
دسته‌بندی خودکار پیام‌های فارسی با استفاده از هوش مصنوعی

دسته‌بندی‌ها:
- complaint (شکایت): گله‌مندی از مشکلات شهری
- suggestion (پیشنهاد): ایده‌ها و پیشنهادات سازنده  
- question (سوال): سوالات درباره برنامه‌ها
- support (حمایت): پیام‌های حمایتی و تشویقی
- criticism (انتقاد): انتقادات سازنده
"""

from typing import Dict, Optional, List
import logging
from datetime import datetime
import re

# برای حالت fallback اگر مدل ML در دسترس نبود
KEYWORD_PATTERNS = {
    'complaint': [
        r'مشکل', r'شکایت', r'چرا', r'نمی\s*شود', r'نشده', r'نکرده',
        r'بد', r'ضعیف', r'افتضاح', r'آشغال', r'خراب', r'معیوب',
        r'گرونی', r'بیکاری', r'آلودگی', r'ترافیک', r'چاله', r'خیابون'
    ],
    'suggestion': [
        r'پیشنهاد', r'بهتر', r'می\s*تونید', r'می\s*شود', r'اگر', r'بد نیست',
        r'خوب\s+است', r'لازم', r'ضروری', r'باید', r'بایستی', r'می\s*توان'
    ],
    'question': [
        r'\?', r'چرا', r'کی', r'چگونه', r'چطور', r'آیا', r'چه\s+زمانی',
        r'برنامه', r'قصد', r'می\s*خواهید', r'می\s*خواید', r'سوال'
    ],
    'support': [
        r'عالی', r'موفق', r'برنده', r'حمایت', r'رای', r'می\s*دهم', r'می\s*دم',
        r'عزیز', r'دوست', r'محترم', r'آقای', r'خانم', r'درود', r'سلام',
        r'ممنون', r'تشکر', r'متشکر', r'خسته\s+نباش', r'افتخار'
    ],
    'criticism': [
        r'انتقاد', r'نقد', r'اما', r'ولی', r'متاسف', r'متاسفانه',
        r'نه', r'خیر', r'موافق نیست', r'اشتباه', r'غلط', r'نادرست'
    ]
}

CATEGORY_NAMES_FA = {
    'complaint': 'شکایت',
    'suggestion': 'پیشنهاد',
    'question': 'سوال',
    'support': 'حمایت',
    'criticism': 'انتقاد',
    'unknown': 'نامشخص'
}

PRIORITY_MAP = {
    'complaint': 'high',      # شکایت اولویت بالا
    'question': 'high',       # سوال اولویت بالا
    'criticism': 'medium',    # انتقاد اولویت متوسط
    'suggestion': 'medium',   # پیشنهاد اولویت متوسط
    'support': 'low',         # حمایت اولویت پایین
    'unknown': 'low'
}

logger = logging.getLogger(__name__)


class MessageCategorizer:
    """
    کلاس اصلی برای دسته‌بندی پیام‌ها
    
    از دو روش استفاده می‌کند:
    1. ML-based: مدل ParsBERT برای دسته‌بندی دقیق
    2. Rule-based: الگوهای کلیدواژه برای fallback
    """
    
    def __init__(self, use_ml: bool = True):
        """
        Args:
            use_ml: استفاده از مدل ML یا فقط rule-based
        """
        self.use_ml = use_ml
        self.ml_model = None
        
        if use_ml:
            try:
                self._load_ml_model()
            except Exception as e:
                logger.warning(f"Could not load ML model, falling back to rule-based: {e}")
                self.use_ml = False
    
    def _load_ml_model(self):
        """بارگذاری مدل ML"""
        try:
            from transformers import pipeline
            
            # استفاده از مدل فارسی
            # در حالت واقعی، باید مدل fine-tune شده استفاده شود
            self.ml_model = pipeline(
                "text-classification",
                model="HooshvareLab/bert-fa-base-uncased",
                device=-1  # CPU (-1), GPU (0)
            )
            logger.info("ML model loaded successfully")
        except ImportError:
            logger.error("transformers not installed, install with: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            raise
    
    def categorize(self, text: str) -> Dict:
        """
        دسته‌بندی پیام
        
        Args:
            text: متن پیام فارسی
        
        Returns:
            dict شامل:
                - category: دسته (complaint, suggestion, ...)
                - category_fa: نام فارسی دسته
                - confidence: اطمینان (0-1)
                - priority: اولویت (high, medium, low)
                - method: روش استفاده شده (ml, rule_based)
        """
        if not text or not text.strip():
            return self._create_result('unknown', 0.0, 'empty')
        
        # تمیز کردن متن
        text = self._clean_text(text)
        
        # تلاش با ML
        if self.use_ml and self.ml_model:
            try:
                result = self._categorize_ml(text)
                if result['confidence'] > 0.5:  # threshold
                    return result
            except Exception as e:
                logger.error(f"ML categorization failed: {e}")
        
        # fallback به rule-based
        return self._categorize_rule_based(text)
    
    def _categorize_ml(self, text: str) -> Dict:
        """دسته‌بندی با ML"""
        # در حالت واقعی باید مدل fine-tune شده باشه
        # این فقط یک مثال است
        result = self.ml_model(text)[0]
        
        # map کردن label به category
        category = self._map_label_to_category(result['label'])
        confidence = result['score']
        
        return self._create_result(category, confidence, 'ml')
    
    def _categorize_rule_based(self, text: str) -> Dict:
        """دسته‌بندی بر اساس کلیدواژه"""
        scores = {cat: 0 for cat in KEYWORD_PATTERNS.keys()}
        
        # محاسبه امتیاز هر دسته
        for category, patterns in KEYWORD_PATTERNS.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                scores[category] += matches
        
        # انتخاب دسته با بالاترین امتیاز
        if max(scores.values()) == 0:
            return self._create_result('unknown', 0.0, 'rule_based')
        
        best_category = max(scores, key=scores.get)
        total_matches = sum(scores.values())
        confidence = scores[best_category] / total_matches if total_matches > 0 else 0.0
        
        return self._create_result(best_category, confidence, 'rule_based')
    
    def _create_result(self, category: str, confidence: float, method: str) -> Dict:
        """ساخت نتیجه استاندارد"""
        return {
            'category': category,
            'category_fa': CATEGORY_NAMES_FA.get(category, 'نامشخص'),
            'confidence': round(confidence, 2),
            'priority': PRIORITY_MAP.get(category, 'low'),
            'method': method,
            'timestamp': datetime.now().isoformat()
        }
    
    def _clean_text(self, text: str) -> str:
        """تمیز کردن و نرمال‌سازی متن"""
        # حذف کاراکترهای اضافی
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # نرمال‌سازی با hazm (اگر نصب باشد)
        try:
            from hazm import Normalizer
            normalizer = Normalizer()
            text = normalizer.normalize(text)
        except ImportError:
            pass
        
        return text
    
    def _map_label_to_category(self, label: str) -> str:
        """تبدیل label مدل به category"""
        # mapping بر اساس مدل استفاده شده
        # این باید customize بشه
        label_lower = label.lower()
        
        if 'complaint' in label_lower or 'negative' in label_lower:
            return 'complaint'
        elif 'suggestion' in label_lower or 'proposal' in label_lower:
            return 'suggestion'
        elif 'question' in label_lower or 'query' in label_lower:
            return 'question'
        elif 'support' in label_lower or 'positive' in label_lower:
            return 'support'
        elif 'criticism' in label_lower or 'critique' in label_lower:
            return 'criticism'
        else:
            return 'unknown'
    
    def batch_categorize(self, texts: List[str]) -> List[Dict]:
        """دسته‌بندی دسته‌جمعی"""
        return [self.categorize(text) for text in texts]
    
    def get_statistics(self, results: List[Dict]) -> Dict:
        """آمار دسته‌بندی"""
        if not results:
            return {}
        
        stats = {
            'total': len(results),
            'by_category': {},
            'by_priority': {},
            'avg_confidence': 0.0,
            'method_usage': {}
        }
        
        for result in results:
            # by category
            cat = result['category']
            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
            
            # by priority
            priority = result['priority']
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # method
            method = result['method']
            stats['method_usage'][method] = stats['method_usage'].get(method, 0) + 1
            
            # confidence
            stats['avg_confidence'] += result['confidence']
        
        stats['avg_confidence'] /= len(results)
        stats['avg_confidence'] = round(stats['avg_confidence'], 2)
        
        return stats


# Instance سراسری (singleton pattern)
_categorizer_instance = None

def get_categorizer(use_ml: bool = True) -> MessageCategorizer:
    """دریافت instance سراسری"""
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = MessageCategorizer(use_ml=use_ml)
    return _categorizer_instance


# تست سریع
if __name__ == "__main__":
    # تست با rule-based (بدون نیاز به ML)
    categorizer = MessageCategorizer(use_ml=False)
    
    test_messages = [
        "سلام، چرا خیابون محله ما آسفالت نشده؟",
        "شما عالی هستید، موفق باشید",
        "پیشنهاد می‌کنم یک پارک در محله بسازید",
        "برنامه شما برای ترافیک چیه؟",
        "متاسفانه با سیاست‌های شما موافق نیستم"
    ]
    
    print("🧪 تست دسته‌بندی پیام‌ها:\n")
    for msg in test_messages:
        result = categorizer.categorize(msg)
        print(f"📝 پیام: {msg}")
        print(f"   🏷️  دسته: {result['category_fa']} ({result['category']})")
        print(f"   📊 اطمینان: {result['confidence']*100:.0f}%")
        print(f"   ⚡ اولویت: {result['priority']}")
        print(f"   🔧 روش: {result['method']}\n")
