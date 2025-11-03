from flask import render_template, request, jsonify
import pandas as pd
import re
import random
from modules.filter import filter_by_location, filter_by_budget, filter_combined, parse_features_from_text
from modules.recommend import calculate_scores_and_explain

# Tải dữ liệu
def load_data():
    try:
        df = pd.read_csv("hotels.csv")
        return df
    except FileNotFoundError:
        return None

base_data = load_data()

# Hàm parse thông tin cải tiến
def parse_flexible_budget(text):
    """Parse ngân sách linh hoạt hơn"""
    text_lower = text.lower()
    
    # Giá rẻ
    if any(word in text_lower for word in ["rẻ", "giá thấp", "tiết kiệm", "bình dân"]):
        return 1000000
    # Giá trung bình
    elif any(word in text_lower for word in ["tầm trung", "vừa phải", "trung bình"]):
        return 3000000
    # Giá cao
    elif any(word in text_lower for word in ["cao cấp", "sang", "đắt"]):
        return 8000000
    
    # Parse số
    numbers = re.findall(r'\d+', text.replace(',', '').replace('.', ''))
    return int(numbers[0]) if numbers else None

def parse_flexible_stars(text):
    """Parse số sao linh hoạt"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["bao nhiêu sao cũng được", "không quan trọng sao", "tùy"]):
        return 0
    elif "5 sao" in text_lower or "năm sao" in text_lower:
        return 5
    elif "4 sao" in text_lower or "bốn sao" in text_lower:
        return 4
    elif "3 sao" in text_lower or "ba sao" in text_lower:
        return 3
    elif "2 sao" in text_lower or "hai sao" in text_lower:
        return 2
    elif "1 sao" in text_lower or "một sao" in text_lower:
        return 1
    
    numbers = re.findall(r'[1-5]', text)
    return int(numbers[0]) if numbers else 0

def parse_city(text):
    """Parse thành phố cải tiến"""
    text_lower = text.lower()
    city_mapping = {
        "hanoi": "Hanoi", "hà nội": "Hanoi", "hn": "Hanoi",
        "da nang": "Da Nang", "đà nẵng": "Da Nang", "dn": "Da Nang",
        "ho chi minh": "Ho Chi Minh City", "sài gòn": "Ho Chi Minh City", 
        "saigon": "Ho Chi Minh City", "hcm": "Ho Chi Minh City", "tp hcm": "Ho Chi Minh City",
        "nha trang": "Nha Trang", "nt": "Nha Trang",
        "đà lạt": "Da Lat", "dalat": "Da Lat",
        "phú quốc": "Phu Quoc", "phu quoc": "Phu Quoc",
        "hội an": "Hoi An", "hoi an": "Hoi An",
        "vũng tàu": "Vung Tau", "vung tau": "Vung Tau"
    }
    
    for keyword, city in city_mapping.items():
        if keyword in text_lower:
            return city
    return None

def parse_features(text):
    """Parse các tính năng từ câu hỏi tự nhiên"""
    text_lower = text.lower()
    features = {}
    
    # Các tính năng khách sạn
    feature_keywords = {
        'pool': ['hồ bơi', 'bể bơi', 'pool', 'bơi lội'],
        'buffet': ['buffet', 'buffet sáng', 'ăn sáng', 'bữa sáng'],
        'gym': ['gym', 'phòng gym', 'thể hình', 'tập thể dục'],
        'spa': ['spa', 'massage', 'xông hơi'],
        'sea': ['biển', 'gần biển', 'view biển', 'bãi biển', 'biển đẹp'],
        'view': ['view', 'cảnh đẹp', 'tầm nhìn'],
        'wifi': ['wifi', 'internet'],
        'parking': ['bãi đỗ', 'đỗ xe', 'parking']
    }
    
    for feature, keywords in feature_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            features[feature] = True
    
    return features

def parse_complex_request(text):
    """Phân tích câu hỏi phức tạp và trích xuất thông tin"""
    text_lower = text.lower()
    extracted_info = {
        'city': parse_city(text),
        'budget': parse_flexible_budget(text),
        'min_stars': parse_flexible_stars(text),
        'features': parse_features(text),
        'text_query': text
    }
    
    return extracted_info

def generate_hotel_recommendations(user_prefs, base_data):
    """Tạo danh sách khách sạn đề xuất"""
    if base_data is None or base_data.empty:
        return [], "Xin lỗi, hiện không có dữ liệu khách sạn."
    
    # Lọc dữ liệu
    filtered_data = base_data.copy()
    
    # Lọc theo thành phố
    if user_prefs.get('city'):
        filtered_data = filter_by_location(filtered_data, user_prefs['city'])
    
    # Lọc theo ngân sách
    if user_prefs.get('budget'):
        filtered_data = filter_by_budget(filtered_data, user_prefs['budget'])
    
    # Lọc theo tính năng
    features = user_prefs.get('features', {})
    if features:
        filtered_data = filter_combined(filtered_data, user_prefs.get('min_stars', 0), features)
    
    # Tính điểm AI
    if not filtered_data.empty:
        final_results, explanation = calculate_scores_and_explain(filtered_data, user_prefs)
        top_hotels = final_results.head(3).to_dict('records')
        return top_hotels, explanation
    else:
        return [], "Không tìm thấy khách sạn phù hợp với yêu cầu của bạn."

def create_hotel_response(hotels, explanation):
    """Tạo câu trả lời về khách sạn"""
    if not hotels:
        return "Xin lỗi, tôi không tìm thấy khách sạn nào phù hợp với yêu cầu của bạn."
    
    response = f"💡 **Phân tích:** {explanation}\n\n"
    response += "🏨 **TOP KHÁCH SẠN PHÙ HỢP:**\n\n"
    
    for i, hotel in enumerate(hotels, 1):
        response += f"**{i}. {hotel['name']}** ({hotel['stars']} ⭐)\n"
        response += f"   - 💰 **Giá:** {hotel['price']:,} VND/đêm\n"
        response += f"   - ⭐ **Đánh giá:** {hotel['rating']}/5\n"
        
        # Thêm thông tin tính năng
        features = []
        if hotel.get('pool'): features.append("🏊 Hồ bơi")
        if hotel.get('buffet'): features.append("🍽️ Buffet sáng")
        if hotel.get('gym'): features.append("💪 Gym")
        if hotel.get('spa'): features.append("💆 Spa")
        if hotel.get('sea'): features.append("🌊 Gần biển")
        
        if features:
            response += f"   - 🎯 **Tiện ích:** {', '.join(features)}\n"
        
        response += f"   - 📝 **Mô tả:** {hotel.get('review', '')[:100]}...\n\n"
    
    response += "💬 **Bạn muốn tìm hiểu thêm về khách sạn nào không? Hoặc có yêu cầu gì khác?**"
    return response

# Routes cho chatbot
def init_chatbot_routes(app):
    @app.route('/chatbot')
    def chatbot_page():
        return render_template('chatbot.html')
    
    @app.route('/api/chat', methods=['POST'])
    def chat_api():
        try:
            data = request.json
            user_message = data.get('message', '').strip()
            session_data = data.get('session', {})
            
            # Logic xử lý hội thoại
            response_data = process_chat_message(user_message, session_data)
            
            return jsonify(response_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

def process_chat_message(user_message, session_data):
    stage = session_data.get('stage', 'greeting')
    user_prefs = session_data.get('preferences', {})
    
    # Xử lý theo stage
    if stage == 'greeting':
        return {
            'response': "Xin chào du khách! 👋 Tôi có thể giúp gì cho bạn ạ?",
            'stage': 'awaiting_request',
            'preferences': user_prefs
        }
    
    elif stage == 'awaiting_request':
        # Phân tích yêu cầu phức tạp
        extracted_info = parse_complex_request(user_message)
        
        # Cập nhật preferences
        user_prefs.update(extracted_info)
        
        # Nếu đã có đủ thông tin cơ bản
        if user_prefs.get('city'):
            # Tìm khách sạn ngay
            hotels, explanation = generate_hotel_recommendations(user_prefs, base_data)
            response_text = create_hotel_response(hotels, explanation)
            
            return {
                'response': response_text,
                'stage': 'follow_up',
                'preferences': user_prefs,
                'hotels': hotels
            }
        else:
            # Hỏi thêm thông tin
            return {
                'response': "Bạn muốn tìm khách sạn ở thành phố nào ạ? (Hà Nội, Đà Nẵng, Hồ Chí Minh, Nha Trang, Đà Lạt, Phú Quốc...)",
                'stage': 'awaiting_city',
                'preferences': user_prefs
            }
    
    elif stage == 'awaiting_city':
        city = parse_city(user_message)
        if city:
            user_prefs['city'] = city
            
            # Hỏi tất cả thông tin còn lại trong 1 câu
            return {
                'response': f"Tuyệt vời! {city} có nhiều lựa chọn hay. Bạn có yêu cầu gì thêm không ạ? (VD: ngân sách, số sao, view ngắm biển, hồ bơi, gym, spa, khu vui chơi trẻ em...)",
                'stage': 'awaiting_details',
                'preferences': user_prefs
            }
        else:
            return {
                'response': "Tôi chưa nhận diện được thành phố. Bạn vui lòng cho biết thành phố cụ thể nhé!",
                'stage': 'awaiting_city',
                'preferences': user_prefs
            }
    
    elif stage == 'awaiting_details':
        # Phân tích thông tin chi tiết
        extracted_info = parse_complex_request(user_message)
        user_prefs.update(extracted_info)
        
        # Tìm khách sạn
        hotels, explanation = generate_hotel_recommendations(user_prefs, base_data)
        response_text = create_hotel_response(hotels, explanation)
        
        return {
            'response': response_text,
            'stage': 'follow_up',
            'preferences': user_prefs,
            'hotels': hotels
        }
    
    elif stage == 'follow_up':
        # Xử lý câu hỏi tiếp theo
        if any(word in user_message.lower() for word in ['tìm lại', 'khác', 'reset']):
            return {
                'response': "OK! Hãy cho tôi biết bạn muốn tìm khách sạn ở đâu?",
                'stage': 'awaiting_city',
                'preferences': {}
            }
        else:
            # Phân tích yêu cầu mới
            extracted_info = parse_complex_request(user_message)
            user_prefs.update(extracted_info)
            
            hotels, explanation = generate_hotel_recommendations(user_prefs, base_data)
            response_text = create_hotel_response(hotels, explanation)
            
            return {
                'response': response_text,
                'stage': 'follow_up',
                'preferences': user_prefs,
                'hotels': hotels
            }
    
    # Mặc định
    return {
        'response': "Xin chào! Tôi có thể giúp bạn tìm khách sạn phù hợp. Bạn muốn tìm ở thành phố nào?",
        'stage': 'awaiting_city',
        'preferences': {}
    }
