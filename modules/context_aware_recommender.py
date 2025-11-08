# modules/context_aware_recommender.py
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

class ContextAwareRecommender:
    def __init__(self):
        try:
            # Pre-trained sentence embeddings
            self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except:
            self.sentence_model = None
        
        # Context embeddings
        self.context_embeddings = self._initialize_context_embeddings()
        
    def _initialize_context_embeddings(self):
        """Kh?i t?o embeddings cho các ng? c?nh du l?ch"""
        contexts = {
            'heartbreak_recovery': "bu?n tình c?m chia tay healing tâm h?n th?t tình cô ??n",
            'business_trip': "công tác chuyên nghi?p hi?u qu? meeting ??i tác work",
            'family_vacation': "gia ?ình tr? em an toàn vui ch?i tr? nh?", 
            'romantic_getaway': "lãng m?n c?p ?ôi riêng t? ??c bi?t tình nhân",
            'solo_adventure': "m?t mình khám phá t? do tr?i nghi?m cá nhân",
            'stress_relief': "c?ng th?ng ngh? ng?i th? giãn tr? li?u m?t m?i",
            'celebration': "k? ni?m ?n m?ng party vui v? thành công",
            'workation': "làm vi?c t? xa digital nomad wifi yên t?nh"
        }
        
        if self.sentence_model:
            return {key: self.sentence_model.encode([value])[0] for key, value in contexts.items()}
        else:
            return contexts
    
    def predict_travel_context(self, user_message, user_history=None):
        """D? ?oán ng? c?nh du l?ch"""
        if self.sentence_model is None:
            return self._simple_context_prediction(user_message)
            
        try:
            user_embedding = self.sentence_model.encode([user_message])[0]
            
            similarities = {}
            for context, context_embedding in self.context_embeddings.items():
                similarity = cosine_similarity([user_embedding], [context_embedding])[0][0]
                similarities[context] = similarity
            
            # L?y top 2 contexts
            top_contexts = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:2]
            
            return {
                'primary_context': top_contexts[0][0],
                'secondary_context': top_contexts[1][0] if len(top_contexts) > 1 else None,
                'confidence_scores': similarities
            }
        except:
            return self._simple_context_prediction(user_message)
    
    def _simple_context_prediction(self, user_message):
        """D? ?oán ng? c?nh ??n gi?n"""
        text_lower = user_message.lower()
        
        context_keywords = {
            'heartbreak_recovery': ['chia tay', 'bu?n', 'th?t tình', 'cô ??n', 'tình c?m'],
            'business_trip': ['công tác', 'meeting', '??i tác', 'work', 'business'],
            'family_vacation': ['gia ?ình', 'con nh?', 'tr? em', 'b? m?'],
            'romantic_getaway': ['lãng m?n', 'ng??i yêu', 'c?p ?ôi', 'tình nhân'],
            'solo_adventure': ['m?t mình', 'solo', '?i riêng', 'cá nhân'],
            'workation': ['làm vi?c', 'wifi', 'yên t?nh', 'remote work']
        }
        
        scores = {context: 0 for context in context_keywords.keys()}
        
        for context, keywords in context_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[context] += 1
        
        if max(scores.values()) > 0:
            primary_context = max(scores.items(), key=lambda x: x[1])[0]
            return {
                'primary_context': primary_context,
                'secondary_context': None,
                'confidence_scores': scores
            }
        else:
            return {
                'primary_context': 'general_travel',
                'secondary_context': None,
                'confidence_scores': scores
            }
    
    def generate_context_specific_suggestions(self, user_context, hotels_df):
        """T?o ?? xu?t d?a trên ng? c?nh"""
        context_recommendations = {
            'heartbreak_recovery': {
                'priority_features': ['spa', 'sea_view', 'quiet', 'nature', 'view'],
                'avoid_features': ['party', 'noisy', 'family_heavy'],
                'message_tone': 'empathetic_healing',
                'hotel_types': ['resort', 'boutique', 'wellness']
            },
            'business_trip': {
                'priority_features': ['wifi', 'conference', 'city_center', 'business_center'],
                'avoid_features': ['remote', 'no_internet', 'party'],
                'message_tone': 'professional_practical', 
                'hotel_types': ['business', 'luxury', 'boutique']
            },
            'workation': {
                'priority_features': ['wifi', 'quiet', 'workspace', 'city_center'],
                'avoid_features': ['noisy', 'party', 'family_heavy'],
                'message_tone': 'productive_focused',
                'hotel_types': ['business', 'boutique', 'apartment']
            },
            'general_travel': {
                'priority_features': ['rating', 'value', 'location'],
                'avoid_features': [],
                'message_tone': 'friendly_helpful',
                'hotel_types': ['all']
            }
        }
        
        context_rules = context_recommendations.get(
            user_context['primary_context'], 
            context_recommendations['general_travel']
        )
        
        return context_rules