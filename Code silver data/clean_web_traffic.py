# -*- coding: utf-8 -*-
"""
LÀM SẠCH DỮ LIỆU VÀ ĐỔ VÀO THỰC THỂ WEB_TRAFFIC (3NF)
Nguồn : web_traffic.csv (dữ liệu thô)
Đích  : web_traffic_3NF.csv
Khóa chính hợp phần: (date, traffic_source)
"""

import pandas as pd  # Thư viện xử lý bảng dữ liệu

# ============================================================
# BƯỚC 0: KHAI BÁO ĐƯỜNG DẪN VÀ DANH SÁCH CỘT
# ============================================================
FILE_VAO = "web_traffic.csv"        # File dữ liệu thô
FILE_RA = "web_traffic_3NF.csv"     # File kết quả sau khi làm sạch

cot_khoa = ["date", "traffic_source"]                            # Hai cột tạo nên khóa chính hợp phần
cot_dem = ["sessions", "unique_visitors", "page_views"]          # Các chỉ số đếm (kiểu int)
cot_so = cot_dem + ["bounce_rate", "avg_session_duration_sec"]   # Tất cả cột số cần điền Mean

# ============================================================
# BƯỚC 1: ĐỌC DỮ LIỆU THÔ
# ============================================================
# encoding="utf-8-sig": đọc đúng file và bỏ ký tự BOM ở đầu file (nếu có)
df = pd.read_csv(FILE_VAO, encoding="utf-8-sig")

print("=== BƯỚC 1: ĐỌC DỮ LIỆU ===")
print("Số dòng, số cột ban đầu:", df.shape)

# ============================================================
# BƯỚC 2: XÓA DÒNG NULL 100%
# ============================================================
so_dong_truoc = len(df)  # Lưu số dòng trước khi xóa để so sánh

# how="all": chỉ xóa dòng mà TẤT CẢ các cột đều trống
df = df.dropna(how="all")

print("\n=== BƯỚC 2: XÓA DÒNG NULL HOÀN TOÀN ===")
print("Số dòng đã xóa:", so_dong_truoc - len(df))

# ============================================================
# BƯỚC 3: CHUẨN HÓA HAI CỘT KHÓA CHÍNH
# ============================================================
# Phải chuẩn hóa khóa TRƯỚC khi lọc trùng, nếu không các dòng trùng sẽ không được nhận ra.
# File thô có nhiều dòng bị gắn thêm hậu tố lạ như "organic_search Variant 0001"
# hoặc thừa khoảng trắng, nên cùng một nguồn nhưng bị coi là nhiều giá trị khác nhau.

# 3a. Đánh dấu dòng nào có hậu tố "Variant" (đây là bản sao chép), dùng ở Bước 5 để ưu tiên giữ dòng gốc
df["la_ban_sao"] = df["traffic_source"].str.contains("Variant", na=False)
print("\n=== BƯỚC 3: CHUẨN HÓA KHÓA ===")
print("Số dòng có hậu tố Variant:", df["la_ban_sao"].sum())

# 3b. Làm sạch traffic_source
df["traffic_source"] = (
    df["traffic_source"]
    .str.strip()                                          # Cắt khoảng trắng thừa hai đầu
    .str.replace(r"\s+Variant\s+\d+$", "", regex=True)    # Xóa hậu tố " Variant 0001"
    .str.lower()                                          # Đưa về chữ thường cho đồng nhất
)

# 3c. Chuyển date về kiểu ngày theo định dạng YYYY-MM-DD
#     errors="coerce": ngày sai (ví dụ "2026-99-99", "not_a_date") sẽ thành NaT (rỗng) thay vì báo lỗi
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")

print("Các giá trị traffic_source sau khi chuẩn hóa:", sorted(df["traffic_source"].dropna().unique()))
print("Số dòng date không hợp lệ:", df["date"].isna().sum())

# ============================================================
# BƯỚC 4: KHÓA CHÍNH KHÔNG ĐƯỢC NULL
# ============================================================
# Không thể điền Mean cho cột khóa, và khóa rỗng thì không định danh được dòng -> xóa
so_dong_truoc = len(df)
df = df.dropna(subset=cot_khoa)

print("\n=== BƯỚC 4: XÓA DÒNG THIẾU KHÓA CHÍNH ===")
print("Số dòng đã xóa:", so_dong_truoc - len(df))

# ============================================================
# BƯỚC 5: LỌC TRÙNG THEO KHÓA CHÍNH HỢP PHẦN (date, traffic_source)
# ============================================================
so_dong_truoc = len(df)

# Sắp xếp để các dòng gốc (la_ban_sao = False) nằm trên các dòng bản sao (True)
# kind="stable": giữ nguyên thứ tự cũ của các dòng cùng giá trị
df = df.sort_values("la_ban_sao", kind="stable")

# subset=cot_khoa: xem hai dòng là trùng khi cùng (date, traffic_source)
# keep="first": giữ dòng đầu tiên, tức là dòng gốc, bỏ các bản sao
df = df.drop_duplicates(subset=cot_khoa, keep="first")

# Bỏ cột đánh dấu vì không thuộc thiết kế của bảng
df = df.drop(columns="la_ban_sao")

print("\n=== BƯỚC 5: LỌC TRÙNG KHÓA HỢP PHẦN ===")
print("Số dòng trùng đã xóa:", so_dong_truoc - len(df))
print("Số dòng còn lại:", len(df))

# ============================================================
# BƯỚC 6: XỬ LÝ CÁC CỘT SỐ (NULL VÀ GIÁ TRỊ SAI)
# ============================================================
# 6a. Ép các cột số về kiểu số.
#     Cột unique_visitors trong file thô có giá trị chữ như "unknown" nên phải ép kiểu;
#     errors="coerce": giá trị không phải số sẽ thành NaN (Null)
for cot in cot_so:
    df[cot] = pd.to_numeric(df[cot], errors="coerce")

# 6b. Chỉ số đếm không thể bằng 0 hoặc âm (ví dụ sessions = -100), coi là giá trị sai và đổi thành Null
for cot in cot_dem:
    df.loc[df[cot] <= 0, cot] = float("nan")

print("\n=== BƯỚC 6: XỬ LÝ CỘT SỐ ===")
print("Số Null mỗi cột trước khi điền Mean:")
print(df[cot_so].isna().sum())

# 6c. Điền giá trị Trung bình (Mean) vào ô Null
#     Tính Mean SAU khi đã lọc trùng để các dòng bản sao không làm lệch trung bình
for cot in cot_so:
    df[cot] = df[cot].fillna(df[cot].mean())

print("\nSố Null mỗi cột sau khi điền Mean:")
print(df[cot_so].isna().sum())

# 6d. Làm tròn và ép kiểu dữ liệu
for cot in cot_dem:
    df[cot] = df[cot].round().astype(int)                # Chỉ số đếm: số nguyên
df["bounce_rate"] = df["bounce_rate"].round(5)           # bounce_rate: số thập phân, giữ 5 chữ số như dữ liệu gốc
df["avg_session_duration_sec"] = df["avg_session_duration_sec"].round(1)  # Thời gian: 1 chữ số thập phân

# ============================================================
# BƯỚC 7: KIỂM TRA RÀNG BUỘC LOGIC
# ============================================================
print("\n=== BƯỚC 7: KIỂM TRA RÀNG BUỘC ===")

# 7a. Khóa chính hợp phần phải duy nhất: không có cặp (date, traffic_source) nào xuất hiện 2 lần
print("Khóa (date, traffic_source) duy nhất:", not df.duplicated(subset=cot_khoa).any())

# 7b. Số khách truy cập không được vượt quá số phiên
print("Số dòng unique_visitors > sessions:", (df["unique_visitors"] > df["sessions"]).sum())

# 7c. bounce_rate là tỷ lệ nên phải nằm trong khoảng 0 đến 1
print("Số dòng bounce_rate ngoài khoảng 0-1:", (~df["bounce_rate"].between(0, 1)).sum())

# ============================================================
# BƯỚC 8: SẮP XẾP CỘT THEO THIẾT KẾ VÀ XUẤT FILE
# ============================================================
thu_tu_cot = [
    "date",                      # PK (phần 1)
    "traffic_source",            # PK (phần 2)
    "sessions",
    "unique_visitors",
    "page_views",
    "bounce_rate",
    "avg_session_duration_sec",
]
web_traffic = df[thu_tu_cot].sort_values(cot_khoa).reset_index(drop=True)

# date_format="%Y-%m-%d": xuất ngày theo định dạng YYYY-MM-DD
# encoding="utf-8-sig": để Excel mở file không bị lỗi font
web_traffic.to_csv(FILE_RA, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")

print("\n=== BƯỚC 8: KẾT QUẢ ===")
print("Kích thước bảng WEB_TRAFFIC:", web_traffic.shape)
print(web_traffic.dtypes)
print("\n10 dòng đầu tiên (preview):")
print(web_traffic.head(10).to_string(index=False))
print(f"\nĐã xuất file: {FILE_RA}")
