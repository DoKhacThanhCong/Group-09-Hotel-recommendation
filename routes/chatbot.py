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

def parse_flexible_budget(text):
    """Parse ngân sách linh hoạt từ câu hỏi hỗn hợp"""
    text_lower = text.lower()
    
    # Tìm số tiền sau từ "dưới", "dưới", "khoảng", "tầm"
    budget_patterns = [
        r'dưới\s*(\d+\s*[kK]?\s*[đd]?[ồô]ng?)',
        r'dưới\s*(\d+\s*[kK]?\s*[đd]?[ồô]ng?)', 
        r'khoảng\s*(\d+\s*[kK]?\s*[đd]?[ồô]ng?)',
        r'tầm\s*(\d+\s*[kK]?\s*[đd]?[ồô]ng?)',
        r'giá\s*(\d+\s*[kK]?\s*[đd]?[ồô]ng?)',
        r'(\d+\s*[kK]?\s*[tr]?[iệI]?[uu]?[ee]?[uu]?)\s*[đd]?[ồô]?ng?'
    ]
    
    for pattern in budget_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            number_str = matches[0].replace('k', '000').replace('K', '000').replace('tr', '000000').replace('triệu', '000000')
            numbers = re.findall(r'\d+', number_str)
            if numbers:
                budget = int(numbers[0])
                # Xử lý đơn vị
                if 'triệu' in matches[0] or 'tr' in matches[0]:
                    return budget * 1000000
                elif 'k' in matches[0] or 'K' in matches[0]:
                    return budget * 1000
                else:
                    # Nếu số lớn hơn 1000, coi như VND, nhỏ hơn coi như triệu
                    return budget * 1000000 if budget < 1000 else budget
    
    # Mức giá tổng quát
    if any(word in text_lower for word in ["rẻ", "giá thấp", "tiết kiệm", "bình dân"]):
        return 1000000
    elif any(word in text_lower for word in ["tầm trung", "vừa phải", "trung bình"]):
        return 3000000
    elif any(word in text_lower for word in ["cao cấp", "sang", "đắt"]):
        return 8000000
    
    return None

def parse_flexible_stars(text):
    """Parse số sao linh hoạt từ câu hỏi hỗn hợp"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["bao nhiêu sao cũng được", "không quan trọng sao", "tùy", "sao cũng được"]):
        return 0
    
    # Tìm số sao cụ thể trong câu
    for i in range(5, 0, -1):
        if f"{i} sao" in text_lower or f"{i}-sao" in text_lower or f"{i} sao" in text_lower.replace('*', ''):
            return i
    
    numbers = re.findall(r'[1-5]', text)
    return int(numbers[0]) if numbers else 0

def parse_city(text):
    """Parse thành phố từ câu hỏi hỗn hợp"""
    text_lower = text.lower()
    city_mapping = {
        "hanoi": "Hanoi", "hà nội": "Hanoi", "hn": "Hanoi", "thủ đô": "Hanoi", "ha noi": "Hanoi",
        "da nang": "Da Nang", "đà nẵng": "Da Nang", "dn": "Da Nang", "da nang": "Da Nang",
        "ho chi minh": "Ho Chi Minh City", "sài gòn": "Ho Chi Minh City", 
        "saigon": "Ho Chi Minh City", "hcm": "Ho Chi Minh City", "tp hcm": "Ho Chi Minh City", "tphcm": "Ho Chi Minh City",
        "nha trang": "Nha Trang", "nt": "Nha Trang", "nha trang": "Nha Trang",
        "đà lạt": "Da Lat", "dalat": "Da Lat", "da lat": "Da Lat",
        "phú quốc": "Phu Quoc", "phu quoc": "Phu Quoc",
        "hội an": "Hoi An", "hoi an": "Hoi An",
        "vũng tàu": "Vung Tau", "vung tau": "Vung Tau",
        "quy nhơn": "Quy Nhon", "quy nhon": "Quy Nhon", "quy nhon": "Quy Nhon"
    }
    
    for keyword, city in city_mapping.items():
        if keyword in text_lower:
            return city
    return None

def extract_all_preferences_from_text(text):
    """Trích xuất TẤT CẢ thông tin từ câu hỏi hỗn hợp - CẢI TIẾN"""
    text_lower = text.lower()
    
    # Kiểm tra xem có phải là yêu cầu tìm khách sạn không
    hotel_keywords = ['khách sạn', 'hotel', 'ks', 'đặt phòng', 'tìm', 'tìm kiếm']
    is_hotel_request = any(keyword in text_lower for keyword in hotel_keywords) or any([
        parse_city(text), parse_flexible_budget(text), parse_flexible_stars(text), parse_features_from_text(text)
    ])
    
    if not is_hotel_request:
        return None
    
    preferences = {
        'city': parse_city(text),
        'budget': parse_flexible_budget(text),
        'min_stars': parse_flexible_stars(text),
        'features': parse_features_from_text(text),
        'text_query': text
    }
    
    return preferences

def has_sufficient_info(preferences):
    """Kiểm tra có đủ thông tin để tìm khách sạn không"""
    if not preferences:
        return False
        
    # Chỉ cần 1 trong các tiêu chí là đủ
    criteria_count = 0
    if preferences.get('city'):
        criteria_count += 1
    if preferences.get('budget'):
        criteria_count += 1  
    if preferences.get('min_stars', 0) > 0:
        criteria_count += 1
    if preferences.get('features'):
        criteria_count += len(preferences['features'])
    
    return criteria_count >= 1  # Chỉ cần 1 tiêu chí là đủ

def generate_hotel_recommendations(user_prefs, base_data):
    """Tạo danh sách khách sạn đề xuất - SỬA ĐỂ TRẢ VỀ 3 KHÁCH SẠN"""
    if base_data is None or base_data.empty:
        return [], "Không có dữ liệu khách sạn."

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
    
    # Tính điểm AI và lấy top 3 - QUAN TRỌNG: ĐẢM BẢO LẤY 3 KHÁCH SẠN
    if not filtered_data.empty:
        final_results, explanation = calculate_scores_and_explain(filtered_data, user_prefs)
        
        # Lấy số lượng khách sạn tối đa có thể (tối đa 3)
        num_hotels = min(3, len(final_results))
        top_hotels = final_results.head(num_hotels).to_dict('records')
        
        return top_hotels, explanation
    else:
        return [], "Không tìm thấy khách sạn phù hợp."

def create_simple_hotel_response(hotels, explanation):
    """Tạo câu trả lời đơn giản với khung khách sạn - KHÔNG mô tả, KHÔNG điểm AI"""
    if not hotels:
        return "Xin lỗi, không tìm thấy khách sạn nào phù hợp với yêu cầu của bạn.", False
    
    response = "**Tôi đã tìm thấy các khách sạn phù hợp cho du khách ạ**\n\n"
    
    for i, hotel in enumerate(hotels, 1):
        response += f"**{hotel['name']}**\n"
        response += f"⭐ {hotel['stars']} sao | 💰 {hotel['price']:,} VND/đêm\n"
        response += f"📍 {hotel['city']} | ⭐ {hotel['rating']}/5\n"
        
        # Thêm biểu tượng tính năng ngắn gọn
        features = []
        if hotel.get('pool'): features.append("🏊 Hồ bơi")
        if hotel.get('buffet'): features.append("🍽️ Buffet sáng") 
        if hotel.get('gym'): features.append("💪 Gym")
        if hotel.get('spa'): features.append("💆 Spa")
        if hotel.get('sea'): features.append("🌊 View biển")
        if hotel.get('view'): features.append("🏞️ View đẹp")
        
        if features:
            response += f"🎯 {', '.join(features)}\n"
        
        # THÊM NÚT XEM CHI TIẾT (Modal)
        response += f"🔍 [Xem chi tiết {hotel['name']}](/hotel/{hotel['name'].replace(' ', '%20')})\n"
        
        if i < len(hotels):  # Không thêm dấu cách sau khách sạn cuối
            response += "\n" + "─" * 50 + "\n\n"
    
    response += "**Du khách có muốn tìm kiếm với tiêu chí khác không ạ?**"
    return response, True

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
    
    # Kiểm tra nếu người dùng nói "không" hoặc từ tương tự
    user_message_lower = user_message.lower()
    negative_keywords = ['không', 'ko', 'thôi', 'khong', 'k cần', 'không cần', 'đủ rồi', 'enough', 'no']
    
    if any(keyword in user_message_lower for keyword in negative_keywords) and stage == 'follow_up':
        return {
            'response': "Cảm ơn du khách đã sử dụng dịch vụ của chúng tôi! 😊✨\nNếu có nhu cầu đặt phòng hoặc tư vấn thêm, hãy quay lại nhé!",
            'stage': 'end',
            'preferences': {},
            'hotels': [],
            'has_results': False
        }
    
    # LUÔN cố gắng phân tích yêu cầu hỗn hợp trước
    extracted_info = extract_all_preferences_from_text(user_message)
    
    # Nếu phân tích được thông tin từ yêu cầu hỗn hợp
    if extracted_info and has_sufficient_info(extracted_info):
        # Tìm khách sạn ngay lập tức
        hotels, explanation = generate_hotel_recommendations(extracted_info, base_data)
        response_text, has_results = create_simple_hotel_response(hotels, explanation)
        
        return {
            'response': response_text,
            'stage': 'follow_up',
            'preferences': extracted_info,
            'hotels': hotels,
            'currentHotels': hotels,  # THÊM DÒNG NÀY
            'has_results': has_results
        }
    
    # Nếu không phân tích được, xử lý theo stage thông thường
    user_prefs = session_data.get('preferences', {})
    
    if stage == 'greeting':
        return {
            'response': "Xin chào du khách! 👋 Hãy cho tôi biết bạn muốn tìm khách sạn như thế nào? (ví dụ: 'Khách sạn ở Đà Nẵng có hồ bơi', 'Phòng giá rẻ ở Hà Nội', 'Khách sạn 5 sao có buffet')",
            'stage': 'awaiting_request', 
            'preferences': user_prefs
        }
    
    elif stage == 'awaiting_request':
        # Nếu đến đây mà không phân tích được, hỏi rõ hơn
        return {
            'response': "Bạn có thể nói rõ hơn về yêu cầu được không? Ví dụ:\n• 'Khách sạn ở Hà Nội có hồ bơi'\n• 'Phòng giá dưới 2 triệu' \n• 'Khách sạn 4 sao ở Đà Nẵng'",
            'stage': 'awaiting_request',
            'preferences': user_prefs
        }
    
    elif stage == 'follow_up':
        # Xử lý yêu cầu mới sau khi đã có kết quả
        if any(word in user_message_lower for word in ['tìm lại', 'khác', 'reset', 'mới']):
            return {
                'response': "OK! Hãy cho tôi biết bạn muốn tìm khách sạn như thế nào?",
                'stage': 'awaiting_request',
                'preferences': {}
            }
        else:
            # Thử phân tích yêu cầu mới
            new_extracted_info = extract_all_preferences_from_text(user_message)
            if new_extracted_info and has_sufficient_info(new_extracted_info):
                hotels, explanation = generate_hotel_recommendations(new_extracted_info, base_data)
                response_text, has_results = create_simple_hotel_response(hotels, explanation)
                
                return {
                    'response': response_text,
                    'stage': 'follow_up',
                    'preferences': new_extracted_info,
                    'hotels': hotels,
                    'currentHotels': hotels,  # THÊM DÒNG NÀY
                    'has_results': has_results
                }
            else:
                return {
                    'response': "Bạn muốn tìm kiếm với tiêu chí gì khác? (ví dụ: thêm hồ bơi, đổi thành phố, giá cả khác...)",
                    'stage': 'follow_up',
                    'preferences': user_prefs
                }
    
    # Mặc định
    return {
        'response': "Hãy cho tôi biết bạn muốn tìm khách sạn như thế nào? (ví dụ: 'Khách sạn ở Đà Nẵng', 'Phòng có hồ bơi', 'Giá dưới 3 triệu')",
        'stage': 'awaiting_request',
        'preferences': {}
    }
