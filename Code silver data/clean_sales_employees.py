# -*- coding: utf-8 -*-
"""
LÀM SẠCH DỮ LIỆU VÀ ĐỔ VÀO THỰC THỂ SALES EMPLOYEES (3NF)
Nguồn : sales_employee.csv (dữ liệu thô)
Đích  : sales_employees_3NF.csv (đúng cấu trúc thực thể trong sơ đồ ERD)
"""

import pandas as pd  # Thư viện xử lý bảng dữ liệu

# ============================================================
# BƯỚC 0: KHAI BÁO ĐƯỜNG DẪN VÀ TÙY CHỌN
# ============================================================
FILE_VAO = "sales_employee.csv"          # File dữ liệu thô
FILE_RA = "sales_employees_3NF.csv"      # File kết quả sau khi làm sạch

# Sơ đồ ERD ghi sales_employee_id là int, nhưng dữ liệu thô là chuỗi "EMP0103".
# True  -> đổi thành số nguyên (EMP0103 -> 103), đúng với ERD
# False -> giữ nguyên chuỗi "EMP0103" (dùng khi các bảng khác cũng đang lưu dạng EMPxxxx)
CHUYEN_ID_SANG_SO = True

# ============================================================
# BƯỚC 1: ĐỌC DỮ LIỆU THÔ
# ============================================================
# encoding="utf-8-sig": file có ký tự BOM ở đầu, nếu không dùng thì
# tên cột đầu tiên sẽ bị lỗi thành "\ufeffsales_employee_id"
df = pd.read_csv(FILE_VAO, encoding="utf-8-sig")

print("=== BƯỚC 1: ĐỌC DỮ LIỆU ===")
print("Số dòng, số cột ban đầu:", df.shape)

# ============================================================
# BƯỚC 2: KHỬ TRÙNG LẶP
# ============================================================
so_dong_truoc = len(df)  # Lưu số dòng trước khi xóa để so sánh

# 2a. Xóa dòng trùng lặp hoàn toàn (giống nhau ở cả 5 cột)
df = df.drop_duplicates()

# 2b. Xóa dòng trùng khóa chính sales_employee_id (mỗi nhân viên chỉ 1 dòng)
#     keep="first": giữ lại dòng xuất hiện đầu tiên
df = df.drop_duplicates(subset="sales_employee_id", keep="first")

print("\n=== BƯỚC 2: KHỬ TRÙNG LẶP ===")
print("Số dòng đã xóa:", so_dong_truoc - len(df))
print("Số dòng còn lại:", len(df))

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
#     Dòng nào thiếu sales_employee_id thì không định danh được -> xóa
df = df.dropna(subset=["sales_employee_id"])

# 4b. Cột SỐ years_experience: điền giá trị Trung bình (Mean) vào chỗ Null
#     Tính Mean SAU khi đã khử trùng để các dòng lặp không làm lệch trung bình
gia_tri_tb = df["years_experience"].mean()                 # Tính trung bình của cột (bỏ qua Null)
df["years_experience"] = df["years_experience"].fillna(gia_tri_tb)  # Điền vào ô Null

# 4c. Cột CHỮ: điền 'N/A' cho ô Null (bạn có thể bỏ 3 dòng này nếu muốn giữ NULL)
cot_chu = ["sales_employee_name", "education_level", "marital_status"]
for cot in cot_chu:
    df[cot] = df[cot].fillna("N/A")

print("\nSố Null mỗi cột sau khi xử lý:")
print(df.isna().sum())

# ============================================================
# BƯỚC 5: ÉP KIỂU DỮ LIỆU CHO ĐÚNG VỚI ERD
# ============================================================
# 5a. years_experience: làm tròn rồi ép về số nguyên (int) theo yêu cầu của ERD
df["years_experience"] = df["years_experience"].round().astype(int)

# 5b. sales_employee_id: tùy chọn ở Bước 0
if CHUYEN_ID_SANG_SO:
    # Cắt bỏ tiền tố "EMP" rồi chuyển thành số nguyên: "EMP0103" -> 103
    df["sales_employee_id"] = (
        df["sales_employee_id"]
        .astype(str)
        .str.replace("EMP", "", regex=False)
        .astype(int)
    )
else:
    # Giữ dạng chuỗi, chỉ cắt khoảng trắng thừa ở hai đầu
    df["sales_employee_id"] = df["sales_employee_id"].astype(str).str.strip()

# 5c. Các cột chữ: cắt khoảng trắng thừa ở hai đầu để dữ liệu đồng nhất
for cot in cot_chu:
    df[cot] = df[cot].astype(str).str.strip()

# ============================================================
# BƯỚC 6: KIỂM TRA RÀNG BUỘC LOGIC
# ============================================================
print("\n=== BƯỚC 6: KIỂM TRA RÀNG BUỘC ===")

# 6a. Khóa chính phải duy nhất
print("sales_employee_id duy nhất:", df["sales_employee_id"].is_unique)

# 6b. Số năm kinh nghiệm không được âm
print("Số dòng years_experience âm:", (df["years_experience"] < 0).sum())

# ============================================================
# BƯỚC 7: SẮP XẾP CỘT THEO ĐÚNG THỨ TỰ TRONG ERD VÀ XUẤT FILE
# ============================================================
# File thô để marital_status trước education_level, còn ERD thì ngược lại
thu_tu_cot_erd = [
    "sales_employee_id",    # PK
    "sales_employee_name",
    "education_level",
    "marital_status",
    "years_experience",
]
sales_employees = df[thu_tu_cot_erd].sort_values("sales_employee_id").reset_index(drop=True)

# encoding="utf-8-sig": để Excel mở file tiếng Việt không bị lỗi font
sales_employees.to_csv(FILE_RA, index=False, encoding="utf-8-sig")

print("\n=== BƯỚC 7: KẾT QUẢ ===")
print("Kích thước bảng SALES EMPLOYEES:", sales_employees.shape)
print(sales_employees.dtypes)
print("\n10 dòng đầu tiên (preview):")
print(sales_employees.head(10).to_string(index=False))
print(f"\nĐã xuất file: {FILE_RA}")
