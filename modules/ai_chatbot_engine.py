# modules/ai_chatbot_engine.py
from datetime import datetime

class AIChatbotEngine:
    def __init__(self):
        from modules.advanced_sentiment import AdvancedSentimentAnalyzer
        from modules.context_aware_recommender import ContextAwareRecommender
        from modules.personality_analyzer import PersonalityAnalyzer
        
        self.sentiment_analyzer = AdvancedSentimentAnalyzer()
        self.context_recommender = ContextAwareRecommender()
        self.personality_analyzer = PersonalityAnalyzer()
        self.conversation_memory = {}
    
    def process_user_message(self, user_id, message, conversation_history=None):
        """X? lý tin nh?n v?i AI nâng cao"""
        # Phân tích ?a chi?u
        sentiment_analysis = self.sentiment_analyzer.analyze_user_state(message)
        context_prediction = self.context_recommender.predict_travel_context(message)
        personality_profile = self.personality_analyzer.analyze_personality_from_text(message)
        
        # T?ng h?p insights
        user_insights = {
            'sentiment': sentiment_analysis,
            'context': context_prediction,
            'personality': personality_profile,
            'timestamp': datetime.now(),
            'special_scenario': sentiment_analysis.get('special_scenario')
        }
        
        # L?u vào memory
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        self.conversation_memory[user_id].append(user_insights)
        
        # T?o ph?n h?i thông minh
        response = self._generate_ai_response(user_insights, message)
        
        return {
            'response': response,
            'insights': user_insights,
            'recommendation_strategy': self._get_recommendation_strategy(user_insights)
        }
    
    def _generate_ai_response(self, insights, original_message):
        """T?o ph?n h?i AI thông minh"""
        sentiment = insights['sentiment']['sentiment']
        emotion = insights['sentiment']['emotion']
        primary_context = insights['context']['primary_context']
        
        # Emotional response mapping
        emotional_responses = {
            'sadness': "Mình th?y b?n ?ang có chút bu?n. ?ôi khi m?t chuy?n ?i nh? có th? giúp tâm tr?ng t?t h?n ??y ??",
            'joy': "Tuy?t v?i! Ni?m vui c?a b?n làm mình c?ng th?y ph?n khích ??",
            'anger': "Mình hi?u c?m giác b?c b?i này. M?t không gian yên t?nh có th? giúp b?n l?y l?i cân b?ng ??",
            'fear': "??ng lo l?ng quá, mình s? giúp b?n tìm m?t n?i th?t an toàn và tho?i mái ???",
            'surprise': "Ôi thú v? quá! ?? Chuy?n ?i b?t ng? th??ng mang l?i nhi?u tr?i nghi?m ?áng nh?!",
            'disgust': "Mình hi?u c?m giác khó ch?u ?ó ?? M?t không gian trong lành s? giúp b?n refresh tinh th?n!",
            'neutral': "R?t vui ???c h? tr? b?n! ??"
        }
        
        # Context-based recommendations
        context_suggestions = {
            'heartbreak_recovery': "Mình g?i ý nh?ng n?i có không gian healing, view ??p giúp tâm h?n nh? nhàng h?n ??",
            'business_trip': "Cho chuy?n công tác, quan tr?ng là ti?n nghi và v? trí thu?n l?i ??",
            'solo_adventure': "?i m?t mình th?t t? do! B?n s? có không gian riêng và nh?ng tr?i nghi?m m?i ??",
            'workation': "Perfect cho workation! Mình s? tìm n?i có wifi t?t và không gian làm vi?c tho?i mái ??"
        }
        
        # Build intelligent response
        response_parts = []
        
        # Emotional empathy
        if emotion in emotional_responses:
            response_parts.append(emotional_responses[emotion])
        
        # Context understanding
        if primary_context in context_suggestions:
            response_parts.append(context_suggestions[primary_context])
        
        # Personality-based suggestion
        personality_type = insights['personality']['personality_type']
        response_parts.append(f"V?i phong cách {personality_type}, mình ngh? b?n s? thích:")
        
        # Add specific recommendations based on AI analysis
        response_parts.extend(self._get_personalized_suggestions(insights))
        
        return "\n\n".join(response_parts)
    
    def _get_personalized_suggestions(self, insights):
        """?? xu?t cá nhân hóa d?a trên phân tích AI"""
        suggestions = []
        
        # D?a trên sentiment
        if insights['sentiment']['emotion'] in ['sadness', 'fear']:
            suggestions.append("• N?i yên t?nh, view thiên nhiên giúp th? giãn")
            suggestions.append("• Khách s?n có spa và d?ch v? wellness")
        
        # D?a trên personality
        personality = insights['personality']['dominant_traits']
        if 'extroverted' in personality:
            suggestions.append("• Khu v?c có ho?t ??ng social và giao l?u")
        if 'introverted' in personality:
            suggestions.append("• Không gian riêng t?, ít ?ông ?úc")
        if 'wellness_focused' in personality:
            suggestions.append("• D?ch v? yoga, thi?n và ch?m sóc s?c kh?e")
        
        return suggestions if suggestions else ["• Khách s?n có rating cao và d?ch v? t?t"]
    
    def _get_recommendation_strategy(self, insights):
        """Xác ??nh chi?n l??c ?? xu?t"""
        context = insights['context']['primary_context']
        emotion = insights['sentiment']['emotion']
        
        strategies = {
            'heartbreak_recovery': 'healing_focus',
            'business_trip': 'practical_focus', 
            'workation': 'productivity_focus',
            'solo_adventure': 'experience_focus'
        }
        
        return strategies.get(context, 'balanced_focus')