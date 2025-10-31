import streamlit as st
import pandas as pd
from filter import filter_by_location, filter_by_budget
from recommend import calculate_scores_and_explain 

# Thiết lập giao diện Web 
st.set_page_config(layout="wide")
st.title("🤖 Hệ thống Gợi ý Du lịch Thông minh 🏨")
st.write("Mô phỏng dự án - Tích hợp Lọc (TV3) và AI (TV4)")

# Tải dữ liệu 
@st.cache_data
def load_data(csv_path):
    try:
        df = pd.read_csv(csv_path)
        return df
    except FileNotFoundError:
        st.error(f"LỖI: Không tìm thấy file {csv_path}. Hãy đảm bảo file này ở cùng thư mục.")
        return None

base_data = load_data("hotels.csv")

if base_data is not None:

    # Giao diện Form (Sidebar) 
    st.sidebar.header("Bộ lọc của bạn")
    
    USER_LOCATION = st.sidebar.text_input("Bạn muốn tìm khách sạn ở thành phố nào?", "Hanoi")
    
    USER_BUDGET = st.sidebar.slider("Ngân sách tối đa của bạn (VND)?", 
                                     min_value=0, 
                                     max_value=10000000, 
                                     value=2000000, 
                                     step=100000)
    
    USER_MIN_STARS = st.sidebar.number_input("Bạn muốn khách sạn tối thiểu mấy sao?", 1, 5, 3)
    
    st.sidebar.subheader("Sở thích đặc biệt (phần AI):")
    USER_POOL = st.sidebar.checkbox("Có hồ bơi (Pool)")
    USER_BUFFET = st.sidebar.checkbox("Có buffet sáng")
    USER_TEXT = st.sidebar.text_area("Hãy mô tả thêm...", "Tôi thích nơi yên tĩnh, dịch vụ tốt")

    # Xử lý khi người dùng bấm nút
    if st.sidebar.button("🔍 Tìm kiếm Khách sạn"):
        
        
        print("--- Đang xử lý yêu cầu trên Web ---")
        filtered_data = filter_by_location(base_data, USER_LOCATION)
        filtered_data = filter_by_budget(filtered_data, USER_BUDGET)
        
        st.write(f"Tìm thấy **{len(filtered_data)}** khách sạn phù hợp với Vị trí và Ngân sách.")

        
        all_user_preferences = {
            'min_stars': USER_MIN_STARS,
            'pool': USER_POOL,
            'buffet': USER_BUFFET,
            'text': USER_TEXT
        }

        final_results_sorted, explanation = calculate_scores_and_explain(
            filtered_data.copy(), 
            all_user_preferences
        )

        #Hiển thị kết quả ---
        
        # Hiển thị giải thích của AI 
        st.info(f"AI giải thích: {explanation}")

        st.subheader("TOP 3 GỢI Ý PHÙ HỢP NHẤT ")
        
        if final_results_sorted.empty:
            st.warning("Rất tiếc, không tìm thấy khách sạn nào phù hợp với tất cả tiêu chí.")
        else:
            top_3 = final_results_sorted.head(3)
            
            for index, row in top_3.iterrows():
                st.markdown(f"### {row['name']} ({row['stars']} sao)")
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(row['image_url'], caption=f"{row['name']}")
                with col2:
                    st.markdown(f"**Giá:** `{row['price']:,} VND`")
                    st.markdown(f"**Rating:** `{row['rating']}/5`")
                    st.markdown(f"**Điểm gợi ý (AI):** `{row['recommend_score']:.2f}`")
                    st.markdown(f"**Đánh giá:** *{row['review']}*")
                st.divider()