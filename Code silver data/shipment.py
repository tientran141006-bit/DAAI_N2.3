import os
import pandas as pd

# ============================================================
# 1. KHAI BÁO ĐƯỜNG DẪN
# ============================================================

shipments_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\shipments_realistic.csv"
orders_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\orders.csv"
output_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\shipments_silver.csv"


# ============================================================
# 2. KIỂM TRA VÀ ĐỌC FILE GỐC
# ============================================================

if not os.path.exists(shipments_file):
  print(f"Không tìm thấy file shipments tại đường dẫn: {shipments_file}")
  exit()

raw_df = pd.read_csv(shipments_file)

print("==============================================")
print("1. THÔNG TIN BAN ĐẦU CỦA FILE GỐC")
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
# Chuyển đổi khoảng trắng thành NA để kiểm tra chính xác
raw_df = raw_df.replace(r"^\s*$", pd.NA, regex=True)

# Hiển thị số lượng null trên từng cột của file gốc
null_summary = raw_df.isnull().sum()
print(null_summary)

print("\n==============================================")
print("3. TIẾN HÀNH XỬ LÝ LÀM SẠCH (XÓA DÒNG TRỐNG & TRÙNG LẶP)")
print("==============================================")

initial_row_count = len(raw_df)

# A. Xóa các dòng mà toàn bộ các cột đều là Null (trống hết)
raw_df = raw_df.dropna(how="all").reset_index(drop=True)
dropped_all_null = initial_row_count - len(raw_df)
print(f"- Số dòng bị xóa do tất cả các thuộc tính đều là NULL: {dropped_all_null}")

# B. Xóa các dòng bị trùng lặp hoàn toàn (giữ lại 1 dòng duy nhất)
before_dup_count = len(raw_df)
raw_df = raw_df.drop_duplicates().reset_index(drop=True)
dropped_duplicates = before_dup_count - len(raw_df)
print(f"- Số dòng trùng lặp hoàn toàn đã bị xóa: {dropped_duplicates}")
print(f"- Tổng số dòng còn lại sau khi làm sạch cơ bản: {len(raw_df)}")


# ============================================================
# 4. TRÍCH XUẤT CÁC CỘT THEO SCHEMA BẢNG SHIPMENTS
# ============================================================

shipments = pd.DataFrame()

# Tự động tạo khóa chính shipment_id tăng dần từ 1
shipments["shipment_id"] = range(1, len(raw_df) + 1)

# Lấy các cột tương ứng từ file gốc
shipments["order_id"] = raw_df["order_id"] if "order_id" in raw_df.columns else pd.NA
shipments["shipper_id"] = raw_df["shipper_id"] if "shipper_id" in raw_df.columns else pd.NA
shipments["delivery_date"] = raw_df["delivery_date"] if "delivery_date" in raw_df.columns else pd.NA
shipments["ship_date"] = raw_df["ship_date"] if "ship_date" in raw_df.columns else pd.NA
shipments["shipping_fee"] = raw_df["shipping_fee"] if "shipping_fee" in raw_df.columns else 0.0


# ============================================================
# 5. CHUYỂN ĐỔI KIỂU DỮ LIỆU & XỬ LÝ NULL SAU TRÍCH XUẤT
# ============================================================

shipments["shipment_id"] = pd.to_numeric(shipments["shipment_id"], errors="coerce").astype(int)
shipments["order_id"] = pd.to_numeric(shipments["order_id"], errors="coerce")
shipments["shipper_id"] = pd.to_numeric(shipments["shipper_id"], errors="coerce")
shipments["shipping_fee"] = pd.to_numeric(shipments["shipping_fee"], errors="coerce")

# Chuẩn hóa định dạng ngày tháng
shipments["delivery_date"] = pd.to_datetime(shipments["delivery_date"], errors="coerce").dt.strftime("%Y-%m-%d")
shipments["ship_date"] = pd.to_datetime(shipments["ship_date"], errors="coerce").dt.strftime("%Y-%m-%d")

# Điền giá trị Null cho các cột quan trọng nếu còn sót lại
if shipments["shipper_id"].isnull().sum() > 0:
  mode_shipper = shipments["shipper_id"].mode()
  if len(mode_shipper) > 0:
    shipments["shipper_id"] = shipments["shipper_id"].fillna(mode_shipper.iloc[0])

if shipments["shipping_fee"].isnull().sum() > 0:
  median_fee = shipments["shipping_fee"].median()
  shipments["shipping_fee"] = shipments["shipping_fee"].fillna(median_fee)


# ============================================================
# 6. KIỂM TRA KHÓA NGOẠI VÀ LOGIC NGÀY THÁNG
# ============================================================

print("\n==============================================")
print("4. KIỂM TRA RÀNG BUỘC KỸ THUẬT (KHÓA NGOẠI & NGÀY)")
print("==============================================")

# Kiểm tra khóa ngoại order_id với file orders.csv
if os.path.exists(orders_file):
  orders = pd.read_csv(orders_file)
  if "order_id" in orders.columns:
    orders["order_id"] = pd.to_numeric(orders["order_id"], errors="coerce")
    valid_orders = orders["order_id"].dropna().unique()
    invalid_orders_count = shipments[
        shipments["order_id"].notna() & ~shipments["order_id"].isin(valid_orders)
    ].shape[0]
    print(f"- Số lượng shipment có order_id KHÔNG tồn tại trong bảng ORDERS: {invalid_orders_count}")
  else:
    print("- File orders.csv không có cột order_id.")
else:
  print("- Không tìm thấy file orders.csv, bỏ qua kiểm tra khóa ngoại.")

# Kiểm tra logic ngày tháng (ship_date <= delivery_date)
s_date = pd.to_datetime(shipments["ship_date"], errors="coerce")
d_date = pd.to_datetime(shipments["delivery_date"], errors="coerce")
invalid_dates_count = (s_date > d_date).sum()
print(f"- Số dòng có ngày vận chuyển (ship_date) lớn hơn ngày giao (delivery_date): {invalid_dates_count}")


# ============================================================
# 7. HOÀN THIỆN VÀ XUẤT FILE SILVER
# ============================================================

shipments["order_id"] = shipments["order_id"].astype("Int64")
shipments["shipper_id"] = shipments["shipper_id"].astype("Int64")

shipments = shipments.sort_values(by="shipment_id").reset_index(drop=True)

shipments.to_csv(output_file, index=False, encoding="utf-8-sig")

print("\n==============================================")
print("5. HOÀN THÀNH XUẤT FILE SILVER")
print("==============================================")
print(f"Đường dẫn file kết quả: {output_file}")
print(f"Tổng số dòng ghi nhận cuối cùng trong bảng Shipments Silver: {len(shipments)}")