import pandas as pd
import os


# ============================================================
# 1. KHAI BÁO ĐƯỜNG DẪN
# ============================================================

# File PAYMENTS gốc
payments_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\payments.csv"

# File ORDERS gốc
orders_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\orders.csv"

# File PAYMENTS sau khi xử lý
output_file = r"D:\KÌ1_NĂM3\NHẬP MÔN PHÂN TÍCH DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO\payments_silver.csv"


# ============================================================
# 2. KIỂM TRA FILE PAYMENTS
# ============================================================

if not os.path.exists(payments_file):
    print("Không tìm thấy file payments.csv:")
    print(payments_file)
    exit()


# ============================================================
# 3. ĐỌC DỮ LIỆU PAYMENTS
# ============================================================

payments = pd.read_csv(payments_file)

print("==============================================")
print("ĐỌC DỮ LIỆU PAYMENTS")
print("==============================================")

print("Số dòng dữ liệu:", len(payments))

print("\nCác cột ban đầu:")
print(payments.columns.tolist())


# ============================================================
# 4. KIỂM TRA CÁC CỘT CẦN THIẾT
# ============================================================

required_columns = [
    "order_id",
    "payment_method",
    "payment_value",
    "installments"
]

for column in required_columns:

    if column not in payments.columns:

        print("\nThiếu cột:", column)
        print("Kiểm tra lại file payments.csv")
        exit()

print("\nPAYMENTS có đầy đủ các cột cần thiết.")


# ============================================================
# 5. CHỈ GIỮ CÁC CỘT THEO BẢNG 3NF
# ============================================================

payments = payments[
    [
        "order_id",
        "payment_method",
        "payment_value",
        "installments"
    ]
].copy()


# ============================================================
# 6. CHUYỂN Ô RỖNG THÀNH NULL
# ============================================================

# Các ô chứa chuỗi rỗng hoặc chỉ có khoảng trắng
# sẽ được chuyển thành NaN.
payments = payments.replace(
    r"^\s*$",
    pd.NA,
    regex=True
)


# ============================================================
# 7. CHUYỂN KIỂU DỮ LIỆU
# ============================================================

payments["order_id"] = pd.to_numeric(
    payments["order_id"],
    errors="coerce"
)

payments["payment_value"] = pd.to_numeric(
    payments["payment_value"],
    errors="coerce"
)

payments["installments"] = pd.to_numeric(
    payments["installments"],
    errors="coerce"
)


# ============================================================
# 8. KIỂM TRA NULL TRƯỚC KHI LẤP ĐẦY
# ============================================================

print("\n==============================================")
print("KIỂM TRA NULL TRƯỚC KHI XỬ LÝ")
print("==============================================")

print(payments.isnull().sum())


# ============================================================
# 9. TẠO PAYMENT_ID TĂNG DẦN
# ============================================================

# payment_id bắt đầu từ 1.
#
# Ví dụ:
# dòng đầu tiên  -> 1
# dòng thứ hai   -> 2
# dòng thứ ba    -> 3
# ...

payments.insert(
    0,
    "payment_id",
    range(1, len(payments) + 1)
)

print("\nĐã tạo payment_id tăng dần.")


# ============================================================
# 10. XỬ LÝ PAYMENT_METHOD BỊ NULL
# ============================================================

# Nếu payment_method bị thiếu,
# sử dụng phương thức xuất hiện nhiều nhất.

if payments["payment_method"].isnull().sum() > 0:

    mode_payment_method = payments[
        "payment_method"
    ].mode()

    if len(mode_payment_method) > 0:

        payments["payment_method"] = payments[
            "payment_method"
        ].fillna(mode_payment_method.iloc[0])

        print(
            "\nĐã bổ sung payment_method bị thiếu bằng:",
            mode_payment_method.iloc[0]
        )

    else:

        print(
            "\nKhông tìm được giá trị phổ biến "
            "để bổ sung payment_method."
        )


# ============================================================
# 11. XỬ LÝ PAYMENT_VALUE BỊ NULL
# ============================================================

# Nếu payment_value bị thiếu,
# sử dụng giá trị trung vị (median).

if payments["payment_value"].isnull().sum() > 0:

    median_payment_value = payments[
        "payment_value"
    ].median()

    payments["payment_value"] = payments[
        "payment_value"
    ].fillna(median_payment_value)

    print(
        "\nĐã bổ sung payment_value bị thiếu bằng median:",
        median_payment_value
    )


# ============================================================
# 12. XỬ LÝ INSTALLMENTS BỊ NULL
# ============================================================

# Nếu installments bị thiếu,
# sử dụng giá trị xuất hiện nhiều nhất.

if payments["installments"].isnull().sum() > 0:

    mode_installments = payments[
        "installments"
    ].mode()

    if len(mode_installments) > 0:

        payments["installments"] = payments[
            "installments"
        ].fillna(mode_installments.iloc[0])

        print(
            "\nĐã bổ sung installments bị thiếu bằng:",
            mode_installments.iloc[0]
        )

    else:

        print(
            "\nKhông tìm được giá trị phổ biến "
            "để bổ sung installments."
        )


# ============================================================
# 13. KIỂM TRA ORDER_ID
# ============================================================

print("\n==============================================")
print("KIỂM TRA KHÓA NGOẠI ORDER_ID")
print("==============================================")


# Kiểm tra order_id bị NULL
null_order_id = payments["order_id"].isnull().sum()

print("Số order_id bị NULL:", null_order_id)


if null_order_id > 0:

    print("\nCẢNH BÁO:")
    print("Có order_id bị thiếu.")
    print("Không tự ý tạo order_id mới.")
    print("Cần xử lý tại bảng ORDERS.")

else:

    print("Không có order_id bị NULL.")


# ============================================================
# 14. ĐỌC ORDERS ĐỂ KIỂM TRA FOREIGN KEY
# ============================================================

if os.path.exists(orders_file):

    orders = pd.read_csv(orders_file)

    print("\nĐã đọc orders.csv để kiểm tra FK.")

    if "order_id" not in orders.columns:

        print("orders.csv không có cột order_id.")
        print("Không thể kiểm tra FK.")

    else:

        # Chuyển order_id của ORDERS về kiểu số
        orders["order_id"] = pd.to_numeric(
            orders["order_id"],
            errors="coerce"
        )

        # Lấy danh sách order_id tồn tại trong ORDERS
        order_ids = orders["order_id"].dropna().unique()

        # Tìm order_id của PAYMENTS nhưng không có trong ORDERS
        invalid_orders = payments[
            payments["order_id"].notna()
            & ~payments["order_id"].isin(order_ids)
        ]

        print(
            "Số payment có order_id không tồn tại trong ORDERS:",
            len(invalid_orders)
        )

        if len(invalid_orders) > 0:

            print("\nCác order_id chưa tồn tại trong ORDERS:")

            print(
                invalid_orders[
                    ["payment_id", "order_id"]
                ]
            )

            print(
                "\n=> Cần kiểm tra và bổ sung ORDER hợp lệ "
                "ở bảng ORDERS."
            )

        else:

            print(
                "Tất cả order_id của PAYMENTS "
                "đều tồn tại trong ORDERS."
            )

else:

    print("\nKhông tìm thấy orders.csv.")
    print("Bỏ qua bước kiểm tra Foreign Key.")


# ============================================================
# 15. KIỂM TRA PAYMENT_ID
# ============================================================

print("\n==============================================")
print("KIỂM TRA PAYMENT_ID")
print("==============================================")

total_rows = len(payments)

unique_payment_ids = payments[
    "payment_id"
].nunique()

print("Tổng số dòng:", total_rows)

print(
    "Số payment_id khác nhau:",
    unique_payment_ids
)

if total_rows == unique_payment_ids:

    print("payment_id không bị trùng.")

else:

    print("CẢNH BÁO: payment_id bị trùng.")


# ============================================================
# 16. KIỂM TRA PAYMENT_METHOD
# ============================================================

print("\n==============================================")
print("KIỂM TRA PAYMENT_METHOD")
print("==============================================")

print(
    payments["payment_method"].value_counts(
        dropna=False
    )
)


# ============================================================
# 17. KIỂM TRA PAYMENT_VALUE
# ============================================================

print("\n==============================================")
print("KIỂM TRA PAYMENT_VALUE")
print("==============================================")

negative_values = (
    payments["payment_value"] < 0
).sum()

print(
    "Số payment_value < 0:",
    negative_values
)

if negative_values == 0:

    print("payment_value hợp lệ.")

else:

    print(
        "CẢNH BÁO: Có payment_value âm."
    )


# ============================================================
# 18. KIỂM TRA INSTALLMENTS
# ============================================================

print("\n==============================================")
print("KIỂM TRA INSTALLMENTS")
print("==============================================")

invalid_installments = (
    payments["installments"] < 1
).sum()

print(
    "Số installments < 1:",
    invalid_installments
)

if invalid_installments == 0:

    print("installments hợp lệ.")

else:

    print(
        "CẢNH BÁO: Có installments < 1."
    )


# ============================================================
# 19. KIỂM TRA NULL SAU KHI LẤP ĐẦY
# ============================================================

print("\n==============================================")
print("NULL SAU KHI LẤP ĐẦY")
print("==============================================")

null_result = payments.isnull().sum()

print(null_result)


# ============================================================
# 20. KIỂM TRA CÁC DÒNG VẪN CÒN NULL
# ============================================================

remaining_null_rows = payments[
    payments.isnull().any(axis=1)
]

print(
    "\nSố dòng vẫn còn NULL:",
    len(remaining_null_rows)
)

if len(remaining_null_rows) > 0:

    print("\nCác dòng còn NULL:")

    print(remaining_null_rows)

else:

    print("Không còn dòng nào chứa NULL.")


# ============================================================
# 21. LÀM TRÒN PAYMENT_VALUE
# ============================================================

# payment_value là DECIMAL(18,2)
# nên giữ tối đa 2 chữ số sau dấu thập phân.

payments["payment_value"] = payments[
    "payment_value"
].round(2)


# ============================================================
# 22. CHUYỂN INSTALLMENTS SANG INT
# ============================================================

if payments["installments"].isnull().sum() == 0:

    payments["installments"] = payments[
        "installments"
    ].astype(int)


# ============================================================
# 23. SẮP XẾP THEO PAYMENT_ID
# ============================================================

payments = payments.sort_values(
    by="payment_id"
).reset_index(drop=True)


# ============================================================
# 24. XUẤT FILE SILVER
# ============================================================

payments.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 25. HIỂN THỊ KẾT QUẢ CUỐI CÙNG
# ============================================================

print("\n==============================================")
print("HOÀN THÀNH PAYMENTS SILVER")
print("==============================================")

print("\nFile Silver:")
print(output_file)

print("\nCấu trúc bảng PAYMENTS:")

print(
    payments.columns.tolist()
)

print(
    "\nTổng số dòng:",
    len(payments)
)

print("\n5 dòng đầu tiên:")

print(
    payments.head()
)

print("\n5 dòng cuối cùng:")

print(
    payments.tail()
)

print("\nKiểm tra NULL lần cuối:")

print(
    payments.isnull().sum()
)

print("\n==============================================")
print("ĐÃ XỬ LÝ XONG PAYMENTS")
print("==============================================")