import os
import pandas as pd

# ============================================================
# 1. KHAI BÁO ĐƯỜNG DẪN
# ============================================================

payments_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\student_data\payments.csv"
orders_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\student_data\orders_enriched.csv"
output_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\student_data\payments_silver.csv"


# ============================================================
# 2. KIỂM TRA VÀ ĐỌC FILE GỐC
# ============================================================

if not os.path.exists(payments_file):
    print(f"Không tìm thấy file payments tại đường dẫn: {payments_file}")
    exit()

raw_df = pd.read_csv(payments_file)

print("==============================================")
print("1. THÔNG TIN BAN ĐẦU CỦA FILE GỐC PAYMENTS")
print("==============================================")
print(f"Tổng số dòng ban đầu: {len(raw_df)}")
print("Các cột có sẵn trong file gốc:")
print(raw_df.columns.tolist())


# ============================================================
# 3. KIỂM TRA NULL VÀ LÀM SẠCH (XÓA DÒNG TRỐNG & TRÙNG LẶP)
# ============================================================

print("\n==============================================")
print("2. KẾT QUẢ KIỂM TRA VÀ THỐNG KÊ DỮ LIỆU NULL (THIẾU)")
print("==============================================")

raw_df = raw_df.replace(r"^\s*$", pd.NA, regex=True)
print(raw_df.isnull().sum())

print("\n==============================================")
print("3. TIẾN HÀNH XỬ LÝ LÀM SẠCH (XÓA DÒNG TRỐNG & TRÙNG LẶP)")
print("==============================================")

initial_row_count = len(raw_df)

raw_df = raw_df.dropna(how="all").reset_index(drop=True)
dropped_all_null = initial_row_count - len(raw_df)
print(f"- Số dòng bị xóa do tất cả các thuộc tính đều là NULL: {dropped_all_null}")

before_dup_count = len(raw_df)
raw_df = raw_df.drop_duplicates().reset_index(drop=True)
dropped_duplicates = before_dup_count - len(raw_df)
print(f"- Số dòng trùng lặp hoàn toàn đã bị xóa: {dropped_duplicates}")
print(f"- Tổng số dòng còn lại sau khi làm sạch cơ bản: {len(raw_df)}")


# ============================================================
# 4. TRÍCH XUẤT VÀ TẠO KHÓA CHÍNH TỰ TĂNG (PAYMENT_ID)
# ============================================================

payments = pd.DataFrame()

# payment_id là thuộc tính tự tăng (1, 2, 3,...)
payments["payment_id"] = range(1, len(raw_df) + 1)

# Ánh xạ chính xác các cột từ file gốc (hỗ trợ kiểm tra linh hoạt tên cột)
payments["order_id"] = raw_df["order_id"] if "order_id" in raw_df.columns else pd.NA

# Lấy cột phương thức thanh toán (ưu tiên payment_method, sau đó đến payment_type)
if "payment_method" in raw_df.columns:
    payments["payment_method"] = raw_df["payment_method"]
elif "payment_type" in raw_df.columns:
    payments["payment_method"] = raw_df["payment_type"]
else:
    payments["payment_method"] = pd.NA

payments["payment_value"] = raw_df["payment_value"] if "payment_value" in raw_df.columns else 0.0

# Lấy cột số kỳ trả góp (ưu tiên installments, sau đó đến payment_installments)
if "installments" in raw_df.columns:
    payments["installments"] = raw_df["installments"]
elif "payment_installments" in raw_df.columns:
    payments["installments"] = raw_df["payment_installments"]
else:
    payments["installments"] = 1


# ============================================================
# 5. CHUYỂN ĐỔI KIỂU DỮ LIỆU & XỬ LÝ NULL SAU TRÍCH XUẤT
# ============================================================

payments["payment_id"] = pd.to_numeric(payments["payment_id"], errors="coerce").astype(int)
payments["order_id"] = pd.to_numeric(payments["order_id"], errors="coerce")
payments["payment_value"] = pd.to_numeric(payments["payment_value"], errors="coerce")
payments["installments"] = pd.to_numeric(payments["installments"], errors="coerce")

# Chuẩn hóa kiểu chuỗi cho payment_method
payments["payment_method"] = payments["payment_method"].astype(str).str.strip()
payments.loc[payments["payment_method"].isin(["nan", "None", ""]), "payment_method"] = pd.NA

# Điền giá trị mặc định / trung vị nếu có Null
if payments["payment_method"].isnull().sum() > 0:
    mode_method = payments["payment_method"].mode()
    if len(mode_method) > 0:
        payments["payment_method"] = payments["payment_method"].fillna(mode_method.iloc[0])

if payments["installments"].isnull().sum() > 0:
    median_inst = payments["installments"].median()
    payments["installments"] = payments["installments"].fillna(median_inst)

if payments["payment_value"].isnull().sum() > 0:
    median_val = payments["payment_value"].median()
    payments["payment_value"] = payments["payment_value"].fillna(median_val)


# ============================================================
# 6. KIỂM TRA RÀNG BUỘC KỸ THUẬT (KHÓA NGOẠI & GIÁ TRỊ)
# ============================================================

print("\n==============================================")
print("4. KIỂM TRA RÀNG BUỘC KỸ THUẬT (KHÓA NGOẠI & GIÁ TRỊ)")
print("==============================================")

# Kiểm tra khóa ngoại order_id với file orders_enriched.csv
if os.path.exists(orders_file):
    orders = pd.read_csv(orders_file)
    if "order_id" in orders.columns:
        orders["order_id"] = pd.to_numeric(orders["order_id"], errors="coerce")
        valid_orders = orders["order_id"].dropna().unique()
        invalid_orders_count = payments[
            payments["order_id"].notna() & ~payments["order_id"].isin(valid_orders)
        ].shape[0]
        print(f"- Số lượng payment có order_id KHÔNG tồn tại trong bảng ORDERS: {invalid_orders_count}")
    else:
        print("- File orders_enriched.csv không có cột order_id.")
else:
    print("- Không tìm thấy file orders_enriched.csv, bỏ qua kiểm tra khóa ngoại.")

# Kiểm tra giá trị thanh toán âm
negative_values = (payments["payment_value"] < 0).sum()
print(f"- Số lượng dòng có payment_value âm (< 0): {negative_values}")


# ============================================================
# 7. HOÀN THIỆN VÀ XUẤT FILE SILVER
# ============================================================

payments["order_id"] = payments["order_id"].astype("Int64")
payments["installments"] = payments["installments"].astype("Int64")
payments["payment_value"] = payments["payment_value"].round(2)

payments = payments.sort_values(by="payment_id").reset_index(drop=True)

payments.to_csv(output_file, index=False, encoding="utf-8-sig")

print("\n==============================================")
print("5. HOÀN THÀNH XUẤT FILE SILVER")
print("==============================================")
print(f"Đường dẫn file kết quả: {output_file}")
print(f"Tổng số dòng ghi nhận cuối cùng trong bảng Payments Silver: {len(payments)}")
print("\nXem trước 5 dòng đầu tiên của kết quả:")
print(payments.head())