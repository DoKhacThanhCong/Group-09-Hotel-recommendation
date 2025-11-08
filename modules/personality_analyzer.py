# modules/personality_analyzer.py
import re
from collections import Counter

class PersonalityAnalyzer:
    def __init__(self):
        self.personality_traits = {
            'extroverted': ['party', 'social', 'people', 'friends', 'fun', 'giao l?u', 'sôi ??ng'],
            'introverted': ['quiet', 'alone', 'peaceful', 'reading', 'nature', 'yên t?nh', 'm?t mình'],
            'adventurous': ['adventure', 'explore', 'new', 'challenge', 'risk', 'khám phá', 'm?o hi?m'],
            'luxury_seeker': ['luxury', 'premium', 'exclusive', 'VIP', 'designer', 'sang tr?ng', 'cao c?p'],
            'budget_conscious': ['budget', 'save', 'cheap', 'affordable', 'value', 'ti?t ki?m', 'giá r?'],
            'wellness_focused': ['wellness', 'yoga', 'meditation', 'health', 'detox', 's?c kh?e', 'thi?n']
        }
    
    def analyze_personality_from_text(self, text):
        """Phân tích tính cách t? v?n b?n"""
        words = re.findall(r'\w+', text.lower())
        word_freq = Counter(words)
        
        trait_scores = {}
        for trait, keywords in self.personality_traits.items():
            score = sum(word_freq.get(keyword, 0) for keyword in keywords)
            trait_scores[trait] = score
        
        # Normalize scores
        total = sum(trait_scores.values())
        if total > 0:
            trait_scores = {k: v/total for k, v in trait_scores.items()}
        
        dominant_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        
        return {
            'dominant_traits': [trait for trait, score in dominant_traits if score > 0.1],
            'trait_scores': trait_scores,
            'personality_type': self._determine_personality_type(dominant_traits)
        }
    
    def _determine_personality_type(self, dominant_traits):
        """Xác ??nh lo?i tính cách t?ng quát"""
        if not dominant_traits:
            return 'Balanced Traveler'
            
        traits = [trait for trait, score in dominant_traits if score > 0.1]
        
        trait_combinations = {
            ('extroverted', 'adventurous'): 'Social Explorer',
            ('introverted', 'wellness_focused'): 'Mindful Traveler', 
            ('luxury_seeker', 'extroverted'): 'Premium Socialite',
            ('budget_conscious', 'adventurous'): 'Budget Adventurer',
            ('wellness_focused', 'introverted'): 'Wellness Seeker',
            ('extroverted',): 'Social Butterfly',
            ('introverted',): 'Quiet Explorer',
            ('adventurous',): 'Adventure Seeker'
        }
        
        traits_tuple = tuple(sorted(traits))
        return trait_combinations.get(traits_tuple, 'Balanced Traveler')