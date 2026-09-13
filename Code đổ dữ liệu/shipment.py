import pandas as pd
import os


# ============================================================
# 1. KHAI BÁO ĐƯỜNG DẪN
# ============================================================

shipments_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\shipments_realistic.csv"
orders_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\orders.csv"
output_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\shipments_silver.csv"


# ============================================================
# 2. KIỂM TRA FILE SHIPMENTS
# ============================================================

if not os.path.exists(shipments_file):
    print("Không tìm thấy file shipments_realistic.csv:")
    print(shipments_file)
    exit()


# ============================================================
# 3. ĐỌC DỮ LIỆU SHIPMENTS
# ============================================================

shipments = pd.read_csv(shipments_file)

print("==============================================")
print("ĐỌC DỮ LIỆU SHIPMENTS")
print("==============================================")

print("Số dòng dữ liệu:", len(shipments))
print("\nCác cột ban đầu:")
print(shipments.columns.tolist())


# ============================================================
# 4. TỰ ĐỘNG TẠO SHIPMENT_ID NẾU CHƯA CÓ
# ============================================================

if "shipment_id" not in shipments.columns:
    shipments.insert(0, "shipment_id", range(1, len(shipments) + 1))
    print("\nFile gốc không có shipment_id -> Đã tự động tạo cột shipment_id tăng dần từ 1.")


# ============================================================
# 5. CHỈ GIỮ CÁC CỘT THEO 3NF / SCHEMA
# ============================================================

required_columns = [
    "shipment_id",
    "order_id",
    "shipper_id",
    "zip", # Nếu file gốc có cột zip, nếu không có bạn có thể bỏ qua dòng này hoặc kiểm tra lại
    "delivery_date",
    "ship_date"
]

# Kiểm tra xem các cột cần thiết có đầy đủ không (ngoại trừ zip nếu file không có)
for column in ["shipment_id", "order_id", "shipper_id", "delivery_date", "ship_date"]:
    if column not in shipments.columns:
        print(f"\nThiếu cột bắt buộc: {column}")
        exit()

# Lọc các cột phục vụ cho bảng shipments chuẩn 3NF
# (Lưu ý: Nếu file của bạn không có cột 'zip', hãy lược bỏ 'zip' khỏi danh sách dưới đây)
available_columns = [col for col in ["shipment_id", "order_id", "shipper_id", "zip", "delivery_date", "ship_date"] if col in shipments.columns]

shipments = shipments[available_columns].copy()


# ============================================================
# 6. CHUYỂN Ô RỖNG THÀNH NULL
# ============================================================

shipments = shipments.replace(
    r"^\s*$",
    pd.NA,
    regex=True
)


# ============================================================
# 7. CHUYỂN KIỂU DỮ LIỆU
# ============================================================

shipments["shipment_id"] = pd.to_numeric(shipments["shipment_id"], errors="coerce")
shipments["order_id"] = pd.to_numeric(shipments["order_id"], errors="coerce")

if "shipper_id" in shipments.columns:
    # Xử lý nếu shipper_id có dạng chuỗi (như SHP...) thì trích xuất số, ngược lại ép số trực tiếp
    if shipments["shipper_id"].dtype == object:
        shipments["shipper_id"] = shipments["shipper_id"].astype(str).str.extract(r'(\d+)')[0]
    shipments["shipper_id"] = pd.to_numeric(shipments["shipper_id"], errors="coerce")

if "zip" in shipments.columns:
    shipments["zip"] = shipments["zip"].astype(str).str.strip()
    shipments.loc[shipments["zip"].isin(["nan", "None", ""]), "zip"] = pd.NA

shipments["delivery_date"] = pd.to_datetime(shipments["delivery_date"], errors="coerce").dt.strftime('%Y-%m-%d')
shipments["ship_date"] = pd.to_datetime(shipments["ship_date"], errors="coerce").dt.strftime('%Y-%m-%d')


# ============================================================
# 8. XỬ LÝ NULL CHO CÁC KHÓA VÀ THUỘC TÍNH
# ============================================================

if shipments["shipper_id"].isnull().sum() > 0:
    mode_shipper = shipments["shipper_id"].mode()
    if len(mode_shipper) > 0:
        shipments["shipper_id"] = shipments["shipper_id"].fillna(mode_shipper.iloc[0])

if "zip" in shipments.columns and shipments["zip"].isnull().sum() > 0:
    mode_zip = shipments["zip"].mode()
    if len(mode_zip) > 0:
        shipments["zip"] = shipments["zip"].fillna(mode_zip.iloc[0])


# ============================================================
# 9. KIỂM TRA KHÓA NGOẠI ORDER_ID
# ============================================================

print("\n==============================================")
print("KIỂM TRA KHÓA NGOẠI ORDER_ID")
print("==============================================")

if os.path.exists(orders_file):
    orders = pd.read_csv(orders_file)
    if "order_id" in orders.columns:
        orders["order_id"] = pd.to_numeric(orders["order_id"], errors="coerce")
        valid_orders = orders["order_id"].dropna().unique()
        invalid_orders = shipments[shipments["order_id"].notna() & ~shipments["order_id"].isin(valid_orders)]
        print(f"Số shipment có order_id không tồn tại trong ORDERS: {len(invalid_orders)}")
    else:
        print("orders.csv không có cột order_id.")
else:
    print("Không tìm thấy orders.csv, bỏ qua kiểm tra order_id FK.")


# ============================================================
# 10. KIỂM TRA LOGIC NGÀY THÁNG
# ============================================================

print("\n==============================================")
print("KIỂM TRA LOGIC NGÀY THÁNG")
print("==============================================")

s_date = pd.to_datetime(shipments["ship_date"], errors="coerce")
d_date = pd.to_datetime(shipments["delivery_date"], errors="coerce")

invalid_dates = (s_date > d_date).sum()
print("Số dòng có ship_date lớn hơn delivery_date:", invalid_dates)


# ============================================================
# 11. ÉP KIỂU SỐ NGUYÊN HOÀN TẤT & XUẤT FILE SILVER
# ============================================================

if shipments["shipment_id"].isnull().sum() == 0:
    shipments["shipment_id"] = shipments["shipment_id"].astype(int)

if shipments["order_id"].isnull().sum() == 0:
    shipments["order_id"] = shipments["order_id"].astype(int)

if "shipper_id" in shipments.columns and shipments["shipper_id"].isnull().sum() == 0:
    shipments["shipper_id"] = shipments["shipper_id"].astype(int)

shipments = shipments.sort_values(by="shipment_id").reset_index(drop=True)

shipments.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print("\n==============================================")
print("HOÀN THÀNH SHIPMENTS SILVER")
print("==============================================")
print("File Silver đã lưu tại:", output_file)
print("Tổng số dòng:", len(shipments))