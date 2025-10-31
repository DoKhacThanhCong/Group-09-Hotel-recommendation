import pandas as pd

def calculate_scores_and_explain(df, all_prefs):
    """
    Hàm tính điểm, sắp xếp và giải thích 
    Trả về 2 giá trị: (dataframe_sorted, explanation_string)
    """
    print(f"[AI] Bắt đầu tính điểm. Sở thích: {all_prefs}")
    
    # Một danh sách để lưu lại các lý do giải thích
    explanation_log = ["Bắt đầu quá trình xếp hạng:"]
    
    # Tạo bản sao để tính toán
    df_scored = df.copy()
    
    # LỌC CỨNG (Hard Filter) ---
    min_stars = all_prefs.get('min_stars', 1)
    df_scored = df_scored[df_scored['stars'] >= min_stars].copy()
    explanation_log.append(f"Loại bỏ các khách sạn dưới {min_stars} sao.")
    
    if df_scored.empty:
        return df_scored, "Không tìm thấy khách sạn nào sau khi lọc theo số sao."

    # TÍNH ĐIỂM (Scoring Logic) ---
    # 
    df_scored['recommend_score'] = df_scored['rating'] * 2
    explanation_log.append("Tính điểm dựa trên 'rating' gốc.")

    # 1. Tính điểm sở thích 
    if all_prefs.get('pool', False):
        df_scored['recommend_score'] += df_scored['pool'].apply(lambda has_pool: 5 if has_pool else -5)
        explanation_log.append("Ưu tiên khách sạn có hồ bơi (Pool).")
    
    if all_prefs.get('buffet', False):
        df_scored['recommend_score'] += df_scored['buffet'].apply(lambda has_buffet: 3 if has_buffet else 0)
        explanation_log.append("Cộng điểm cho khách sạn có Buffet.")

    # 2. Tính điểm Text 
    user_text = all_prefs.get('text', '').lower()
    text_score = 0
    
    if 'biển' in user_text:
        text_score += df_scored['sea'].apply(lambda has_sea: 10 if has_sea else -3)
        explanation_log.append("Tìm kiếm từ khóa 'biển', ưu tiên khách sạn gần biển.")
    
    if 'yên tĩnh' in user_text:
        text_score += df_scored['review'].str.contains('yên tĩnh|thoải mái', case=False).apply(lambda x: 5 if x else 0)
        explanation_log.append("Tìm kiếm từ khóa 'yên tĩnh' trong đánh giá.")

    if 'dịch vụ' in user_text or 'thân thiện' in user_text:
         text_score += df_scored['review'].str.contains('dịch vụ|thân thiện', case=False).apply(lambda x: 4 if x else 0)
         explanation_log.append("Tìm kiếm từ khóa 'dịch vụ', 'thân thiện' trong đánh giá.")

    df_scored['recommend_score'] += text_score

    # SẮP XẾP (Sorting) ---
    # Sắp xếp theo yêu cầu mới
    final_results_sorted = df_scored.sort_values(by="recommend_score", ascending=False)
    explanation_log.append("Hoàn tất! Đã sắp xếp kết quả.")

    # TRẢ VỀ KẾT QUẢ ---
    final_explanation = " ".join(explanation_log)
    
    return final_results_sorted, final_explanation