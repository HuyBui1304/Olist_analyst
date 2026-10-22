"""Hằng số bố cục và màu dùng chung cho ảnh nền và report."""

PAGE_W, PAGE_H = 1600, 900

# Màu (lấy theo mẫu thiết kế)
BG = "#0E0E0E"
SIDEBAR = "#0B0B0B"
PANEL = "#1C1D1C"
LIME = "#C2FA5C"
TEXT = "#F2F2F2"
MUTED = "#A6A6A6"
SUBTLE = "#8C8C8C"
GRID = "#2E2F2E"
RED = "#F26F6F"
AMBER = "#F7B531"
CYAN = "#5CC8FA"
WHITE_SERIES = "#E6E6E6"

# Sidebar & menu: (nhãn, glyph Segoe Fluent Icons, id trang)
SIDEBAR_W = 236
NAV_Y, NAV_STEP, NAV_H = 136, 62, 48
NAV = [
    ("Overview", "\ue9d2", "overview"),
    ("Delivery", "\ue806", "delivery"),
    ("Customer Experience", "\ue734", "experience"),
    ("Sellers", "\ue719", "sellers"),
    ("Products", "\uf158", "products"),
    ("Customers", "\ue716", "customers"),
    ("Payments", "\ue8c7", "payments"),
]

# Vùng nội dung
CX, CW = 260, 1320
KPI_Y, KPI_H, KPI_W, KPI_GAP = 116, 136, 252, 15
KPI_X = [CX + k * (KPI_W + KPI_GAP) for k in range(5)]

ROW2_Y, ROW2_H = 268, 316
ROW3_Y, ROW3_H = 600, 270
L2 = (CX, ROW2_Y, 872, ROW2_H)
R2 = (CX + 888, ROW2_Y, 432, ROW2_H)
L3 = (CX, ROW3_Y, 652, ROW3_H)
R3 = (CX + 668, ROW3_Y, 652, ROW3_H)
