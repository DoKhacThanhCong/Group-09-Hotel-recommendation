from flask import render_template, request, jsonify
import pandas as pd
import re
from modules.filter import filter_by_location, filter_by_budget
from modules.recommend import calculate_scores_and_explain

# Tải dữ liệu
def load_data():
    try:
        df = pd.read_csv("hotels.csv")
        return df
    except FileNotFoundError:
        return None

base_data = load_data()

# Hàm parse thông tin từ tin nhắn
def parse_budget(text):
    numbers = re.findall(r'\d+', text.replace(',', '').replace('.', ''))
    return int(numbers[0]) if numbers else None

def parse_city(text):
    text_lower = text.lower()
    city_mapping = {
        "hanoi": "Hanoi", "hà nội": "Hanoi",
        "da nang": "Da Nang", "đà nẵng": "Da Nang", 
        "ho chi minh": "Ho Chi Minh City", "sài gòn": "Ho Chi Minh City", "saigon": "Ho Chi Minh City",
        "nha trang": "Nha Trang", "đà lạt": "Da Lat", "phú quốc": "Phu Quoc"
    }
    for keyword, city in city_mapping.items():
        if keyword in text_lower:
            return city
    return None

def parse_stars(text):
    numbers = re.findall(r'[1-5]', text)
    return int(numbers[0]) if numbers else None

def parse_bool(text):
    return any(word in text.lower() for word in ["yes", "có", "ừ", "cần", "muốn"])

# Routes cho chatbot
def init_chatbot_routes(app):
    @app.route('/chatbot')
    def chatbot_page():
        return render_template('chatbot.html')
    
    @app.route('/api/chat', methods=['POST'])
    def chat_api():
        try:
            data = request.json
            user_message = data.get('message', '')
            session_data = data.get('session', {})
            
            # Logic xử lý hội thoại
            response_data = process_chat_message(user_message, session_data)
            
            return jsonify(response_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

def process_chat_message(user_message, session_data):
    stage = session_data.get('stage', 'awaiting_city')
    user_prefs = session_data.get('preferences', {})
    
    if stage == 'awaiting_city':
        city = parse_city(user_message)
        if city:
            user_prefs['location'] = city
            return {
                'response': f"Tuyệt vời! Ngân sách tối đa của bạn cho 1 đêm là bao nhiêu (ví dụ: 1000000)?",
                'stage': 'awaiting_budget',
                'preferences': user_prefs
            }
        else:
            return {
                'response': "Tôi chưa nhận diện được thành phố. Bạn vui lòng chọn: Hanoi, Da Nang, Ho Chi Minh City, Nha Trang...",
                'stage': 'awaiting_city',
                'preferences': user_prefs
            }
    
    elif stage == 'awaiting_budget':
        budget = parse_budget(user_message)
        if budget and budget > 0:
            user_prefs['budget'] = budget
            return {
                'response': f"OK, ngân sách {budget:,} VND. Bạn muốn khách sạn tối thiểu mấy sao (1-5)?",
                'stage': 'awaiting_stars', 
                'preferences': user_prefs
            }
        else:
            return {
                'response': "Vui lòng nhập một con số hợp lệ cho ngân sách (ví dụ: 1500000).",
                'stage': 'awaiting_budget',
                'preferences': user_prefs
            }
    
    elif stage == 'awaiting_stars':
        stars = parse_stars(user_message)
        if stars:
            user_prefs['min_stars'] = stars
            return {
                'response': f"Đã ghi nhận {stars} sao. Bạn có cần hồ bơi không (yes/no)?",
                'stage': 'awaiting_pool',
                'preferences': user_prefs
            }
        else:
            return {
                'response': "Vui lòng nhập số sao từ 1 đến 5.",
                'stage': 'awaiting_stars',
                'preferences': user_prefs
            }
    
    elif stage == 'awaiting_pool':
        user_prefs['pool'] = parse_bool(user_message)
        return {
            'response': "Bạn có cần buffet sáng không (yes/no)?",
            'stage': 'awaiting_buffet',
            'preferences': user_prefs
        }
    
    elif stage == 'awaiting_buffet':
        user_prefs['buffet'] = parse_bool(user_message)
        return {
            'response': "Cuối cùng, bạn có mô tả gì thêm không (ví dụ: 'thích yên tĩnh, gần biển')? Nếu không, cứ nói 'không' nhé.",
            'stage': 'awaiting_text', 
            'preferences': user_prefs
        }
    
    elif stage == 'awaiting_text':
        user_prefs['text'] = user_message if user_message.lower() not in ["không", "ko", "no"] else ""
        
        # Xử lý tìm kiếm khách sạn
        if base_data is not None:
            # Lọc dữ liệu
            filtered_data = filter_by_location(base_data, user_prefs.get("location"))
            filtered_data = filter_by_budget(filtered_data, user_prefs.get("budget"))
            
            # Gợi ý AI
            final_results, explanation = calculate_scores_and_explain(filtered_data, user_prefs)
            
            # Tạo response
            if final_results.empty:
                response_text = "Rất tiếc, không tìm thấy khách sạn nào phù hợp với tất cả tiêu chí của bạn."
            else:
                response_text = f"💡 **Giải thích AI:** {explanation}\n\n"
                response_text += "**TOP 3 GỢI Ý TỐT NHẤT:**\n\n"
                
                top_3 = final_results.head(3)
                for i, (_, row) in enumerate(top_3.iterrows(), 1):
                    response_text += f"**{i}. {row['name']}** ({row['stars']} ⭐)\n"
                    response_text += f"   - 💰 Giá: {row['price']:,} VND\n"
                    response_text += f"   - ⭐ Rating: {row['rating']}/5\n"
                    response_text += f"   - 🎯 Điểm AI: {row['recommend_score']:.2f}\n"
                    response_text += f"   - 📝 {row['review'][:100]}...\n\n"
            
            response_text += "Gõ 'tìm lại' để bắt đầu lượt tìm kiếm mới!"
            
            return {
                'response': response_text,
                'stage': 'done',
                'preferences': user_prefs,
                'hotels': top_3.to_dict('records') if not final_results.empty else []
            }
        else:
            return {
                'response': "Xin lỗi, có lỗi xảy ra khi tải dữ liệu khách sạn.",
                'stage': 'done',
                'preferences': user_prefs
            }
    
    elif stage == 'done':
        if 'tìm lại' in user_message.lower() or 'lại' in user_message.lower():
            return {
                'response': "OK, bắt đầu lại nhé! Bạn muốn tìm khách sạn ở thành phố nào?",
                'stage': 'awaiting_city',
                'preferences': {}
            }
        else:
            return {
                'response': "Gõ 'tìm lại' để bắt đầu một lượt tìm kiếm mới nhé!",
                'stage': 'done',
                'preferences': user_prefs
            }
    
    # Mặc định
    return {
        'response': "Xin chào! Tôi có thể giúp bạn tìm khách sạn phù hợp. Bạn muốn tìm ở thành phố nào?",
        'stage': 'awaiting_city',
        'preferences': {}
    }

