import os
import pandas as pd
import numpy as np

# Cấu hình đường dẫn
INPUT_DIR = r"D:\Khang\clean_file"
OUTPUT_DIR = r"D:\Khang\silver_file"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clean_and_impute(df, table_name, exclude_impute_cols=None):
    if exclude_impute_cols is None:
        exclude_impute_cols = []

    initial_shape = df.shape

    # Chuẩn hóa chuỗi khoảng trắng và text rỗng về NaN
    df = df.replace(r"^\s*$", np.nan, regex=True)
    df = df.replace(
        ["unknown", "Unknown", "null", "NULL", "none", "None", "NA", "N/A"],
        np.nan,
    )

    # 1. Cả dòng đều null -> Xóa
    df = df.dropna(how="all")

    # 2. Cả dòng trùng lặp hoàn toàn -> Xóa
    df = df.drop_duplicates()

    # 3. Cột có tất cả các dòng đều null -> Xóa
    df = df.dropna(axis=1, how="all")

    # 4. Cột số có giá trị null -> Điền trung bình (mean)
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
        f"  - Ban đầu: {initial_shape[0]:,} dòng x {initial_shape[1]} cột -> Sau làm sạch: {df.shape[0]:,} dòng x {df.shape[1]} cột"
    )
    if imputed_cols:
        print(f"  - Cột số đã điền mean: {', '.join(imputed_cols)}")
    return df


# Đọc và chuẩn hóa dữ liệu ORDER_ITEMS
oi_file = (
    "order_items_clean.csv"
    if os.path.exists(os.path.join(INPUT_DIR, "order_items_clean.csv"))
    else "order_items.csv"
)
oi_path = os.path.join(INPUT_DIR, oi_file)
df_oi_raw = pd.read_csv(oi_path, low_memory=False)

# 3NF: Loại bỏ promo_id vì tách sang bảng ORDER_ITEMS_PROMOTION
oi_erd_cols = [
    "order_id",
    "product_id",
    "quantity",
    "unit_price",
    "discount_amount",
]
df_oi_silver = df_oi_raw[[c for c in oi_erd_cols if c in df_oi_raw.columns]]
df_oi_silver = clean_and_impute(
    df_oi_silver, "ORDER_ITEMS", exclude_impute_cols=["order_id", "product_id"]
)

output_file = os.path.join(OUTPUT_DIR, "ORDER_ITEMS_SILVER.csv")
df_oi_silver.to_csv(output_file, index=False, encoding="utf-8-sig")
print(f"--> Đã lưu thành công: {output_file}")