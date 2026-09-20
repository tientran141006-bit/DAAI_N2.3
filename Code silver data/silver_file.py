import os
import pandas as pd
import numpy as np

# 1. Thiết lập thư mục nguồn và thư mục đích
INPUT_DIR = './clean_file'
OUTPUT_DIR = './silver'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Hàm áp dụng đúng bộ quy tắc làm sạch dữ liệu
def clean_and_impute(df, table_name, exclude_impute_cols=None):
    if exclude_impute_cols is None:
        exclude_impute_cols = []

    initial_shape = df.shape

    # Chuẩn hóa khoảng trắng và các giá trị text null về NaN
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df = df.replace(['unknown', 'Unknown', 'null', 'NULL', 'none', 'None', 'NA', 'N/A'], np.nan)

    # Quy tắc 1: Cả 1 dòng đều null -> Xóa
    df = df.dropna(how='all')

    # Quy tắc 2: Cả 1 dòng đều trùng lặp với dòng khác -> Xóa
    df = df.drop_duplicates()

    # Quy tắc 3: Cột có tất cả các dòng đều null -> Xóa
    df = df.dropna(axis=1, how='all')

    # Quy tắc 4: Cột số có giá trị null -> Tính trung bình (mean) -> Thay vào
    imputed = []
    for col in df.columns:
        is_identifier = col in exclude_impute_cols or col.lower().endswith('_id') or 'date' in col.lower() or col.lower() == 'zip'
        if not is_identifier:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            if pd.api.types.is_numeric_dtype(df[col]) or (numeric_col.notna().sum() / len(df) > 0.5):
                df[col] = numeric_col
                if df[col].isna().sum() > 0:
                    mean_val = df[col].mean()
                    df[col] = df[col].fillna(mean_val)
                    imputed.append(col)

    print(f"[{table_name}] Gốc: {initial_shape[0]:,} dòng x {initial_shape[1]} cột -> Sau làm sạch: {df.shape[0]:,} dòng x {df.shape[1]} cột")
    if imputed:
        print(f" -> Các cột số được điền giá trị mean: {', '.join(imputed)}")
    return df

print("=== BẮT ĐẦU ĐỔ DỮ LIỆU SANG 4 BẢNG SILVER ===\n")

# =============================================================
# 1. BẢNG ORDERS
# =============================================================
df_orders_raw = pd.read_csv(os.path.join(INPUT_DIR, 'orders.csv'), low_memory=False)
orders_erd_cols = [
    'order_id', 'customer_id', 'order_date', 'order_status',
    'order_source', 'device_type', 'zip', 'sales_employee_id', 'comment'
]
df_orders_silver = df_orders_raw[[c for c in orders_erd_cols if c in df_orders_raw.columns]]
df_orders_silver = clean_and_impute(
    df_orders_silver,
    table_name='ORDERS',
    exclude_impute_cols=['order_id', 'customer_id', 'zip', 'sales_employee_id']
)
df_orders_silver.to_csv(os.path.join(OUTPUT_DIR, 'ORDERS_SILVER.csv'), index=False,encoding ='utf-8-sig')


# =============================================================
# 2. BẢNG INVENTORY
# =============================================================
# Lấy file inventory sạch từ thư mục cleanfile
inv_file_name = 'inventory_clean.csv' if os.path.exists(os.path.join(INPUT_DIR, 'inventory_clean.csv')) else 'inventory.csv'
df_inv_raw = pd.read_csv(os.path.join(INPUT_DIR, inv_file_name), low_memory=False, encoding ='utf-8-sig')
inv_erd_cols = [
    'snapshot_date', 'product_id', 'stock_on_hand', 'units_received',
    'units_sold', 'stockout_days', 'sell_through_rate', 'fill_rate', 'days_of_supply'
]
df_inv_silver = df_inv_raw[[c for c in inv_erd_cols if c in df_inv_raw.columns]]
df_inv_silver = clean_and_impute(
    df_inv_silver,
    table_name='INVENTORY',
    exclude_impute_cols=['product_id']
)
df_inv_silver.to_csv(os.path.join(OUTPUT_DIR, 'INVENTORY_SILVER.csv'), index=False, encoding ='utf-8-sig')


# =============================================================
# 3. BẢNG ORDER_ITEMS
# =============================================================
oi_file_name = 'order_items_clean.csv' if os.path.exists(os.path.join(INPUT_DIR, 'order_items_clean.csv')) else 'order_items.csv'
df_oi_raw = pd.read_csv(os.path.join(INPUT_DIR, oi_file_name), low_memory=False)
oi_erd_cols = ['order_id', 'product_id', 'quantity', 'unit_price', 'discount_amount']
df_oi_silver = df_oi_raw[[c for c in oi_erd_cols if c in df_oi_raw.columns]]
df_oi_silver = clean_and_impute(
    df_oi_silver,
    table_name='ORDER_ITEMS',
    exclude_impute_cols=['order_id', 'product_id']
)
df_oi_silver.to_csv(os.path.join(OUTPUT_DIR, 'ORDER_ITEMS_SILVER.csv'), index=False, encoding ='utf-8-sig')


# =============================================================
# 4. BẢNG RETURNS
# =============================================================
ret_file_path = os.path.join(INPUT_DIR, 'returns.csv')
returns_erd_cols = [
    'return_id', 'order_id', 'product_id', 'return_quantity',
    'return_date', 'return_reason', 'refund_amount'
]

if os.path.exists(ret_file_path):
    df_ret_raw = pd.read_csv(ret_file_path, low_memory=False)
    # Kiểm tra xem file returns.csv đã có sẵn các cột chuẩn theo ERD chưa
    matched_cols = [c for c in returns_erd_cols if c in df_ret_raw.columns]
    if len(matched_cols) == len(returns_erd_cols):
        df_returns_silver = df_ret_raw[returns_erd_cols]
    else:
        df_returns_silver = df_ret_raw
else:
    # Nếu file returns.csv thiếu cột, tự động dựng từ các đơn hàng có trạng thái 'returned'
    ret_orders = df_orders_silver[df_orders_silver['order_status'] == 'returned'][['order_id', 'order_date']]
    merged_ret = df_oi_silver.merge(ret_orders, on='order_id', how='inner')

    # Ghép với delivery_date từ shipments nếu có để lấy ngày trả hàng
    if os.path.exists(os.path.join(INPUT_DIR, 'shipments.csv')):
        df_ship = pd.read_csv(os.path.join(INPUT_DIR, 'shipments.csv'), low_memory=False)
        merged_ret = merged_ret.merge(df_ship[['order_id', 'delivery_date']], on='order_id', how='left')
        merged_ret['return_date'] = pd.to_datetime(merged_ret['delivery_date']).fillna(pd.to_datetime(merged_ret['order_date'])).dt.strftime('%Y-%m-%d')
    else:
        merged_ret['return_date'] = merged_ret['order_date']

    merged_ret['return_id'] = range(1, len(merged_ret) + 1)
    merged_ret['return_quantity'] = merged_ret['quantity']
    merged_ret['return_reason'] = 'Sản phẩm lỗi hoặc không phù hợp'
    merged_ret['refund_amount'] = (merged_ret['quantity'] * merged_ret['unit_price'] - merged_ret['discount_amount']).round(2)
    df_returns_silver = merged_ret[returns_erd_cols]

df_returns_silver = clean_and_impute(
    df_returns_silver,
    table_name='RETURNS',
    exclude_impute_cols=['return_id', 'order_id', 'product_id']
)
df_returns_silver.to_csv(os.path.join(OUTPUT_DIR, 'RETURNS_SILVER.csv'), index=False, encoding ='utf-8-sig')

print("\n--> HOÀN TẤT TẠO 4 FILE SILVER TẠI THƯ MỤC:", OUTPUT_DIR)