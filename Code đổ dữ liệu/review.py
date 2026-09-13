import pandas as pd
import os


# ============================================================
# 1. KHAI BÁO ĐƯỜNG DẪN
# ============================================================

# File REVIEWS gốc
reviews_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\reviews.csv"

# File ORDERS gốc (để kiểm tra khóa ngoại order_id)
orders_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\orders.csv"

# File PRODUCTS gốc (để kiểm tra khóa ngoại product_id)
products_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\products.csv"

# File CUSTOMERS gốc (để kiểm tra khóa ngoại customer_id)
customers_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\customers.csv"

# File REVIEWS sau khi xử lý
output_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\reviews_silver.csv"


# ============================================================
# 2. KIỂM TRA FILE REVIEWS
# ============================================================

if not os.path.exists(reviews_file):
    print("Không tìm thấy file reviews.csv:")
    print(reviews_file)
    exit()


# ============================================================
# 3. ĐỌC DỮ LIỆU REVIEWS
# ============================================================

reviews = pd.read_csv(reviews_file)

print("==============================================")
print("ĐỌC DỮ LIỆU REVIEWS")
print("==============================================")

print("Số dòng dữ liệu:", len(reviews))

print("\nCác cột ban đầu:")
print(reviews.columns.tolist())


# ============================================================
# 4. KIỂM TRA CÁC CỘT CẦN THIẾT
# ============================================================

required_columns = [
    "review_id",
    "order_id",
    "product_id",
    "customer_id",
    "review_date",
    "rating",
    "review_title"
]

for column in required_columns:

    if column not in reviews.columns:

        print("\nThiếu cột:", column)
        print("Kiểm tra lại file reviews.csv")
        exit()

print("\nREVIEWS có đầy đủ các cột cần thiết.")


# ============================================================
# 5. CHỈ GIỮ CÁC CỘT THEO BẢNG 3NF
# ============================================================

reviews = reviews[
    [
        "review_id",
        "order_id",
        "product_id",
        "customer_id",
        "review_date",
        "rating",
        "review_title"
    ]
].copy()


# ============================================================
# 6. CHUYỂN Ô RỖNG THÀNH NULL
# ============================================================

reviews = reviews.replace(
    r"^\s*$",
    pd.NA,
    regex=True
)


# ============================================================
# 7. CHUYỂN KIỂU DỮ LIỆU
# ============================================================

reviews["review_id"] = reviews["review_id"].astype(str).str.strip()

reviews["order_id"] = pd.to_numeric(
    reviews["order_id"],
    errors="coerce"
)

reviews["product_id"] = pd.to_numeric(
    reviews["product_id"],
    errors="coerce"
)

reviews["customer_id"] = pd.to_numeric(
    reviews["customer_id"],
    errors="coerce"
)

reviews["review_date"] = pd.to_datetime(
    reviews["review_date"],
    errors="coerce"
).dt.strftime('%Y-%m-%d')

reviews["rating"] = pd.to_numeric(
    reviews["rating"],
    errors="coerce"
)

reviews["review_title"] = reviews["review_title"].astype(str).str.strip()
reviews.loc[reviews["review_title"].isin(["nan", "None", ""]), "review_title"] = pd.NA


# ============================================================
# 8. KIỂM TRA NULL TRƯỚC KHI LẤP ĐẦY
# ============================================================

print("\n==============================================")
print("KIỂM TRA NULL TRƯỚC KHI XỬ LÝ")
print("==============================================")

print(reviews.isnull().sum())


# ============================================================
# 9. XỬ LÝ REVIEW_ID BỊ NULL (NẾU CÓ)
# ============================================================

# Nếu review_id bị thiếu, có thể tự động gán mã định danh
if reviews["review_id"].isnull().sum() > 0 or (reviews["review_id"] == "nan").sum() > 0:
    missing_mask = reviews["review_id"].isnull() | (reviews["review_id"] == "nan")
    reviews.loc[missing_mask, "review_id"] = [f"REV-{i+1:05d}" for i in range(missing_mask.sum())]
    print("\nĐã tự động tạo review_id cho các dòng bị thiếu.")


# ============================================================
# 10. XỬ LÝ RATING BỊ NULL
# ============================================================

# Nếu rating bị thiếu, sử dụng giá trị trung vị (median) hoặc mode làm tròn
if reviews["rating"].isnull().sum() > 0:

    median_rating = round(reviews["rating"].median())

    reviews["rating"] = reviews["rating"].fillna(median_rating)

    print(
        "\nĐã bổ sung rating bị thiếu bằng median:",
        median_rating
    )


# ============================================================
# 11. XỬ LÝ REVIEW_DATE BỊ NULL
# ============================================================

if reviews["review_date"].isnull().sum() > 0:

    mode_date = reviews["review_date"].mode()

    if len(mode_date) > 0:
        reviews["review_date"] = reviews["review_date"].fillna(mode_date.iloc[0])
        print("\nĐã bổ sung review_date bị thiếu bằng mode:", mode_date.iloc[0])


# ============================================================
# 12. KIỂM TRA KHÓA NGOẠI (ORDER_ID, PRODUCT_ID, CUSTOMER_ID)
# ============================================================

print("\n==============================================")
print("KIỂM TRA CÁC KHÓA NGOẠI (FK)")
print("==============================================")

# Kiểm tra order_id
if os.path.exists(orders_file):
    orders = pd.read_csv(orders_file)
    if "order_id" in orders.columns:
        orders["order_id"] = pd.to_numeric(orders["order_id"], errors="coerce")
        valid_orders = orders["order_id"].dropna().unique()
        invalid_orders = reviews[reviews["order_id"].notna() & ~reviews["order_id"].isin(valid_orders)]
        print(f"Số review có order_id không tồn tại trong ORDERS: {len(invalid_orders)}")
    else:
        print("orders.csv không có cột order_id.")
else:
    print("Không tìm thấy orders.csv, bỏ qua kiểm tra order_id FK.")

# Kiểm tra product_id
if os.path.exists(products_file):
    products = pd.read_csv(products_file)
    if "product_id" in products.columns:
        products["product_id"] = pd.to_numeric(products["product_id"], errors="coerce")
        valid_products = products["product_id"].dropna().unique()
        invalid_products = reviews[reviews["product_id"].notna() & ~reviews["product_id"].isin(valid_products)]
        print(f"Số review có product_id không tồn tại trong PRODUCTS: {len(invalid_products)}")
    else:
        print("products.csv không có cột product_id.")
else:
    print("Không tìm thấy products.csv, bỏ qua kiểm tra product_id FK.")

# Kiểm tra customer_id
if os.path.exists(customers_file):
    customers = pd.read_csv(customers_file)
    if "customer_id" in customers.columns:
        customers["customer_id"] = pd.to_numeric(customers["customer_id"], errors="coerce")
        valid_customers = customers["customer_id"].dropna().unique()
        invalid_customers = reviews[reviews["customer_id"].notna() & ~reviews["customer_id"].isin(valid_customers)]
        print(f"Số review có customer_id không tồn tại trong CUSTOMERS: {len(invalid_customers)}")
    else:
        print("customers.csv không có cột customer_id.")
else:
    print("Không tìm thấy customers.csv, bỏ qua kiểm tra customer_id FK.")


# ============================================================
# 13. KIỂM TRA REVIEW_ID (PK)
# ============================================================

print("\n==============================================")
print("KIỂM TRA REVIEW_ID")
print("==============================================")

total_rows = len(reviews)
unique_review_ids = reviews["review_id"].nunique()

print("Tổng số dòng:", total_rows)
print("Số review_id khác nhau:", unique_review_ids)

if total_rows == unique_review_ids:
    print("review_id không bị trùng.")
else:
    print("CẢNH BÁO: review_id bị trùng.")


# ============================================================
# 14. KIỂM TRA RATING (CHECK 1-5)
# ============================================================

print("\n==============================================")
print("KIỂM TRA RATING")
print("==============================================")

invalid_ratings = (
    (reviews["rating"] < 1) | (reviews["rating"] > 5)
).sum()

print("Số rating ngoài khoảng 1-5:", invalid_ratings)

if invalid_ratings == 0:
    print("rating hợp lệ (trong khoảng 1-5).")
else:
    print("CẢNH BÁO: Có rating không nằm trong khoảng 1-5.")


# ============================================================
# 15. KIỂM TRA NULL SAU KHI LẤP ĐẦY
# ============================================================

print("\n==============================================")
print("NULL SAU KHI LẤP ĐẦY")
print("==============================================")

null_result = reviews.isnull().sum()
print(null_result)


# ============================================================
# 16. CHUYỂN ĐỔI KIỂU DỮ LIỆU CỐ ĐỊNH TRƯỚC KHI XUẤT FILE
# ============================================================

if reviews["order_id"].isnull().sum() == 0:
    reviews["order_id"] = reviews["order_id"].astype(int)

if reviews["product_id"].isnull().sum() == 0:
    reviews["product_id"] = reviews["product_id"].astype(int)

if reviews["customer_id"].isnull().sum() == 0:
    reviews["customer_id"] = reviews["customer_id"].astype(int)

if reviews["rating"].isnull().sum() == 0:
    reviews["rating"] = reviews["rating"].astype(int)


# ============================================================
# 17. SẮP XẾP VÀ XUẤT FILE SILVER
# ============================================================

reviews = reviews.sort_values(
    by="review_id"
).reset_index(drop=True)

reviews.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 18. HIỂN THỊ KẾT QUẢ CUỐI CÙNG
# ============================================================

print("\n==============================================")
print("HOÀN THÀNH REVIEWS SILVER")
print("==============================================")

print("\nFile Silver:")
print(output_file)

print("\nCấu trúc bảng REVIEWS:")
print(reviews.columns.tolist())

print("\nTổng số dòng:", len(reviews))

print("\n5 dòng đầu tiên:")
print(reviews.head())

print("\n5 dòng cuối cùng:")
print(reviews.tail())

print("\nKiểm tra NULL lần cuối:")
print(reviews.isnull().sum())

print("\n==============================================")
print("ĐÃ XỬ LÝ XONG REVIEWS")
print("==============================================")