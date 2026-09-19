# -*- coding: utf-8 -*-
"""
LÀM SẠCH DỮ LIỆU VÀ ĐỔ VÀO THỰC THỂ PROMOTIONS (3NF)
Nguồn : PROMOTIONS_FINAL.csv (dữ liệu thô)
Đích  : PROMOTIONS.csv (đúng cấu trúc thực thể trong sơ đồ ERD)
"""

import pandas as pd  # Thư viện xử lý bảng dữ liệu

# ============================================================
# BƯỚC 0: KHAI BÁO ĐƯỜNG DẪN
# ============================================================
FILE_VAO = "PROMOTIONS_FINAL.csv"   # File dữ liệu thô
FILE_RA = "PROMOTIONS.csv"          # File kết quả sau khi làm sạch

# ============================================================
# BƯỚC 1: ĐỌC DỮ LIỆU THÔ
# ============================================================
# encoding="utf-8-sig": file có ký tự BOM ở đầu, nếu không dùng thì
# tên cột đầu tiên sẽ bị lỗi thành "\ufeffpromo_id"
df = pd.read_csv(FILE_VAO, encoding="utf-8-sig")

print("=== BƯỚC 1: ĐỌC DỮ LIỆU ===")
print("Số dòng, số cột ban đầu:", df.shape)

# ============================================================
# BƯỚC 2: KHỬ TRÙNG LẶP
# ============================================================
so_dong_truoc = len(df)

# 2a. Xóa dòng trùng lặp hoàn toàn (giống nhau ở mọi cột)
df = df.drop_duplicates()

# 2b. Xóa dòng trùng khóa chính promo_id (mỗi promo_id chỉ được xuất hiện 1 lần)
#     keep="first": giữ lại dòng xuất hiện đầu tiên
df = df.drop_duplicates(subset="promo_id", keep="first")

print("\n=== BƯỚC 2: KHỬ TRÙNG LẶP ===")
print("Số dòng đã xóa:", so_dong_truoc - len(df))

# ============================================================
# BƯỚC 3: XÓA DÒNG NULL 100%
# ============================================================
so_dong_truoc = len(df)

# how="all": chỉ xóa dòng mà TẤT CẢ các cột đều trống
df = df.dropna(how="all")

print("\n=== BƯỚC 3: XÓA DÒNG NULL HOÀN TOÀN ===")
print("Số dòng đã xóa:", so_dong_truoc - len(df))

# ============================================================
# BƯỚC 4: XỬ LÝ NULL MỘT PHẦN
# ============================================================
print("\n=== BƯỚC 4: XỬ LÝ NULL MỘT PHẦN ===")
print("Số Null mỗi cột trước khi xử lý:")
print(df.isna().sum())

# 4a. Khóa chính (PK): bắt buộc không được NULL
#     Dòng nào thiếu promo_id thì không định danh được -> xóa
df = df.dropna(subset=["promo_id"])

# 4b. Cột dạng SỐ (numeric): điền giá trị Trung bình (Mean) vào chỗ Null
cot_so = ["discount_value", "min_order_value"]
for cot in cot_so:
    gia_tri_tb = df[cot].mean()          # Tính trung bình của cột (bỏ qua Null)
    df[cot] = df[cot].fillna(gia_tri_tb)  # Điền trung bình vào ô Null

# 4c. Cột dạng CHỮ / DANH MỤC (categorical): giữ nguyên NULL
#     Riêng các cột chữ BẮT BUỘC (không được để trống) thì thay bằng 'N/A'
cot_chu_bat_buoc = ["promo_name", "promo_type", "promo_channel"]
for cot in cot_chu_bat_buoc:
    df[cot] = df[cot].fillna("N/A")

# applicable_category: KHÔNG bắt buộc -> giữ nguyên NULL
# (NULL ở đây có nghĩa là khuyến mãi áp dụng cho TẤT CẢ danh mục)

print("\nSố Null mỗi cột sau khi xử lý:")
print(df.isna().sum())

# ============================================================
# BƯỚC 5: ÉP KIỂU DỮ LIỆU CHO ĐÚNG VỚI ERD
# ============================================================
# ERD quy định: promo_id là int, nhưng dữ liệu thô là chữ "PROMO-0001".
# Cắt bỏ tiền tố "PROMO-" rồi chuyển thành số nguyên: "PROMO-0001" -> 1
df["promo_id"] = (
    df["promo_id"]
    .astype(str)
    .str.replace("PROMO-", "", regex=False)
    .astype(int)
)

# Cột decimal: làm tròn 2 chữ số thập phân
df["discount_value"] = df["discount_value"].astype(float).round(2)
df["min_order_value"] = df["min_order_value"].astype(float).round(2)

# Cột boolean: dữ liệu thô là 0/1 -> chuyển thành True/False
df["stackable_flag"] = df["stackable_flag"].astype(bool)

# Cột date: chuyển chuỗi thành kiểu ngày
df["start_date"] = pd.to_datetime(df["start_date"])
df["end_date"] = pd.to_datetime(df["end_date"])

# ============================================================
# BƯỚC 6: KIỂM TRA RÀNG BUỘC LOGIC
# ============================================================
print("\n=== BƯỚC 6: KIỂM TRA RÀNG BUỘC ===")

# 6a. promo_id phải là duy nhất (đúng yêu cầu của khóa chính)
print("promo_id duy nhất:", df["promo_id"].is_unique)

# 6b. Ngày kết thúc phải >= ngày bắt đầu
so_loi_ngay = (df["end_date"] < df["start_date"]).sum()
print("Số dòng có end_date < start_date:", so_loi_ngay)

# 6c. Giá trị giảm giá không âm; nếu là phần trăm thì không vượt quá 100
so_loi_giam = (df["discount_value"] < 0).sum()
so_loi_pt = ((df["promo_type"] == "percentage") & (df["discount_value"] > 100)).sum()
print("Số dòng discount_value âm:", so_loi_giam)
print("Số dòng giảm phần trăm > 100:", so_loi_pt)

# ============================================================
# BƯỚC 7: SẮP XẾP CỘT THEO ĐÚNG THỨ TỰ TRONG ERD VÀ XUẤT FILE
# ============================================================
thu_tu_cot_erd = [
    "promo_id",             # PK
    "promo_name",
    "promo_type",
    "discount_value",
    "min_order_value",
    "applicable_category",
    "promo_channel",
    "stackable_flag",
    "start_date",
    "end_date",
]
promotions = df[thu_tu_cot_erd].sort_values("promo_id").reset_index(drop=True)

# Xuất ra CSV. na_rep="" để ô NULL được để trống (nhập vào SQL sẽ thành NULL)
promotions.to_csv(FILE_RA, index=False, encoding="utf-8", na_rep="",
                  date_format="%Y-%m-%d")

print("\n=== BƯỚC 7: KẾT QUẢ ===")
print("Kích thước bảng PROMOTIONS:", promotions.shape)
print(promotions.dtypes)
print(promotions.head(10).to_string(index=False))
print(f"\nĐã xuất file: {FILE_RA}")
