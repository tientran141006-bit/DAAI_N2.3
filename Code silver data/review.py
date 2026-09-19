import os
import pandas as pd

# ============================================================
# 1. KHAI BÁO ĐƯỜNG DẪN
# ============================================================

reviews_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\reviews.csv"
orders_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\orders.csv"
products_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\products.csv"
customers_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\customers.csv"
output_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\reviews_silver.csv"


# ============================================================
# 2. ĐỌC DỮ LIỆU VÀ KIỂM TRA DÒNG NULL / TRÙNG LẶP TOÀN BỘ
# ============================================================

if not os.path.exists(reviews_file):
    print("Không tìm thấy file reviews.csv tại đường dẫn:", reviews_file)
    exit()

reviews = pd.read_csv(reviews_file)

print("==============================================")
print("1. THỐNG KÊ DÒNG NULL TOÀN BỘ & TRÙNG LẶP HOÀN TOÀN")
print("==============================================")
print(f"Tổng số dòng ban đầu: {len(reviews)}")

# Chuẩn hóa khoảng trắng thành NA để kiểm tra null chính xác
reviews_clean_check = reviews.replace(r"^\s*$", pd.NA, regex=True)

# 1. Kiểm tra các dòng null hết (tất cả các cột đều là NA)
completely_null_rows = reviews_clean_check[reviews_clean_check.isnull().all(axis=1)]
print(f"- Số lượng dòng NULL hoàn toàn (tất cả các cột đều trống): {len(completely_null_rows)}")
if len(completely_null_rows) > 0:
    print("Các chỉ số dòng (index) bị NULL hoàn toàn:")
    print(completely_null_rows.index.tolist())

# 2. Kiểm tra các dòng trùng lặp hoàn toàn
duplicated_rows = reviews[reviews.duplicated(keep=False)]
print(f"- Số lượng dòng bị trùng lặp hoàn toàn (kể cả dòng gốc và dòng trùng): {len(duplicated_rows)}")
if len(duplicated_rows) > 0:
    print("Chi tiết các dòng bị trùng lặp hoàn toàn:")
    print(duplicated_rows)


# ============================================================
# 3. LÀM SẠCH (XÓA DÒNG NULL HẾT & TRÙNG LẶP)
# ============================================================

reviews = reviews_clean_check.dropna(how="all").reset_index(drop=True)
reviews = reviews.drop_duplicates().reset_index(drop=True)

print(f"\nTổng số dòng sau khi đã loại bỏ dòng null hết và trùng lặp: {len(reviews)}")


# ============================================================
# 4. TRÍCH XUẤT CÁC CỘT (GIỮ NGUYÊN REVIEW_ID GỐC)
# ============================================================

processed_reviews = pd.DataFrame()

# Giữ nguyên review_id gốc dưới dạng chuỗi (string)
processed_reviews["review_id"] = reviews["review_id"].astype(str).str.strip() if "review_id" in reviews.columns else pd.NA
processed_reviews.loc[processed_reviews["review_id"].isin(["nan", "None", ""]), "review_id"] = pd.NA

# Ánh xạ các cột còn lại từ file gốc
processed_reviews["order_id"] = reviews["order_id"] if "order_id" in reviews.columns else pd.NA
processed_reviews["product_id"] = reviews["product_id"] if "product_id" in reviews.columns else pd.NA

customer_col = "customer_id" if "customer_id" in reviews.columns else ([c for c in reviews.columns if c.startswith("customer")] or [pd.NA])[0]
processed_reviews["customer_id"] = reviews[customer_col] if customer_col in reviews.columns else pd.NA

date_col = "review_date" if "review_date" in reviews.columns else ([c for c in reviews.columns if c.startswith("review_dat")] or [pd.NA])[0]
processed_reviews["review_date"] = reviews[date_col] if date_col in reviews.columns else pd.NA

processed_reviews["rating"] = reviews["rating"] if "rating" in reviews.columns else pd.NA
processed_reviews["review_title"] = reviews["review_title"] if "review_title" in reviews.columns else pd.NA


# ============================================================
# 5. CHUYỂN ĐỔI KIỂU DỮ LIỆU CÁC CỘT KHÁC
# ============================================================

processed_reviews["order_id"] = pd.to_numeric(processed_reviews["order_id"], errors="coerce")
processed_reviews["product_id"] = pd.to_numeric(processed_reviews["product_id"], errors="coerce")
processed_reviews["customer_id"] = pd.to_numeric(processed_reviews["customer_id"], errors="coerce")

processed_reviews["review_date"] = pd.to_datetime(
    processed_reviews["review_date"], errors="coerce"
).dt.strftime('%Y-%m-%d')

processed_reviews["rating"] = pd.to_numeric(processed_reviews["rating"], errors="coerce")

processed_reviews["review_title"] = processed_reviews["review_title"].astype(str).str.strip()
processed_reviews.loc[processed_reviews["review_title"].isin(["nan", "None", ""]), "review_title"] = pd.NA


# ============================================================
# 6. XỬ LÝ DỮ LIỆU NULL CỤ THỂ TỪNG CỘT (NẾU CÓ)
# ============================================================

if processed_reviews["rating"].isnull().sum() > 0:
    median_rating = round(processed_reviews["rating"].median())
    processed_reviews["rating"] = processed_reviews["rating"].fillna(median_rating)
    print(f"\n- Đã điền rating thiếu bằng median: {median_rating}")

if processed_reviews["review_date"].isnull().sum() > 0:
    mode_date = processed_reviews["review_date"].mode()
    if len(mode_date) > 0:
        processed_reviews["review_date"] = processed_reviews["review_date"].fillna(mode_date.iloc[0])
        print(f"- Đã điền review_date thiếu bằng mode: {mode_date.iloc[0]}")


# ============================================================
# 7. KIỂM TRA KHÓA NGOẠI (FK) & RÀNG BUỘC KỸ THUẬT
# ============================================================

print("\n==============================================")
print("2. KIỂM TRA CÁC RÀNG BUỘC KỸ THUẬT KHÁC")
print("==============================================")

# Kiểm tra trùng lặp review_id sau khi làm sạch
duplicate_ids = processed_reviews["review_id"].duplicated().sum()
print(f"- Số lượng review_id bị trùng lặp: {duplicate_ids}")

# Kiểm tra order_id FK
if os.path.exists(orders_file):
    orders = pd.read_csv(orders_file)
    if "order_id" in orders.columns:
        valid_orders = pd.to_numeric(orders["order_id"], errors="coerce").dropna().unique()
        invalid_orders = processed_reviews[processed_reviews["order_id"].notna() & ~processed_reviews["order_id"].isin(valid_orders)]
        print(f"- Số lượng review có order_id không tồn tại trong ORDERS: {len(invalid_orders)}")

# Kiểm tra product_id FK
if os.path.exists(products_file):
    products = pd.read_csv(products_file)
    if "product_id" in products.columns:
        valid_products = pd.to_numeric(products["product_id"], errors="coerce").dropna().unique()
        invalid_products = processed_reviews[processed_reviews["product_id"].notna() & ~processed_reviews["product_id"].isin(valid_products)]
        print(f"- Số lượng review có product_id không tồn tại trong PRODUCTS: {len(invalid_products)}")

# Kiểm tra customer_id FK
if os.path.exists(customers_file):
    customers = pd.read_csv(customers_file)
    if "customer_id" in customers.columns:
        valid_customers = pd.to_numeric(customers["customer_id"], errors="coerce").dropna().unique()
        invalid_customers = processed_reviews[processed_reviews["customer_id"].notna() & ~processed_reviews["customer_id"].isin(valid_customers)]
        print(f"- Số lượng review có customer_id không tồn tại trong CUSTOMERS: {len(invalid_customers)}")

# Kiểm tra khoảng rating (1-5)
invalid_ratings = ((processed_reviews["rating"] < 1) | (processed_reviews["rating"] > 5)).sum()
print(f"- Số lượng rating ngoài khoảng 1-5: {invalid_ratings}")


# ============================================================
# 8. CHUYỂN ĐỔI KIỂU DỮ LIỆU CỐ ĐỊNH & XUẤT FILE
# ============================================================

processed_reviews["order_id"] = processed_reviews["order_id"].astype("Int64")
processed_reviews["product_id"] = processed_reviews["product_id"].astype("Int64")
processed_reviews["customer_id"] = processed_reviews["customer_id"].astype("Int64")
processed_reviews["rating"] = processed_reviews["rating"].astype("Int64")

processed_reviews = processed_reviews.sort_values(by="review_id").reset_index(drop=True)

processed_reviews.to_csv(output_file, index=False, encoding="utf-8-sig")

print("\n==============================================")
print("3. HOÀN THÀNH XUẤT FILE REVIEWS SILVER")
print("==============================================")
print("Đường dẫn file kết quả:", output_file)
print("Tổng số dòng ghi nhận cuối cùng:", len(processed_reviews))
print("\nXem trước 5 dòng đầu tiên:")
print(processed_reviews.head())