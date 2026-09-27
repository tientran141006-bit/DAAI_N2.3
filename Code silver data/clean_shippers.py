# -*- coding: utf-8 -*-
"""
TRÍCH XUẤT VÀ LÀM SẠCH DỮ LIỆU VÀO THỰC THỂ SHIPPERS (3NF)
Nguồn : shipments_realistic.csv (bảng giao hàng, mỗi dòng là 1 lượt giao)
Đích  : shippers_3NF.csv     (bảng SHIPPERS, mỗi shipper 1 dòng)
        locations_lookup.csv (bảng tra cứu khu vực cho khóa ngoại location_id)
"""

import pandas as pd  # Thư viện xử lý bảng dữ liệu

# ============================================================
# BƯỚC 0: KHAI BÁO ĐƯỜNG DẪN VÀ DANH SÁCH CỘT
# ============================================================
FILE_VAO = "shipments_realistic.csv"        # File dữ liệu thô
FILE_SHIPPERS = "shippers_3NF.csv"          # File kết quả bảng SHIPPERS
FILE_LOCATIONS = "locations_lookup.csv"     # File bảng khu vực (đích của khóa ngoại)

# Chỉ lấy các cột thuộc về shipper (bỏ order_id, ship_date, shipping_fee... vì đó là dữ liệu của từng lượt giao)
cot_shipper = [
    "shipper_id", "shipper_name", "shipper_phone", "shipper_company",
    "shipper_gender", "shipper_age", "shipper_education",
    "shipper_experience_years", "shipper_marital_status", "shipper_vehicle",
    "join_date", "shipper_rating", "working_shift",
]
cot_khu_vuc = ["region", "city", "district"]   # Các cột mô tả khu vực của shipper

# ============================================================
# BƯỚC 1: ĐỌC DỮ LIỆU THÔ
# ============================================================
# usecols: chỉ đọc các cột cần dùng cho nhẹ bộ nhớ (file có hơn 566.000 dòng)
# dtype={"shipper_phone": str}: đọc số điện thoại dạng chuỗi để không bị mất/đổi định dạng
# encoding="utf-8-sig": đọc đúng tiếng Việt và bỏ ký tự BOM ở đầu file (nếu có)
df = pd.read_csv(
    FILE_VAO,
    usecols=cot_shipper + cot_khu_vuc,
    dtype={"shipper_phone": str},
    encoding="utf-8-sig",
)

print("=== BƯỚC 1: ĐỌC DỮ LIỆU ===")
print("Số dòng, số cột của file thô:", df.shape)

# ============================================================
# BƯỚC 2: XÓA DÒNG NULL 100%
# ============================================================
so_dong_truoc = len(df)

# how="all": chỉ xóa dòng mà TẤT CẢ các cột đều trống
df = df.dropna(how="all")

print("\n=== BƯỚC 2: XÓA DÒNG NULL HOÀN TOÀN ===")
print("Số dòng đã xóa:", so_dong_truoc - len(df))

# ============================================================
# BƯỚC 3: KHÓA CHÍNH KHÔNG ĐƯỢC NULL
# ============================================================
# Dòng nào thiếu shipper_id thì không biết thuộc shipper nào -> xóa
so_dong_truoc = len(df)
df = df.dropna(subset=["shipper_id"])

print("\n=== BƯỚC 3: KIỂM TRA KHÓA CHÍNH ===")
print("Số dòng thiếu shipper_id đã xóa:", so_dong_truoc - len(df))

# ============================================================
# BƯỚC 4: TRÍCH XUẤT DANH SÁCH SHIPPER (SELECT DISTINCT)
# ============================================================
# Tương đương SQL: SELECT DISTINCT <các cột của shipper> FROM shipments
# Nhiều dòng giao hàng của cùng 1 shipper có thông tin giống hệt nhau nên sẽ gộp thành 1 dòng
shippers = df[cot_shipper + cot_khu_vuc].drop_duplicates()

print("\n=== BƯỚC 4: TRÍCH XUẤT SHIPPER ===")
print("Số dòng sau SELECT DISTINCT:", len(shippers))
print("Số shipper_id khác nhau:", shippers["shipper_id"].nunique())

# Kiểm tra: nếu 1 shipper_id vẫn xuất hiện nhiều dòng nghĩa là thông tin của
# shipper đó bị mâu thuẫn giữa các lượt giao (ví dụ 2 số điện thoại khác nhau)
print("Mỗi shipper_id chỉ có 1 bộ thông tin (không mâu thuẫn):", shippers["shipper_id"].is_unique)

# Đảm bảo khóa chính duy nhất: nếu có mâu thuẫn thì giữ dòng xuất hiện đầu tiên
shippers = shippers.drop_duplicates(subset="shipper_id", keep="first")

# ============================================================
# BƯỚC 5: XỬ LÝ NULL MỘT PHẦN
# ============================================================
# Làm bước này SAU khi đã lọc shipper duy nhất để mỗi shipper được tính 1 lần,
# không bị lệch bởi việc shipper nào giao nhiều đơn hơn
print("\n=== BƯỚC 5: XỬ LÝ NULL MỘT PHẦN ===")
print("Số Null mỗi cột trước khi xử lý:")
print(shippers.isna().sum())

# 5a. Cột SỐ: điền giá trị Trung bình (Mean) vào chỗ Null
cot_so = ["shipper_age", "shipper_experience_years", "shipper_rating"]
for cot in cot_so:
    shippers[cot] = pd.to_numeric(shippers[cot], errors="coerce")   # Ép về số, giá trị lỗi thành Null
    shippers[cot] = shippers[cot].fillna(shippers[cot].mean())      # Điền trung bình của cột

# 5b. Cột CHỮ: điền 'N/A' cho ô Null (bạn có thể bỏ đoạn này nếu muốn giữ NULL)
cot_chu = [
    "shipper_name", "shipper_phone", "shipper_company", "shipper_gender",
    "shipper_education", "shipper_marital_status", "shipper_vehicle",
    "working_shift",
] + cot_khu_vuc
for cot in cot_chu:
    shippers[cot] = shippers[cot].fillna("N/A")

print("\nSố Null mỗi cột sau khi xử lý:")
print(shippers.isna().sum())

# ============================================================
# BƯỚC 6: ÉP KIỂU DỮ LIỆU CHO ĐÚNG VỚI THIẾT KẾ
# ============================================================
# 6a. Tuổi và số năm kinh nghiệm: làm tròn rồi ép về số nguyên (int)
shippers["shipper_age"] = shippers["shipper_age"].round().astype(int)
shippers["shipper_experience_years"] = shippers["shipper_experience_years"].round().astype(int)

# 6b. Điểm đánh giá (decimal): làm tròn 1 chữ số thập phân cho giống dữ liệu gốc
shippers["shipper_rating"] = shippers["shipper_rating"].round(1)

# 6c. Ngày tham gia: chuyển chuỗi thành kiểu ngày, ngày lỗi sẽ thành NaT (rỗng)
shippers["join_date"] = pd.to_datetime(shippers["join_date"], errors="coerce")

# 6d. Các cột chữ: cắt khoảng trắng thừa ở hai đầu để dữ liệu đồng nhất
for cot in cot_chu:
    shippers[cot] = shippers[cot].astype(str).str.strip()

# ============================================================
# BƯỚC 7: TẠO KHÓA NGOẠI location_id CHO KHU VỰC
# ============================================================
# File thô lưu khu vực bằng 3 cột (region, city, district) và không có mã zip.
# Region phụ thuộc vào city, nên để đạt 3NF ta tách khu vực ra bảng riêng,
# mỗi khu vực có 1 mã location_id, còn bảng SHIPPERS chỉ giữ mã đó (khóa ngoại).

# 7a. Lấy danh sách khu vực khác nhau, sắp xếp rồi đánh số 1, 2, 3...
locations = (
    shippers[["region", "city", "district"]]
    .drop_duplicates()
    .sort_values(["region", "city", "district"])
    .reset_index(drop=True)
)
locations["location_id"] = locations.index + 1
locations = locations[["location_id", "region", "city", "district"]]

# 7b. Gắn location_id vào bảng SHIPPERS bằng cách nối theo 3 cột khu vực
shippers = shippers.merge(locations, on=["region", "city", "district"], how="left")

print("\n=== BƯỚC 7: TẠO KHÓA NGOẠI ===")
print("Số khu vực khác nhau:", len(locations))
print("Số shipper chưa có location_id (phải bằng 0):", shippers["location_id"].isna().sum())

# ============================================================
# BƯỚC 8: KIỂM TRA RÀNG BUỘC LOGIC
# ============================================================
print("\n=== BƯỚC 8: KIỂM TRA RÀNG BUỘC ===")
print("shipper_id duy nhất:", shippers["shipper_id"].is_unique)
print("Số dòng shipper_age <= 0:", (shippers["shipper_age"] <= 0).sum())
print("Số dòng shipper_experience_years < 0:", (shippers["shipper_experience_years"] < 0).sum())
print("Số dòng shipper_rating ngoài khoảng 0-5:", (~shippers["shipper_rating"].between(0, 5)).sum())
print("Số dòng join_date không hợp lệ:", shippers["join_date"].isna().sum())

# ============================================================
# BƯỚC 9: SẮP XẾP CỘT THEO THIẾT KẾ VÀ XUẤT FILE
# ============================================================
thu_tu_cot = [
    "shipper_id",                # PK
    "shipper_name",
    "shipper_phone",
    "shipper_company",
    "shipper_gender",
    "shipper_age",
    "shipper_education",
    "shipper_experience_years",
    "shipper_marital_status",
    "shipper_vehicle",
    "join_date",
    "shipper_rating",
    "working_shift",
    "location_id",               # FK
]
shippers = shippers[thu_tu_cot].sort_values("shipper_id").reset_index(drop=True)
shippers["location_id"] = shippers["location_id"].astype(int)

# date_format="%Y-%m-%d": xuất ngày theo định dạng YYYY-MM-DD
# encoding="utf-8-sig": để Excel mở file tiếng Việt không bị lỗi font
shippers.to_csv(FILE_SHIPPERS, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
locations.to_csv(FILE_LOCATIONS, index=False, encoding="utf-8-sig")

print("\n=== BƯỚC 9: KẾT QUẢ ===")
print("Kích thước bảng SHIPPERS:", shippers.shape)
print(shippers.dtypes)
print("\n10 dòng đầu tiên của bảng SHIPPERS:")
print(shippers.head(10).to_string(index=False))
print(f"\nĐã xuất file: {FILE_SHIPPERS} và {FILE_LOCATIONS}")
