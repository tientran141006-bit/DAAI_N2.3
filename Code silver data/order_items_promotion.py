import os
import pandas as pd


# ============================================================
# 1. KHAI BÁO ĐƯỜNG DẪN FILE
# ============================================================

base_dir = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\student_data"

order_items_file = os.path.join(base_dir, "order_items.csv")
orders_file = os.path.join(base_dir, "orders.csv")
products_file = os.path.join(base_dir, "products.csv")
promotions_file = os.path.join(base_dir, "promotions.csv")

output_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\order_items_promotion_silver.csv"


# ============================================================
# 2. ĐỌC DỮ LIỆU VÀ THỰC HIỆN CÁC KIỂM TRA (CHECKS)
# ============================================================

if not os.path.exists(order_items_file):
    print(f"Không tìm thấy file: {order_items_file}")
    exit()

order_items = pd.read_csv(order_items_file, low_memory=False)

print("==============================================")
print("THỐNG KÊ KIỂM TRA DỮ LIỆU (DATA VALIDATION)")
print("==============================================")
print(f"1. Tổng số dòng ban đầu trong order_items: {len(order_items)}")

# Chuẩn hóa khoảng trắng thành giá trị NA để kiểm tra chính xác
order_items_clean_check = order_items.replace(r"^\s*$", pd.NA, regex=True)

# Kiểm tra 1: Dòng trống hoàn toàn (tất cả các cột đều null)
completely_null_rows = order_items_clean_check[order_items_clean_check.isnull().all(axis=1)]
print(f"2. Số lượng dòng NULL hoàn toàn: {len(completely_null_rows)}")

# Kiểm tra 2: Dòng trùng lặp hoàn toàn (duplicated rows)
duplicated_rows = order_items[order_items.duplicated(keep=False)]
num_duplicated = order_items.duplicated().sum()
print(f"3. Số lượng dòng bị trùng lặp hoàn toàn (cần loại bỏ bớt): {num_duplicated}")

# Làm sạch cơ bản: Loại bỏ dòng null hoàn toàn và dòng trùng lặp
order_items = order_items_clean_check.dropna(how="all").reset_index(drop=True)
order_items = order_items.drop_duplicates().reset_index(drop=True)
print(f"4. Số dòng sau khi loại bỏ null toàn bộ và trùng lặp: {len(order_items)}")

# Ép kiểu dữ liệu khóa chính/khóa ngoại cơ bản
order_items["order_id"] = pd.to_numeric(order_items["order_id"], errors="coerce")
order_items["product_id"] = pd.to_numeric(order_items["product_id"], errors="coerce")

# Chuẩn hóa các cột mã giảm giá
order_items["promo_id"] = order_items["promo_id"].astype(str).str.strip()
order_items["promo_id"] = order_items["promo_id"].replace(["nan", "None", "<NA>", ""], pd.NA)

order_items["promo_id_2"] = order_items["promo_id_2"].astype(str).str.strip()
order_items["promo_id_2"] = order_items["promo_id_2"].replace(["nan", "None", "<NA>", ""], pd.NA)


# ============================================================
# 3. KIỂM TRA THAM CHIẾU KHÓA NGOẠI (FOREIGN KEY CHECKS)
# ============================================================

valid_orders = set()
if os.path.exists(orders_file):
    orders_df = pd.read_csv(orders_file, low_memory=False)
    if "order_id" in orders_df.columns:
        valid_orders = set(pd.to_numeric(orders_df["order_id"], errors="coerce").dropna().astype(int))

valid_products = set()
if os.path.exists(products_file):
    products_df = pd.read_csv(products_file, low_memory=False)
    if "product_id" in products_df.columns:
        valid_products = set(pd.to_numeric(products_df["product_id"], errors="coerce").dropna().astype(int))

valid_promos = set()
if os.path.exists(promotions_file):
    promotions_df = pd.read_csv(promotions_file, low_memory=False)
    promo_col = "promo_id" if "promo_id" in promotions_df.columns else promotions_df.columns[0]
    if promo_col in promotions_df.columns:
        valid_promos = set(promotions_df[promo_col].astype(str).str.strip().dropna())


# ============================================================
# 4. XỬ LÝ VÀ ĐỔ DỮ LIỆU VÀO BẢNG TRUNG GIAN (GIỮ LẠI DÒNG NULL PROMO)
# ============================================================

promo_rows = []
invalid_fk_count = 0

for _, row in order_items.iterrows():
    o_id = row["order_id"]
    p_id = row["product_id"]
    p1 = row["promo_id"]
    p2 = row["promo_id_2"]
    
    # Bỏ qua nếu thiếu order_id hoặc product_id (khóa bắt buộc)
    if pd.isna(o_id) or pd.isna(p_id):
        continue
        
    o_id_int = int(o_id)
    p_id_int = int(p_id)
    
    # Kiểm tra tính hợp lệ của khóa ngoại (nếu không tồn tại trong bảng cha thì loại bỏ dòng này)
    if valid_orders and o_id_int not in valid_orders:
        invalid_fk_count += 1
        continue
    if valid_products and p_id_int not in valid_products:
        invalid_fk_count += 1
        continue
        
    # Xử lý promo_id: Nếu có và hợp lệ thì giữ lại, KHÔNG CÓ thì gán thành pd.NA (null)
    p1_val = pd.NA
    if pd.notna(p1):
        p1_str = str(p1)
        if not valid_promos or p1_str in valid_promos:
            p1_val = p1_str
            
    # Xử lý promo_id_2: Nếu có và hợp lệ thì giữ lại, KHÔNG CÓ thì gán thành pd.NA (null)
    p2_val = pd.NA
    if pd.notna(p2):
        p2_str = str(p2)
        if not valid_promos or p2_str in valid_promos:
            p2_val = p2_str
            
    # THÊM DÒNG VÀO BẢNG TRUNG GIAN (Kể cả không có mã giảm giá vẫn được thêm vào với giá trị NA)
    promo_rows.append({
        "order_id": o_id_int,
        "product_id": p_id_int,
        "promo_id": p1_val,
        "promo_id_2": p2_val
    })

order_items_promotion_silver = pd.DataFrame(promo_rows)

if not order_items_promotion_silver.empty:
    # Loại bỏ trùng lặp tổ hợp khóa
    order_items_promotion_silver = order_items_promotion_silver.drop_duplicates(
        subset=["order_id", "product_id", "promo_id", "promo_id_2"]
    ).reset_index(drop=True)

    order_items_promotion_silver["order_id"] = order_items_promotion_silver["order_id"].astype(int)
    order_items_promotion_silver["product_id"] = order_items_promotion_silver["product_id"].astype(int)

# Xuất kết quả (Đã sửa lỗi cú pháp ở đây)
order_items_promotion_silver.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"5. Số dòng bị loại do sai khóa ngoại (orders/products): {invalid_fk_count}")
print(f"6. Tổng số dòng ghi nhận cuối cùng vào bảng trung gian: {len(order_items_promotion_silver)}")
print("==============================================")