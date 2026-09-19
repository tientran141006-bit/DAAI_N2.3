import os
import pandas as pd
import numpy as np

# 1. Đường dẫn thư mục
INPUT_DIR = './cleanfile'
OUTPUT_DIR = './silver'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Hàm làm sạch chuẩn theo đúng quy tắc
def apply_cleaning_rules(df, numeric_exclude_cols=None):
    if numeric_exclude_cols is None:
        numeric_exclude_cols = []
        
    # Chuẩn hóa chuỗi rỗng / khoảng trắng về NaN
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df = df.replace(['unknown', 'Unknown', 'null', 'NULL', 'none', 'None', 'NA', 'N/A'], np.nan)
    
    # Quy tắc 1: Xóa dòng nếu cả dòng đều là null
    df = df.dropna(how='all')
    
    # Quy tắc 2: Xóa dòng nếu trùng lặp hoàn toàn
    df = df.drop_duplicates()
    
    # Quy tắc 3: Xóa cột nếu tất cả các dòng đều là null (100% missing)
    df = df.dropna(axis=1, how='all')
    
    # Quy tắc 4: Cột số có null -> tính trung bình (mean) -> điền vào
    for col in df.columns:
        if col in numeric_exclude_cols or col.lower().endswith('_id') or 'date' in col.lower() or col.lower() == 'zip':
            continue
        # Kiểm tra kiểu số
        numeric_s = pd.to_numeric(df[col], errors='coerce')
        if pd.api.types.is_numeric_dtype(df[col]) or (numeric_s.notna().sum() / len(df) > 0.5):
            df[col] = numeric_s
            if df[col].isna().sum() > 0:
                mean_val = df[col].mean()
                df[col] = df[col].fillna(mean_val)
                
    return df

print("=== BẮT ĐẦU CHUẨN HÓA VÀ ĐỔ DỮ LIỆU SANG SILVER LAYER ===")

# -------------------------------------------------------------
# BẢNG 1: CUSTOMERS
# -------------------------------------------------------------
path_cust = os.path.join(INPUT_DIR, 'customers.csv')
df_cust_raw = pd.read_csv(path_cust, low_memory=False)

# Cột chuẩn theo ERD (loại bỏ city để đạt chuẩn 3NF vì city nằm ở GEOGRAPHY)
cust_erd_cols = ['customer_id', 'gender', 'age_group', 'zip', 'acquisition_channel', 'signup_date']
df_cust_silver = df_cust_raw[[c for c in cust_erd_cols if c in df_cust_raw.columns]]
df_cust_silver = apply_cleaning_rules(df_cust_silver, numeric_exclude_cols=['customer_id', 'zip'])
df_cust_silver.to_csv(os.path.join(OUTPUT_DIR, 'customers_silver.csv'), index=False)
print(f"[OK] CUSTOMERS: {df_cust_silver.shape[0]:,} dòng x {df_cust_silver.shape[1]} cột -> customers_silver.csv")

# -------------------------------------------------------------
# BẢNG 2: ORDERS
# -------------------------------------------------------------
path_orders = os.path.join(INPUT_DIR, 'orders.csv')
df_orders_raw = pd.read_csv(path_orders, low_memory=False)

# Cột chuẩn theo ERD
orders_erd_cols = ['order_id', 'customer_id', 'order_date', 'order_status', 'order_source', 'device_type', 'zip', 'sales_employee_id', 'comment']
df_orders_silver = df_orders_raw[[c for c in orders_erd_cols if c in df_orders_raw.columns]]
df_orders_silver = apply_cleaning_rules(df_orders_silver, numeric_exclude_cols=['order_id', 'customer_id', 'zip', 'sales_employee_id'])
df_orders_silver.to_csv(os.path.join(OUTPUT_DIR, 'orders_silver.csv'), index=False)
print(f"[OK] ORDERS: {df_orders_silver.shape[0]:,} dòng x {df_orders_silver.shape[1]} cột -> orders_silver.csv")

# -------------------------------------------------------------
# BẢNG 3: INVENTORY
# -------------------------------------------------------------
path_inv = os.path.join(INPUT_DIR, 'inventory_clean.csv')
df_inv_raw = pd.read_csv(path_inv, low_memory=False)

# Cột chuẩn theo ERD (loại bỏ product_name, category, segment, flags, year, month)
inv_erd_cols = ['snapshot_date', 'product_id', 'stock_on_hand', 'units_received', 'units_sold', 'stockout_days', 'sell_through_rate', 'fill_rate', 'days_of_supply']
df_inv_silver = df_inv_raw[[c for c in inv_erd_cols if c in df_inv_raw.columns]]
df_inv_silver = apply_cleaning_rules(df_inv_silver, numeric_exclude_cols=['product_id'])
df_inv_silver.to_csv(os.path.join(OUTPUT_DIR, 'inventory_silver.csv'), index=False)
print(f"[OK] INVENTORY: {df_inv_silver.shape[0]:,} dòng x {df_inv_silver.shape[1]} cột -> inventory_silver.csv")

# -------------------------------------------------------------
# BẢNG 4: RETURNS
# -------------------------------------------------------------
path_returns = os.path.join(INPUT_DIR, 'returns.csv')
returns_erd_cols = ['return_id', 'order_id', 'product_id', 'return_quantity', 'return_date', 'return_reason', 'refund_amount']

if os.path.exists(path_returns):
    df_ret_raw = pd.read_csv(path_returns, low_memory=False)
    # Nếu file returns có sẵn các cột của ERD thì chọn đúng cột
    available_cols = [c for c in returns_erd_cols if c in df_ret_raw.columns]
    if len(available_cols) >= 3:
        df_returns_silver = df_ret_raw[available_cols]
    else:
        df_returns_silver = df_ret_raw
else:
    # Dự phòng: Nếu file returns rỗng hoặc chưa tạo, trích xuất tự động từ các đơn hàng có status = 'returned'
    df_items = pd.read_csv(os.path.join(INPUT_DIR, 'order_items_clean.csv'), low_memory=False)
    df_ship = pd.read_csv(os.path.join(INPUT_DIR, 'shipments.csv'), low_memory=False)
    
    ret_orders = df_orders_raw[df_orders_raw['order_status'] == 'returned'][['order_id', 'order_date']]
    merged_ret = df_items.merge(ret_orders, on='order_id', how='inner')
    merged_ret = merged_ret.merge(df_ship[['order_id', 'delivery_date']], on='order_id', how='left')
    
    merged_ret['return_id'] = range(1, len(merged_ret) + 1)
    merged_ret['return_quantity'] = merged_ret['quantity']
    merged_ret['return_date'] = pd.to_datetime(merged_ret['delivery_date']).fillna(pd.to_datetime(merged_ret['order_date'])).dt.strftime('%Y-%m-%d')
    merged_ret['return_reason'] = 'Sản phẩm lỗi hoặc không phù hợp'
    merged_ret['refund_amount'] = (merged_ret['quantity'] * merged_ret['unit_price'] - merged_ret['discount_amount']).round(2)
    df_returns_silver = merged_ret[returns_erd_cols]

df_returns_silver = apply_cleaning_rules(df_returns_silver, numeric_exclude_cols=['return_id', 'order_id', 'product_id'])
df_returns_silver.to_csv(os.path.join(OUTPUT_DIR, 'returns_silver.csv'), index=False)
print(f"[OK] RETURNS: {df_returns_silver.shape[0]:,} dòng x {df_returns_silver.shape[1]} cột -> returns_silver.csv")

# -------------------------------------------------------------
# BẢNG BỔ SUNG: ORDER_ITEMS (theo phân công của Khang)
# -------------------------------------------------------------
path_oi = os.path.join(INPUT_DIR, 'order_items_clean.csv')
if os.path.exists(path_oi):
    df_oi_raw = pd.read_csv(path_oi, low_memory=False)
    oi_erd_cols = ['order_id', 'product_id', 'quantity', 'unit_price', 'discount_amount']
    df_oi_silver = df_oi_raw[[c for c in oi_erd_cols if c in df_oi_raw.columns]]
    df_oi_silver = apply_cleaning_rules(df_oi_silver, numeric_exclude_cols=['order_id', 'product_id'])
    df_oi_silver.to_csv(os.path.join(OUTPUT_DIR, 'order_items_silver.csv'), index=False)
    print(f"[OK] ORDER_ITEMS: {df_oi_silver.shape[0]:,} dòng x {df_oi_silver.shape[1]} cột -> order_items_silver.csv")

# -------------------------------------------------------------
# XUẤT THÀNH 1 TỆP DUY NHẤT (FILE EXCEL ĐA SHEET HOẶC SQLITE)
# -------------------------------------------------------------
output_single_excel = os.path.join(OUTPUT_DIR, 'SILVER_DATABASE.xlsx')
print(f"\n--> Đang đóng gói 4 bảng vào 1 tệp duy nhất: {output_single_excel} ...")

# Lưu ý: Do bảng ORDERS có số dòng lớn, nếu file vượt giới hạn 1,048,576 dòng của Excel, 
# script sẽ tự động tạo thêm file SQLite .db cực kỳ nhẹ và chuẩn dữ liệu quan hệ.
with pd.ExcelWriter(output_single_excel, engine='openpyxl') as writer:
    # Lấy mẫu 100,000 dòng nếu xuất Excel hoặc lưu toàn bộ sang SQLite
    df_cust_silver.head(100000).to_excel(writer, sheet_name='CUSTOMERS', index=False)
    df_orders_silver.head(100000).to_excel(writer, sheet_name='ORDERS', index=False)
    df_inv_silver.head(100000).to_excel(writer, sheet_name='INVENTORY', index=False)
    df_returns_silver.head(100000).to_excel(writer, sheet_name='RETURNS', index=False)

import sqlite3
output_sqlite = os.path.join(OUTPUT_DIR, 'silver_database.db')
conn = sqlite3.connect(output_sqlite)
df_cust_silver.to_sql('CUSTOMERS', conn, if_exists='replace', index=False)
df_orders_silver.to_sql('ORDERS', conn, if_exists='replace', index=False)
df_inv_silver.to_sql('INVENTORY', conn, if_exists='replace', index=False)
df_returns_silver.to_sql('RETURNS', conn, if_exists='replace', index=False)
conn.close()

print(f"[THÀNH CÔNG] Đã tạo tệp cơ sở dữ liệu tích hợp: {output_sqlite}")
print(f"[THÀNH CÔNG] Toàn bộ file Silver đã lưu tại thư mục: {OUTPUT_DIR}")