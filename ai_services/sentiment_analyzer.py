# -*- coding: utf-8 -*-
"""
Sentiment Analysis Service
===========================
تحلیل احساسات پیام‌های فارسی

تشخیص احساس پیام:
- positive (مثبت): 0.3 تا 1.0
- neutral (خنثی): -0.3 تا 0.3
- negative (منفی): -1.0 تا -0.3
"""

from typing import Dict, Optional, List
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# واژگان احساسی فارسی (Sentiment Lexicon)
POSITIVE_WORDS = [
    'عالی', 'خوب', 'موفق', 'برنده', 'حمایت', 'رای', 'عزیز', 'محترم',
    'ممنون', 'تشکر', 'متشکر', 'خسته نباش', 'افتخار', 'دوست', 'سلام',
    'درود', 'موید', 'صد درصد', 'کامل', 'بهترین', 'مناسب', 'مفید',
    'خوشحال', 'راضی', 'مطمئن', 'امیدوار', 'پیشرفت', 'رشد', 'موفقیت'
]

NEGATIVE_WORDS = [
    'بد', 'ضعیف', 'افتضاح', 'آشغال', 'خراب', 'معیوب', 'مشکل', 'شکایت',
    'متاسف', 'متاسفانه', 'نه', 'خیر', 'اشتباه', 'غلط', 'نادرست',
    'ناراحت', 'عصبانی', 'ناامید', 'نگران', 'ترس', 'دلسرد', 'ناکام'
]

INTENSIFIERS = {
    'خیلی': 1.5,
    'بسیار': 1.5,
    'بی نهایت': 2.0,
    'فوق العاده': 1.8,
    'واقعا': 1.3,
    'اصلا': 1.4,
    'کاملا': 1.5,
    'به شدت': 1.6
}

NEGATIONS = ['نه', 'نی', 'ندارم', 'نیست', 'نمی', 'هیچ', 'بدون']


class SentimentAnalyzer:
    """
    تحلیل‌گر احساسات فارسی
    
    از دو روش استفاده می‌کند:
    1. Lexicon-based: بر اساس واژگان احساسی
    2. ML-based: مدل‌های deep learning (در آینده)
    """
    
    def __init__(self, use_ml: bool = False):
        """
        Args:
            use_ml: استفاده از مدل ML (فعلاً False)
        """
        self.use_ml = use_ml
        self.ml_model = None
        
        if use_ml:
            try:
                self._load_ml_model()
            except Exception as e:
                logger.warning(f"Could not load sentiment ML model: {e}")
                self.use_ml = False
    
    def _load_ml_model(self):
        """بارگذاری مدل ML"""
        try:
            from transformers import pipeline
            
            # مدل sentiment analysis فارسی
            # مثال: HooshvareLab/bert-fa-base-uncased-sentiment
            self.ml_model = pipeline(
                "sentiment-analysis",
                model="HooshvareLab/bert-fa-base-uncased-sentiment",
                device=-1
            )
            logger.info("Sentiment ML model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentiment model: {e}")
            raise
    
    def analyze(self, text: str) -> Dict:
        """
        تحلیل احساس متن
        
        Args:
            text: متن فارسی
        
        Returns:
            dict شامل:
                - score: نمره (-1 تا 1)
                - label: positive, neutral, negative
                - confidence: اطمینان (0-1)
                - emotions: احساسات تشخیص داده شده
        """
        if not text or not text.strip():
            return self._create_result(0.0, 'neutral', 0.0, 'empty')
        
        # تمیز کردن متن
        text = self._clean_text(text)
        
        # تلاش با ML
        if self.use_ml and self.ml_model:
            try:
                result = self._analyze_ml(text)
                if result['confidence'] > 0.6:
                    return result
            except Exception as e:
                logger.error(f"ML sentiment analysis failed: {e}")
        
        # fallback به lexicon-based
        return self._analyze_lexicon(text)
    
    def _analyze_ml(self, text: str) -> Dict:
        """تحلیل با ML"""
        result = self.ml_model(text)[0]
        
        # تبدیل label به score
        label = result['label'].lower()
        if 'positive' in label or 'pos' in label:
            score = 0.7
            label = 'positive'
        elif 'negative' in label or 'neg' in label:
            score = -0.7
            label = 'negative'
        else:
            score = 0.0
            label = 'neutral'
        
        confidence = result['score']
        
        return self._create_result(score, label, confidence, 'ml')
    
    def _analyze_lexicon(self, text: str) -> Dict:
        """تحلیل بر اساس واژگان"""
        words = text.split()
        
        positive_count = 0
        negative_count = 0
        intensity_factor = 1.0
        has_negation = False
        
        for i, word in enumerate(words):
            # بررسی نفی
            if any(neg in word for neg in NEGATIONS):
                has_negation = True
                continue
            
            # بررسی تشدید
            for intensifier, factor in INTENSIFIERS.items():
                if intensifier in word:
                    intensity_factor = factor
                    break
            
            # بررسی کلمات مثبت
            if any(pos in word for pos in POSITIVE_WORDS):
                if has_negation:
                    negative_count += intensity_factor
                    has_negation = False
                else:
                    positive_count += intensity_factor
                intensity_factor = 1.0
            
            # بررسی کلمات منفی
            elif any(neg in word for neg in NEGATIVE_WORDS):
                if has_negation:
                    positive_count += intensity_factor
                    has_negation = False
                else:
                    negative_count += intensity_factor
                intensity_factor = 1.0
        
        # محاسبه نمره
        total = positive_count + negative_count
        if total == 0:
            score = 0.0
            label = 'neutral'
            confidence = 0.3
        else:
            score = (positive_count - negative_count) / total
            
            if score > 0.3:
                label = 'positive'
            elif score < -0.3:
                label = 'negative'
            else:
                label = 'neutral'
            
            confidence = min(abs(score) + 0.3, 1.0)
        
        return self._create_result(score, label, confidence, 'lexicon')
    
    def _create_result(self, score: float, label: str, confidence: float, method: str) -> Dict:
        """ساخت نتیجه استاندارد"""
        label_fa = {
            'positive': 'مثبت',
            'neutral': 'خنثی',
            'negative': 'منفی'
        }
        
        # شناسایی احساسات
        emotions = self._detect_emotions(score, label)
        
        return {
            'score': round(score, 2),
            'label': label,
            'label_fa': label_fa.get(label, 'نامشخص'),
            'confidence': round(confidence, 2),
            'emotions': emotions,
            'method': method,
            'timestamp': datetime.now().isoformat()
        }
    
    def _detect_emotions(self, score: float, label: str) -> List[str]:
        """شناسایی احساسات دقیق‌تر"""
        emotions = []
        
        if label == 'positive':
            if score > 0.7:
                emotions.append('بسیار خوشحال')
            elif score > 0.5:
                emotions.append('خوشحال')
            else:
                emotions.append('راضی')
        
        elif label == 'negative':
            if score < -0.7:
                emotions.append('بسیار ناراحت')
            elif score < -0.5:
                emotions.append('ناراحت')
            else:
                emotions.append('نگران')
        
        else:
            emotions.append('خنثی')
        
        return emotions
    
    def _clean_text(self, text: str) -> str:
        """تمیز کردن متن"""
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # نرمال‌سازی با hazm
        try:
            from hazm import Normalizer
            normalizer = Normalizer()
            text = normalizer.normalize(text)
        except ImportError:
            pass
        
        return text
    
    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """تحلیل دسته‌جمعی"""
        return [self.analyze(text) for text in texts]
    
    def get_sentiment_trend(self, results: List[Dict]) -> Dict:
        """روند احساسات"""
        if not results:
            return {}
        
        positive_count = sum(1 for r in results if r['label'] == 'positive')
        neutral_count = sum(1 for r in results if r['label'] == 'neutral')
        negative_count = sum(1 for r in results if r['label'] == 'negative')
        
        total = len(results)
        avg_score = sum(r['score'] for r in results) / total
        
        return {
            'total': total,
            'positive': positive_count,
            'neutral': neutral_count,
            'negative': negative_count,
            'positive_percent': round(positive_count / total * 100, 1),
            'neutral_percent': round(neutral_count / total * 100, 1),
            'negative_percent': round(negative_count / total * 100, 1),
            'avg_score': round(avg_score, 2),
            'overall': 'positive' if avg_score > 0.2 else 'negative' if avg_score < -0.2 else 'neutral'
        }


# Singleton instance
_analyzer_instance = None

def get_sentiment_analyzer(use_ml: bool = False) -> SentimentAnalyzer:
    """دریافت instance سراسری"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SentimentAnalyzer(use_ml=use_ml)
    return _analyzer_instance


# تست
if __name__ == "__main__":
    analyzer = SentimentAnalyzer(use_ml=False)
    
    test_messages = [
        "شما واقعا عالی هستید! خیلی موفق باشید 👍",
        "متاسفانه با برنامه‌های شما موافق نیستم",
        "برنامه‌تون رو توضیح بدید لطفا",
        "خیلی بد کار می‌کنید، اصلا راضی نیستم",
        "ممنون از زحماتتون، امیدوارم موفق بشید"
    ]
    
    print("🧪 تست تحلیل احساسات:\n")
    for msg in test_messages:
        result = analyzer.analyze(msg)
        print(f"📝 پیام: {msg}")
        print(f"   😊 احساس: {result['label_fa']} ({result['label']})")
        print(f"   📊 نمره: {result['score']}")
        print(f"   💯 اطمینان: {result['confidence']*100:.0f}%")
        print(f"   ❤️  احساسات: {', '.join(result['emotions'])}")
        print(f"   🔧 روش: {result['method']}\n")
    
    # تست روند
    results = [analyzer.analyze(msg) for msg in test_messages]
    trend = analyzer.get_sentiment_trend(results)
    print("📈 روند کلی احساسات:")
    print(f"   مثبت: {trend['positive_percent']}%")
    print(f"   خنثی: {trend['neutral_percent']}%")
    print(f"   منفی: {trend['negative_percent']}%")
    print(f"   میانگین: {trend['avg_score']}")
    print(f"   نتیجه: {trend['overall']}")
