# modules/advanced_sentiment.py
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import re
from collections import Counter

class AdvancedSentimentAnalyzer:
    def __init__(self):
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                tokenizer="nlptown/bert-base-multilingual-uncased-sentiment"
            )
            
            self.emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base", 
                return_all_scores=True
            )
        except:
            # Fallback to simple analyzer if models not available
            self.sentiment_analyzer = None
            self.emotion_classifier = None
    
    def analyze_user_state(self, user_message):
        """Phân tích c?m xúc và tr?ng thái ng??i dùng"""
        if self.sentiment_analyzer is None:
            return self._simple_analysis(user_message)
            
        try:
            # Sentiment analysis
            sentiment_result = self.sentiment_analyzer(user_message)[0]
            
            # Emotion detection
            emotion_results = self.emotion_classifier(user_message)[0]
            top_emotion = max(emotion_results, key=lambda x: x['score'])
            
            return {
                'sentiment': sentiment_result['label'],
                'sentiment_score': sentiment_result['score'],
                'emotion': top_emotion['label'],
                'emotion_score': top_emotion['score'],
                'urgency': self._detect_urgency(user_message),
                'needs': self._extract_needs(user_message),
                'special_scenario': self._detect_special_scenario(user_message)
            }
        except:
            return self._simple_analysis(user_message)
    
    def _simple_analysis(self, text):
        """Phân tích ??n gi?n khi không có model"""
        text_lower = text.lower()
        
        # Basic sentiment detection
        positive_words = ['vui', 't?t', 'tuy?t', 'thích', 'happy', 'good']
        negative_words = ['bu?n', 't?', 'x?u', 'ghét', 'sad', 'bad', 'huhu', 'ti?c']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
            
        return {
            'sentiment': sentiment,
            'sentiment_score': 0.8,
            'emotion': self._detect_emotion_simple(text_lower),
            'emotion_score': 0.7,
            'urgency': self._detect_urgency(text_lower),
            'needs': self._extract_needs(text_lower),
            'special_scenario': self._detect_special_scenario(text_lower)
        }
    
    def _detect_emotion_simple(self, text_lower):
        """Phát hi?n c?m xúc ??n gi?n"""
        emotion_keywords = {
            'sadness': ['bu?n', 'huhu', 'khóc', 'th?t v?ng', 'chia tay', 'm?t'],
            'joy': ['vui', 'happy', 'ph?n khích', 'tuy?t v?i', 'thích'],
            'anger': ['t?c', 'gi?n', 'b?c', 'khó ch?u', 't?c gi?n'],
            'fear': ['s?', 'lo', 'ho?ng', 'b?t an', 'lo l?ng'],
            'surprise': ['ôi', 'wow', 'b?t ng?', 'ng?c nhiên']
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        return 'neutral'
    
    def _detect_urgency(self, text):
        """Phát hi?n m?c ?? kh?n c?p"""
        text_lower = text.lower()
        urgency_keywords = {
            'high': ['g?p', 'ngay', 'kh?n c?p', 'c?n ngay', 'nhanh', 'l?p t?c'],
            'medium': ['s?m', 'tu?n sau', 'tháng sau', 'k? ho?ch', 'd? ??nh'],
            'low': ['lúc nào c?ng ???c', 'không v?i', 't??ng lai', 'khi nào r?nh']
        }
        
        for level, keywords in urgency_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return level
        return 'medium'
    
    def _extract_needs(self, text):
        """Trích xu?t nhu c?u ?n"""
        text_lower = text.lower()
        needs = []
        
        need_patterns = {
            'relaxation': ['th? giãn', 'ngh? ng?i', 'x? stress', 'm?t m?i', 'c?ng th?ng'],
            'celebration': ['k? ni?m', 'sinh nh?t', 'c??i', 'thành công', '?n m?ng'],
            'business': ['công tác', 'meeting', '??i tác', 'd? án', 'work'],
            'adventure': ['khám phá', 'tr?i nghi?m', 'm?o hi?m', 'm?i l?', 'phiêu l?u'],
            'healing': ['ch?a lành', 't?nh tâm', 'thi?n', 'suy ngh?', 'chia tay'],
            'family': ['gia ?ình', 'con nh?', 'tr? em', 'b? m?', 'ông bà'],
            'romance': ['lãng m?n', 'ng??i yêu', 'c?p ?ôi', 'tình nhân', 'anniversary']
        }
        
        for need, patterns in need_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                needs.append(need)
                
        return needs if needs else ['general_travel']
    
    def _detect_special_scenario(self, text):
        """Phát hi?n các tình hu?ng ??c bi?t c?n x? lý"""
        text_lower = text.lower()
        
        special_scenarios = {
            'room_unavailable': ['h?t phòng', 'h?t ch?', 'full phòng', '??y phòng', 'không còn phòng', 'm?t tiu'],
            'price_concern': ['??t quá', 'm?c quá', 'giá cao', 'over budget', '??t ??'],
            'quality_concern': ['s?ch không', 'v? sinh', 'b?n', 'd?', '??m b?o', 'cam k?t'],
            'safety_concern': ['an toàn không', 'có an ninh', 'nguy hi?m', 'safe', 'security'],
            'urgent_booking': ['g?p l?m', 'ngay bây gi?', 'kh?n c?p', 'c?n ngay', 'l?p t?c']
        }
        
        for scenario, keywords in special_scenarios.items():
            if any(keyword in text_lower for keyword in keywords):
                return scenario
        
        return None
    
    def analyze_quality_concerns(self, user_message):
        """Phân tích các lo l?ng v? ch?t l??ng d?ch v?"""
        text_lower = user_message.lower()
        
        quality_concerns = {
            'cleanliness': {
                'keywords': ['s?ch không', 'v? sinh', 'b?n', 'd?', 'clean', 'hygiene'],
                'focus': 'housekeeping_standards',
                'urgency': 'medium'
            },
            'safety': {
                'keywords': ['an toàn không', 'có an ninh', 'nguy hi?m', 'safe', 'security'],
                'focus': 'safety_measures', 
                'urgency': 'high'
            },
            'service_quality': {
                'keywords': ['nhân viên t?t không', 'd?ch v?', 'ph?c v?', 'service', 'staff'],
                'focus': 'service_standards',
                'urgency': 'medium'
            },
            'facility_condition': {
                'keywords': ['h? b?i s?ch', 'phòng c?', 'thi?t b?', 'facility', 'condition'],
                'focus': 'maintenance',
                'urgency': 'medium'
            },
            'direct_guarantee': {
                'keywords': ['có ??m b?o không', 'b?n ??m b?o', 'cam k?t', 'ch?c ch?n không'],
                'focus': 'accountability',
                'urgency': 'high'
            }
        }
        
        for concern, data in quality_concerns.items():
            if any(keyword in text_lower for keyword in data['keywords']):
                return concern, data
        
        return None, None