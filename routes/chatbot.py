from flask import render_template, request, jsonify
import pandas as pd
import re
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

# Hàm parse thông tin cải tiến cho yêu cầu hỗn hợp
def parse_flexible_budget(text):
    """Parse ngân sách linh hoạt từ câu hỏi hỗn hợp"""
    text_lower = text.lower()
    
    # Giá cụ thể
    if "dưới" in text_lower or "dưới" in text_lower:
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            return int(numbers[0])
    
    # Mức giá tổng quát
    if any(word in text_lower for word in ["rẻ", "giá thấp", "tiết kiệm", "bình dân"]):
        return 1000000
    elif any(word in text_lower for word in ["tầm trung", "vừa phải", "trung bình"]):
        return 3000000
    elif any(word in text_lower for word in ["cao cấp", "sang", "đắt"]):
        return 8000000
    
    # Parse số trực tiếp
    numbers = re.findall(r'\d+', text.replace(',', '').replace('.', ''))
    return int(numbers[0]) if numbers else None

def parse_flexible_stars(text):
    """Parse số sao linh hoạt từ câu hỏi hỗn hợp"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["bao nhiêu sao cũng được", "không quan trọng sao", "tùy", "sao cũng được"]):
        return 0
    
    # Tìm số sao cụ thể trong câu
    for i in range(5, 0, -1):
        if f"{i} sao" in text_lower or f"{i} sao" in text_lower.replace('*', ''):
            return i
    
    numbers = re.findall(r'[1-5]', text)
    return int(numbers[0]) if numbers else 0

def parse_city(text):
    """Parse thành phố từ câu hỏi hỗn hợp"""
    text_lower = text.lower()
    city_mapping = {
        "hanoi": "Hanoi", "hà nội": "Hanoi", "hn": "Hanoi", "thủ đô": "Hanoi",
        "da nang": "Da Nang", "đà nẵng": "Da Nang", "dn": "Da Nang",
        "ho chi minh": "Ho Chi Minh City", "sài gòn": "Ho Chi Minh City", 
        "saigon": "Ho Chi Minh City", "hcm": "Ho Chi Minh City", "tp hcm": "Ho Chi Minh City",
        "nha trang": "Nha Trang", "nt": "Nha Trang",
        "đà lạt": "Da Lat", "dalat": "Da Lat",
        "phú quốc": "Phu Quoc", "phu quoc": "Phu Quoc",
        "hội an": "Hoi An", "hoi an": "Hoi An",
        "vũng tàu": "Vung Tau", "vung tau": "Vung Tau",
        "quy nhơn": "Quy Nhon", "quy nhon": "Quy Nhon"
    }
    
    for keyword, city in city_mapping.items():
        if keyword in text_lower:
            return city
    return None

def extract_all_preferences_from_text(text):
    """Trích xuất TẤT CẢ thông tin từ câu hỏi hỗn hợp"""
    text_lower = text.lower()
    
    preferences = {
        'city': parse_city(text),
        'budget': parse_flexible_budget(text),
        'min_stars': parse_flexible_stars(text),
        'features': parse_features_from_text(text),
        'text_query': text
    }
    
    return preferences

def get_remaining_features(used_features):
    """Lấy danh sách tính năng CHƯA được đề cập để gợi ý"""
    all_features = {
        'pool': 'hồ bơi',
        'buffet': 'buffet sáng', 
        'gym': 'phòng gym',
        'spa': 'spa/massage',
        'sea': 'view biển',
        'view': 'view đẹp',
        'wifi': 'wifi tốt',
        'parking': 'bãi đỗ xe',
        'breakfast': 'bữa sáng',
        'restaurant': 'nhà hàng'
    }
    
    remaining = []
    for feature, vietnamese in all_features.items():
        if feature not in used_features:
            remaining.append(vietnamese)
    
    return remaining

def generate_hotel_recommendations(user_prefs, base_data):
    """Tạo danh sách khách sạn đề xuất với xử lý hỗn hợp"""
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
        return [], "Không tìm thấy khách sạn nào phù hợp với yêu cầu của bạn."

def create_hotel_response(hotels, explanation, used_features=None):
    """Tạo câu trả lời về khách sạn với gợi ý tiếp theo"""
    if not hotels:
        return "Xin lỗi, tôi không tìm thấy khách sạn nào phù hợp với yêu cầu của bạn.", []
    
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
    
    # Tạo câu hỏi tiếp theo với tính năng chưa dùng
    remaining_features = get_remaining_features(used_features or [])
    if remaining_features:
        follow_up = f"💬 **Du khách có muốn thêm yêu cầu gì không ạ?** (ví dụ: {', '.join(remaining_features[:4])}...)"
    else:
        follow_up = "💬 **Bạn có yêu cầu gì khác không ạ?**"
    
    response += follow_up
    return response, remaining_features

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
    used_features = session_data.get('used_features', [])
    
    # Xử lý theo stage
    if stage == 'greeting':
        return {
            'response': "Xin chào du khách! 👋 Tôi có thể giúp gì cho bạn ạ?",
            'stage': 'awaiting_request',
            'preferences': user_prefs,
            'used_features': used_features
        }
    
    elif stage == 'awaiting_request':
        # Phân tích yêu cầu HỖN HỢP
        extracted_info = extract_all_preferences_from_text(user_message)
        
        # Cập nhật used_features
        new_features = list(extracted_info.get('features', {}).keys())
        used_features.extend(new_features)
        used_features = list(set(used_features))  # Remove duplicates
        
        # Cập nhật preferences
        user_prefs.update(extracted_info)
        
        # Nếu có đủ thông tin để tìm kiếm (có thành phố hoặc đủ tiêu chí)
        if user_prefs.get('city') or (user_prefs.get('features') and len(user_prefs.get('features', {})) >= 2):
            # Tìm khách sạn ngay
            hotels, explanation = generate_hotel_recommendations(user_prefs, base_data)
            response_text, remaining_features = create_hotel_response(hotels, explanation, used_features)
            
            return {
                'response': response_text,
                'stage': 'follow_up',
                'preferences': user_prefs,
                'used_features': used_features,
                'hotels': hotels
            }
        else:
            # Hỏi thêm thông tin cơ bản
            if not user_prefs.get('city'):
                return {
                    'response': "Bạn muốn tìm khách sạn ở thành phố nào ạ? (Hà Nội, Đà Nẵng, Hồ Chí Minh, Nha Trang, Đà Lạt...)",
                    'stage': 'awaiting_city',
                    'preferences': user_prefs,
                    'used_features': used_features
                }
            else:
                # Đã có thành phố, hỏi thêm chi tiết
                return {
                    'response': f"Tuyệt vời! {user_prefs['city']} có nhiều lựa chọn hay. Bạn có yêu cầu gì cụ thể không ạ? (ví dụ: giá cả, số sao, hồ bơi, buffet sáng...)",
                    'stage': 'awaiting_details',
                    'preferences': user_prefs,
                    'used_features': used_features
                }
    
    elif stage == 'awaiting_city':
        city = parse_city(user_message)
        if city:
            user_prefs['city'] = city
            
            # Tìm khách sạn ngay với thành phố + bất kỳ thông tin nào đã có
            hotels, explanation = generate_hotel_recommendations(user_prefs, base_data)
            response_text, remaining_features = create_hotel_response(hotels, explanation, used_features)
            
            return {
                'response': response_text,
                'stage': 'follow_up',
                'preferences': user_prefs,
                'used_features': used_features,
                'hotels': hotels
            }
        else:
            return {
                'response': "Tôi chưa nhận diện được thành phố. Bạn vui lòng cho biết thành phố cụ thể nhé!",
                'stage': 'awaiting_city',
                'preferences': user_prefs,
                'used_features': used_features
            }
    
    elif stage == 'awaiting_details':
        # Phân tích thông tin chi tiết từ câu hỏi hỗn hợp
        extracted_info = extract_all_preferences_from_text(user_message)
        new_features = list(extracted_info.get('features', {}).keys())
        used_features.extend(new_features)
        used_features = list(set(used_features))
        
        user_prefs.update(extracted_info)
        
        # Tìm khách sạn ngay
        hotels, explanation = generate_hotel_recommendations(user_prefs, base_data)
        response_text, remaining_features = create_hotel_response(hotels, explanation, used_features)
        
        return {
            'response': response_text,
            'stage': 'follow_up',
            'preferences': user_prefs,
            'used_features': used_features,
            'hotels': hotels
        }
    
    elif stage == 'follow_up':
        # Xử lý câu hỏi tiếp theo
        if any(word in user_message.lower() for word in ['tìm lại', 'khác', 'reset', 'mới']):
            return {
                'response': "OK! Hãy cho tôi biết bạn muốn tìm khách sạn ở đâu?",
                'stage': 'awaiting_city',
                'preferences': {},
                'used_features': []
            }
        else:
            # Phân tích yêu cầu mới và cập nhật
            extracted_info = extract_all_preferences_from_text(user_message)
            new_features = list(extracted_info.get('features', {}).keys())
            used_features.extend(new_features)
            used_features = list(set(used_features))
            
            user_prefs.update(extracted_info)
            
            hotels, explanation = generate_hotel_recommendations(user_prefs, base_data)
            response_text, remaining_features = create_hotel_response(hotels, explanation, used_features)
            
            return {
                'response': response_text,
                'stage': 'follow_up',
                'preferences': user_prefs,
                'used_features': used_features,
                'hotels': hotels
            }
    
    # Mặc định
    return {
        'response': "Xin chào! Tôi có thể giúp bạn tìm khách sạn phù hợp. Bạn muốn tìm ở thành phố nào?",
        'stage': 'awaiting_city',
        'preferences': {},
        'used_features': []
    }
