import pandas as pd
import os


# ============================================================
# 1. KHAI BÁO ĐƯỜNG DẪN
# ============================================================

order_items_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\order_items.csv"
orders_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\orders.csv"
products_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\products.csv"
promotions_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\promotions.csv"

# File output Silver
output_order_items = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\order_items_silver.csv"
output_items_promo = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\order_items_promotion_silver.csv"


# ============================================================
# 2. ĐỌC FILE ORDER_ITEMS
# ============================================================

if not os.path.exists(order_items_file):
    print(f"Không tìm thấy file: {order_items_file}")
    exit()

order_items = pd.read_csv(order_items_file)

print("==============================================")
print("ĐỌC DỮ LIỆU ORDER_ITEMS")
print("==============================================")
print("Số dòng dữ liệu:", len(order_items))


# ============================================================
# 3. CHUYỂN ĐỔI KIỂU DỮ LIỆU CƠ BẢN
# ============================================================

order_items = order_items.replace(r"^\s*$", pd.NA, regex=True)

order_items["order_id"] = pd.to_numeric(order_items["order_id"], errors="coerce")
order_items["product_id"] = pd.to_numeric(order_items["product_id"], errors="coerce")
order_items["quantity"] = pd.to_numeric(order_items["quantity"], errors="coerce").fillna(1)
order_items["unit_price"] = pd.to_numeric(order_items["unit_price"], errors="coerce").fillna(0)
order_items["discount_amount"] = pd.to_numeric(order_items["discount_amount"], errors="coerce").fillna(0)

# Chuẩn hóa mã khuyến mãi
order_items["promo_id"] = order_items["promo_id"].astype(str).str.strip()
order_items.loc[order_items["promo_id"].isin(["nan", "None", ""]), "promo_id"] = pd.NA

order_items["promo_id_2"] = order_items["promo_id_2"].astype(str).str.strip()
order_items.loc[order_items["promo_id_2"].isin(["nan", "None", ""]), "promo_id_2"] = pd.NA


# ============================================================
# 4. TẠO BẢNG ORDER_ITEMS_SILVER
# ============================================================

order_items_silver = order_items[[
    "order_id",
    "product_id",
    "quantity",
    "unit_price",
    "discount_amount"
]].copy()

order_items_silver["order_id"] = order_items_silver["order_id"].astype(int)
order_items_silver["product_id"] = order_items_silver["product_id"].astype(int)
order_items_silver["quantity"] = order_items_silver["quantity"].astype(int)
order_items_silver["unit_price"] = order_items_silver["unit_price"].round(2)
order_items_silver["discount_amount"] = order_items_silver["discount_amount"].round(2)

order_items_silver = order_items_silver.drop_duplicates(subset=["order_id", "product_id"]).reset_index(drop=True)
order_items_silver.to_csv(output_order_items, index=False, encoding="utf-8-sig")


# ============================================================
# 5. XỬ LÝ VÀ KIỂM TRA KHÓA NGOẠI CHO BẢNG TRUNG GIAN ORDER_ITEMS_PROMOTION
# ============================================================

print("\n==============================================")
print("KIỂM TRA KHÓA NGOẠI CHO BẢNG TRUNG GIAN")
print("==============================================")

# Lấy danh sách hợp lệ từ các bảng cha (nếu file tồn tại)
valid_orders = set()
if os.path.exists(orders_file):
    orders_df = pd.read_csv(orders_file)
    if "order_id" in orders_df.columns:
        valid_orders = set(pd.to_numeric(orders_df["order_id"], errors="coerce").dropna().astype(int))

valid_products = set()
if os.path.exists(products_file):
    products_df = pd.read_csv(products_file)
    if "product_id" in products_df.columns:
        valid_products = set(pd.to_numeric(products_df["product_id"], errors="coerce").dropna().astype(int))

valid_promos = set()
if os.path.exists(promotions_file):
    promotions_df = pd.read_csv(promotions_file)
    # Tùy thuộc vào cột khóa chính của bảng promotions (thường là 'promo_id')
    promo_col = "promo_id" if "promo_id" in promotions_df.columns else promotions_df.columns[0]
    valid_promos = set(promotions_df[promo_col].astype(str).str.strip().dropna())

# Trích xuất các dòng có áp dụng khuyến mãi
items_promo_list = []
for _, row in order_items.iterrows():
    o_id = row["order_id"]
    p_id = row["product_id"]
    p1 = row["promo_id"]
    p2 = row["promo_id_2"]
    
    if pd.notna(o_id) and pd.notna(p_id):
        # Kiểm tra điều kiện khóa ngoại cơ bản với orders và products
        if valid_orders and int(o_id) not in valid_orders:
            continue
        if valid_products and int(p_id) not in valid_products:
            continue
            
        # Thêm promo_id chính nếu hợp lệ
        if pd.notna(p1):
            if not valid_promos or str(p1) in valid_promos:
                items_promo_list.append({
                    "order_id": int(o_id),
                    "product_id": int(p_id),
                    "promo_id": str(p1),
                    "promo_id_2": str(p2) if pd.notna(p2) and (not valid_promos or str(p2) in valid_promos) else pd.NA
                })
        # Trường hợp chỉ có promo_id_2 mà không có promo_id chính
        elif pd.notna(p2):
            if not valid_promos or str(p2) in valid_promos:
                items_promo_list.append({
                    "order_id": int(o_id),
                    "product_id": int(p_id),
                    "promo_id": str(p2),
                    "promo_id_2": pd.NA
                })

order_items_promotion_silver = pd.DataFrame(items_promo_list)

if not order_items_promotion_silver.empty:
    order_items_promotion_silver = order_items_promotion_silver.drop_duplicates().reset_index(drop=True)

order_items_promotion_silver.to_csv(output_items_promo, index=False, encoding="utf-8-sig")


# ============================================================
# 6. KẾT QUẢ
# ============================================================

print("\n==============================================")
print("HOÀN THÀNH XỬ LÝ ORDER_ITEMS & PROMOTION")
print("==============================================")
print(f"1. order_items_silver.csv: {len(order_items_silver)} dòng")
print(f"2. order_items_promotion_silver.csv: {len(order_items_promotion_silver)} dòng")