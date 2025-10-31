import pandas as pd

def filter_by_location(df, location_city):
    """
    Lọc DataFrame dựa trên thành phố 
    """
    if not location_city: 
        return df
    filtered_df = df[df['city'].str.lower() == location_city.lower()]
    return filtered_df

def filter_by_budget(df, max_price):
    """
    Lọc DataFrame dựa trên ngân sách tối đa 
    Chỉ giữ lại các khách sạn có giá <= max_price.
    """
    if max_price <= 0: 
        return df
    filtered_df = df[df['price'] <= max_price]
    return filtered_df

def filter_combined(df, min_stars, preferences):
    """
    Hàm lọc phức tạp, kết hợp nhiều tiêu chí.
    - Lọc theo số sao tối thiểu 
    - Lọc theo các sở thích : 'pool', 'buffet'
    """
    print(f"[Filter] Đang lọc với {min_stars} sao và sở thích {preferences}...")
    
   
    filtered_df = df.copy()
    
   
    if min_stars > 0:
        filtered_df = filtered_df[filtered_df['stars'] >= min_stars]

    for key, value in preferences.items():
        if value: 
            if key in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[key] == True]
            else:
                print(f"Cảnh báo: Không tìm thấy cột '{key}' để lọc.")
                
    return filtered_df
