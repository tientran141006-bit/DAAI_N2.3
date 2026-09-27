import os
import numpy as np
import pandas as pd

# ==============================================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN TRÊN WINDOWS
# ==============================================================================
INPUT_DIR = r"D:\Khang\clean_file"
OUTPUT_DIR = r"D:\Khang\silver_file"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==============================================================================
# 2. HÀM XỬ LÝ LÀM SẠCH CHUẨN THEO ĐÚNG CÁC QUY TẮC
# ==============================================================================
def clean_and_impute(df, table_name, exclude_impute_cols=None):
  if exclude_impute_cols is None:
    exclude_impute_cols = []

  initial_shape = df.shape

  # 1. Chuẩn hóa chuỗi khoảng trắng và text rỗng về NaN
  df = df.replace(r"^\s*$", np.nan, regex=True)
  df = df.replace(
      ["unknown", "Unknown", "null", "NULL", "none", "None", "NA", "N/A"],
      np.nan,
  )

  # Quy tắc 1: Cả dòng đều null -> Xóa
  df = df.dropna(how="all")

  # Quy tắc 2: Cả dòng trùng lặp hoàn toàn -> Xóa
  df = df.drop_duplicates()

  # Quy tắc 3: Cột có tất cả các dòng đều null -> Xóa
  df = df.dropna(axis=1, how="all")

  # Quy tắc 4: Cột số có giá trị null -> Điền trung bình (mean)
  imputed_cols = []
  for col in df.columns:
    is_identifier = (
        col in exclude_impute_cols
        or col.lower().endswith("_id")
        or "date" in col.lower()
        or col.lower() in ["zip", "phone"]
    )
    if not is_identifier:
      numeric_col = pd.to_numeric(df[col], errors="coerce")
      if pd.api.types.is_numeric_dtype(df[col]) or (
          numeric_col.notna().sum() / len(df) > 0.5
      ):
        df[col] = numeric_col
        if df[col].isna().sum() > 0:
          mean_val = df[col].mean()
          df[col] = df[col].fillna(mean_val)
          imputed_cols.append(f"{col} (mean = {mean_val:,.2f})")

  print(f"[{table_name}]")
  print(
      f"  - Ban đầu: {initial_shape[0]:,} dòng x {initial_shape[1]} cột -> Sau"
      f" làm sạch: {df.shape[0]:,} dòng x {df.shape[1]} cột"
  )
  if imputed_cols:
    print(f"  - Cột số đã điền mean: {', '.join(imputed_cols)}")
  return df


# ==============================================================================
# 3. ĐỌC DỮ LIỆU VÀ CHUẨN HÓA BẢNG RETURNS THEO CHUẨN ERD
# ==============================================================================
returns_erd_cols = [
    "return_id",
    "order_id",
    "product_id",
    "return_quantity",
    "return_date",
    "return_reason",
    "refund_amount",
]

ret_file_path = os.path.join(INPUT_DIR, "returns.csv")

if os.path.exists(ret_file_path):
  print(f"--> Đang đọc dữ liệu từ file có sẵn: {ret_file_path}")
  df_ret_raw = pd.read_csv(ret_file_path, low_memory=False)
  matched = [c for c in returns_erd_cols if c in df_ret_raw.columns]

  if len(matched) == len(returns_erd_cols):
    df_returns = df_ret_raw[returns_erd_cols]
  else:
    df_returns = df_ret_raw
else:
  print("--> Chưa có sẵn file returns.csv. Tiến hành trích xuất từ dữ liệu:")
  print("    + orders.csv (lọc các đơn hàng trạng thái 'returned')")
  print("    + order_items_clean.csv (lấy product_id, quantity, giá bán)")
  print("    + shipments.csv (lấy delivery_date làm ngày phát sinh trả hàng)")

  # Đọc bảng orders
  df_orders = pd.read_csv(
      os.path.join(INPUT_DIR, "orders.csv"), low_memory=False
  )
  ret_orders = df_orders[df_orders["order_status"] == "returned"][
      ["order_id", "order_date"]
  ]

  # Đọc bảng order_items
  oi_file = (
      "order_items_clean.csv"
      if os.path.exists(os.path.join(INPUT_DIR, "order_items_clean.csv"))
      else "order_items.csv"
  )
  df_oi = pd.read_csv(os.path.join(INPUT_DIR, oi_file), low_memory=False)

  # Ghép đơn hàng bị hoàn trả với chi tiết mặt hàng
  merged_ret = df_oi.merge(ret_orders, on="order_id", how="inner")

  # Ghép thêm ngày giao hàng từ shipments nếu có
  ship_path = os.path.join(INPUT_DIR, "shipments.csv")
  if os.path.exists(ship_path):
    df_ship = pd.read_csv(ship_path, low_memory=False)
    merged_ret = merged_ret.merge(
        df_ship[["order_id", "delivery_date"]], on="order_id", how="left"
    )
    merged_ret["return_date"] = (
        pd.to_datetime(merged_ret["delivery_date"])
        .fillna(pd.to_datetime(merged_ret["order_date"]))
        .dt.strftime("%Y-%m-%d")
    )
  else:
    merged_ret["return_date"] = merged_ret["order_date"]

  # Tạo các trường dữ liệu theo đúng chuẩn ERD
  merged_ret = merged_ret.sort_values(by=["order_id", "product_id"]).reset_index(
      drop=True
  )
  merged_ret["return_id"] = range(1, len(merged_ret) + 1)
  merged_ret["return_quantity"] = merged_ret["quantity"]
  merged_ret["return_reason"] = "Sản phẩm lỗi hoặc không vừa size"
  merged_ret["refund_amount"] = (
      merged_ret["quantity"] * merged_ret["unit_price"]
      - merged_ret["discount_amount"]
  ).round(2)

  df_returns = merged_ret[returns_erd_cols]

# ==============================================================================
# 4. ÁP DỤNG QUY TẮC LÀM SẠCH VÀ LƯU FILE SILVER
# ==============================================================================
df_returns_silver = clean_and_impute(
    df_returns,
    table_name="RETURNS",
    exclude_impute_cols=["return_id", "order_id", "product_id"],
)

output_file = os.path.join(OUTPUT_DIR, "RETURNS_SILVER.csv")
df_returns_silver.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"\n--> ĐÃ LƯU THÀNH CÔNG BẢNG SILVER: {output_file}")