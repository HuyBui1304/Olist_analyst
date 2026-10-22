"""Sinh semantic model (TMDL) cho dashboard Olist.

Bảng nạp từ data_model/*.csv qua tham số Power Query `DataFolder`.
Measure đặt trong bảng `_Measures`, chia display folder theo trang.
"""
import uuid

NS = uuid.UUID("6f1b8f8e-3c1a-4c55-9d43-0a7c2f3b9e11")


def tag(*parts):
    """lineageTag ổn định giữa các lần build."""
    return str(uuid.uuid5(NS, "/".join(parts)))


def q(name):
    """Đặt tên trong nháy đơn khi cần (TMDL)."""
    if name.replace("_", "").isalnum() and name.isascii() and not name[0].isdigit():
        return name
    return "'" + name.replace("'", "''") + "'"


# ----------------------------------------------------------------- bảng dữ liệu
# (tên cột, kiểu, tùy chọn). Kiểu: s=text, i=int, d=double, dt=date, ts=datetime
# Tùy chọn: h=ẩn, sort=<cột>, sum=tổng mặc định, key=khóa bảng ngày
TABLES = {
    "Orders": ("fact_orders.csv", [
        ("order_id", "s", "h"), ("customer_unique_id", "s", "h"), ("customer_state", "s", "h"),
        ("customer_city", "s", ""), ("order_status", "s", ""), ("status_group", "s", "sort=status_sort"),
        ("status_sort", "i", "h"), ("purchase_date", "dt", "h"), ("purchase_ts", "ts", ""),
        ("approved_ts", "ts", "h"), ("carrier_ts", "ts", "h"), ("delivered_ts", "ts", ""),
        ("estimated_date", "dt", ""), ("is_delivered", "i", "h"), ("is_canceled", "i", "h"),
        ("n_items", "i", ""), ("n_products", "i", "h"), ("n_sellers", "i", "h"),
        ("items_value", "d", "sum"), ("freight_value", "d", "sum"), ("order_value", "d", "sum"),
        ("payment_value", "d", "sum"), ("payment_type_main", "s", ""), ("installments", "i", ""),
        ("installment_bucket", "s", "sort=installment_sort"), ("installment_sort", "i", "h"),
        ("uses_voucher", "i", "h"), ("review_score", "i", ""), ("review_label", "s", "sort=review_score"),
        ("has_review_comment", "i", "h"), ("review_sentiment", "s", ""), ("delivery_days", "d", ""),
        ("approval_hours", "d", ""), ("handling_days", "d", ""), ("transit_days", "d", ""),
        ("estimated_days", "d", ""), ("delay_days", "i", ""), ("is_late", "i", "h"),
        ("delivery_bucket", "s", "sort=delivery_bucket_sort"), ("delivery_bucket_sort", "i", "h"),
        ("delay_bucket", "s", "sort=delay_bucket_sort"), ("delay_bucket_sort", "i", "h"),
        ("purchase_hour", "i", ""), ("customer_order_seq", "i", ""), ("is_first_order", "i", "h"),
    ]),
    "OrderItems": ("fact_order_items.csv", [
        ("order_id", "s", "h"), ("order_item_id", "i", "h"), ("product_id", "s", "h"), ("seller_id", "s", "h"),
        ("shipping_limit_ts", "ts", ""), ("price", "d", "sum"), ("freight_value", "d", "sum"),
        ("item_value", "d", "sum"), ("seller_ship_late", "i", "h"),
    ]),
    "Payments": ("fact_payments.csv", [
        ("order_id", "s", "h"), ("payment_sequential", "i", "h"), ("payment_type", "s", ""),
        ("payment_installments", "i", ""), ("installments_bucket", "s", "sort=installments_sort"),
        ("installments_sort", "i", "h"), ("payment_value", "d", "sum"),
    ]),
    "Products": ("dim_product.csv", [
        ("product_id", "s", "h"), ("category", "s", ""), ("category_pt", "s", ""), ("photos_qty", "i", ""),
        ("photos_bucket", "s", "sort=photos_sort"), ("photos_sort", "i", "h"), ("weight_g", "d", ""),
        ("volume_cm3", "d", ""), ("description_length", "i", ""),
    ]),
    "Sellers": ("dim_seller.csv", [
        ("seller_id", "s", "h"), ("seller_code", "s", ""), ("seller_city", "s", ""), ("seller_state", "s", ""),
        ("seller_region", "s", ""), ("revenue_scope", "d", ""), ("revenue_tier", "s", "sort=revenue_tier_sort"),
        ("revenue_tier_sort", "i", "h"), ("first_sale_date", "dt", ""),
    ]),
    "Customers": ("dim_customer.csv", [
        ("customer_unique_id", "s", "h"), ("first_order_date", "dt", ""), ("n_orders", "i", ""),
        ("lifetime_value", "d", ""), ("order_count_group", "s", "sort=order_count_sort"),
        ("order_count_sort", "i", "h"), ("customer_type", "s", ""),
    ]),
    "States": ("dim_state.csv", [
        ("state", "s", ""), ("state_name", "s", ""), ("region", "s", "sort=region_sort"), ("region_sort", "i", "h"),
    ]),
    "Date": ("dim_date.csv", [
        ("Date", "dt", "key"), ("Year", "i", ""), ("Quarter", "s", ""), ("MonthNo", "i", "h"),
        ("Month", "s", "sort=MonthNo"), ("YearMonth", "s", "sort=YearMonthKey"), ("YearMonthKey", "i", "h"),
        ("MonthStart", "dt", ""), ("Weekday", "s", "sort=WeekdayNo"), ("WeekdayNo", "i", "h"),
    ]),
}

M_TYPE = {"s": "type text", "i": "Int64.Type", "d": "type number", "dt": "type date", "ts": "type datetime"}
TMDL_TYPE = {"s": "string", "i": "int64", "d": "double", "dt": "dateTime", "ts": "dateTime"}
FORMAT = {"i": "0", "d": "#,0.00", "dt": "dd/MM/yyyy", "ts": "dd/MM/yyyy HH:mm"}

RELATIONSHIPS = [
    # (từ bảng nhiều, cột, tới bảng một, cột, hai chiều?)
    ("Orders", "purchase_date", "Date", "Date", False),
    ("Orders", "customer_state", "States", "state", False),
    ("Orders", "customer_unique_id", "Customers", "customer_unique_id", False),
    ("OrderItems", "order_id", "Orders", "order_id", True),
    ("OrderItems", "product_id", "Products", "product_id", False),
    ("OrderItems", "seller_id", "Sellers", "seller_id", False),
    ("Payments", "order_id", "Orders", "order_id", False),
]

# ----------------------------------------------------------------- measure
# (tên, DAX, format, folder)
F_OV, F_DL, F_CX, F_SE, F_PR, F_CU, F_PA = (
    "1. Overview", "2. Delivery", "3. Customer Experience", "4. Sellers", "5. Products", "6. Customers",
    "7. Payments")
CUR0, CUR2, PCT, INT, DEC1, DEC2 = "R$ #,0", "R$ #,0.00", "0.0%", "#,0", "#,0.0", "0.00"
DELIVERED = "Orders[is_delivered] = 1"

MEASURES = [
    # Tổng quan
    ("Total Orders", "COUNTROWS(Orders)", INT, F_OV),
    ("Delivered Orders", f"CALCULATE(COUNTROWS(Orders), {DELIVERED})", INT, F_OV),
    ("Delivered Sales", f"CALCULATE(SUM(Orders[order_value]), {DELIVERED})", CUR0, F_OV),
    ("Avg Order Value", "DIVIDE([Delivered Sales], [Delivered Orders])", CUR2, F_OV),
    ("Canceled Orders", "CALCULATE(COUNTROWS(Orders), Orders[is_canceled] = 1)", INT, F_OV),
    ("Cancellation Rate", "DIVIDE([Canceled Orders], [Total Orders])", "0.00%", F_OV),
    ("Undelivered Orders", "CALCULATE(COUNTROWS(Orders), Orders[is_delivered] = 0)", INT, F_OV),
    ("Orders Canceled", "CALCULATE(COUNTROWS(Orders), Orders[order_status] = \"canceled\")", INT, F_OV),
    ("Orders Unavailable", "CALCULATE(COUNTROWS(Orders), Orders[order_status] = \"unavailable\")", INT, F_OV),
    ("Orders In Progress", "CALCULATE(COUNTROWS(Orders), Orders[status_sort] = 4)", INT, F_OV),
    ("Sales Share (State)",
     "DIVIDE([Delivered Sales], CALCULATE([Delivered Sales], REMOVEFILTERS(States)))", PCT, F_OV),
    # Giao hàng
    ("Avg Delivery Days", "AVERAGE(Orders[delivery_days])", DEC1, F_DL),
    ("Avg Estimated Days", f"CALCULATE(AVERAGE(Orders[estimated_days]), {DELIVERED})", DEC1, F_DL),
    ("Late Delivery Rate", "AVERAGE(Orders[is_late])", PCT, F_DL),
    ("On-Time Delivery Rate", "IF(NOT ISBLANK([Late Delivery Rate]), 1 - [Late Delivery Rate])", PCT, F_DL),
    ("Late Orders", "CALCULATE(COUNTROWS(Orders), Orders[is_late] = 1)", INT, F_DL),
    ("Avg Days Late", "CALCULATE(AVERAGE(Orders[delay_days]), Orders[is_late] = 1)", DEC1, F_DL),
    ("Avg Days Ahead of ETA", "-AVERAGE(Orders[delay_days])", DEC1, F_DL),
    ("Avg Approval Days", f"CALCULATE(AVERAGE(Orders[approval_hours]) / 24, {DELIVERED})", DEC1, F_DL),
    ("Avg Seller Handling Days", f"CALCULATE(AVERAGE(Orders[handling_days]), {DELIVERED})", DEC1, F_DL),
    ("Avg Carrier Transit Days", "AVERAGE(Orders[transit_days])", DEC1, F_DL),
    ("Freight-to-Value Ratio",
     f"DIVIDE(CALCULATE(SUM(Orders[freight_value]), {DELIVERED}), CALCULATE(SUM(Orders[items_value]), {DELIVERED}))",
     PCT, F_DL),
    ("Order Share (Delivery Time)",
     "VAR n = COUNT(Orders[delivery_days])\n"
     "RETURN IF(n > 0, DIVIDE(n, CALCULATE(COUNT(Orders[delivery_days]), REMOVEFILTERS(Orders[delivery_bucket], Orders[delivery_bucket_sort]))))",
     PCT, F_DL),
    ("Late Rate Color",
     'VAR r = [Late Delivery Rate] RETURN SWITCH(TRUE(), r >= 0.12, "#F26F6F", r >= 0.08, "#F7B531", "#C2FA5C")',
     "", F_DL),
    # Trải nghiệm khách hàng
    ("Avg Review Score", "AVERAGE(Orders[review_score])", DEC2, F_CX),
    ("Reviews", "COUNT(Orders[review_score])", INT, F_CX),
    ("5-Star Rate", "DIVIDE(CALCULATE([Reviews], Orders[review_score] = 5), [Reviews])", PCT, F_CX),
    ("Negative Review Rate", "DIVIDE(CALCULATE([Reviews], Orders[review_score] <= 2), [Reviews])", PCT, F_CX),
    ("Comment Rate", "DIVIDE(CALCULATE([Reviews], Orders[has_review_comment] = 1), [Reviews])", PCT, F_CX),
    ("Avg Score (Late Orders)", "CALCULATE([Avg Review Score], Orders[is_late] = 1)", DEC2, F_CX),
    ("Avg Score (On-Time Orders)", "CALCULATE([Avg Review Score], Orders[is_late] = 0)", DEC2, F_CX),
    ("Review Share",
     "IF([Reviews] > 0, DIVIDE([Reviews], CALCULATE([Reviews], REMOVEFILTERS(Orders[review_label], Orders[review_score]))))",
     PCT, F_CX),
    ("Avg Score (100+ Reviews)", "IF([Reviews] >= 100, [Avg Review Score])", DEC2, F_CX),
    ("Score Color",
     'VAR s = [Avg Review Score] RETURN SWITCH(TRUE(), ISBLANK(s), "#8C8C8C", s < 3, "#F26F6F", s < 4, "#F7B531", "#C2FA5C")',
     "", F_CX),
    ("Star Color",
     'VAR s = SELECTEDVALUE(Orders[review_score]) RETURN SWITCH(TRUE(), s <= 2, "#F26F6F", s = 3, "#F7B531", "#C2FA5C")',
     "", F_CX),
    # Người bán
    ("Item Sales", f"CALCULATE(SUM(OrderItems[item_value]), {DELIVERED})", CUR0, F_SE),
    ("Active Sellers", "DISTINCTCOUNT(OrderItems[seller_id])", INT, F_SE),
    ("New Sellers",
     "VAR _min = MIN('Date'[Date]) VAR _max = MAX('Date'[Date])\n"
     "RETURN CALCULATE([Active Sellers], KEEPFILTERS(FILTER(ALL(Sellers[first_sale_date]),\n"
     "    Sellers[first_sale_date] >= _min && Sellers[first_sale_date] <= _max)))", INT, F_SE),
    ("Sales per Seller", "DIVIDE([Item Sales], [Active Sellers])", CUR0, F_SE),
    ("Top 10% Seller Share",
     "VAR _s = ADDCOLUMNS(VALUES(OrderItems[seller_id]), \"@rev\", [Item Sales])\n"
     "VAR _k = ROUNDUP(COUNTROWS(_s) * 0.1, 0)\n"
     "RETURN DIVIDE(SUMX(TOPN(_k, _s, [@rev], DESC), [@rev]), SUMX(_s, [@rev]))", PCT, F_SE),
    ("Avg Seller Prep Days", "AVERAGE(Orders[handling_days])", DEC1, F_SE),
    ("Late Handover Rate", "AVERAGE(OrderItems[seller_ship_late])", PCT, F_SE),
    ("Sales Share (Seller)",
     "DIVIDE([Item Sales], CALCULATE([Item Sales], REMOVEFILTERS(Sellers)))", PCT, F_SE),
    ("Seller Count", "DISTINCTCOUNT(Sellers[seller_id])", INT, F_SE),
    # Sản phẩm
    ("Items Sold", f"CALCULATE(COUNTROWS(OrderItems), {DELIVERED})", INT, F_PR),
    ("Categories Sold",
     f"COUNTROWS(SUMMARIZE(CALCULATETABLE(OrderItems, {DELIVERED}), Products[category]))", INT, F_PR),
    ("Products Sold", f"CALCULATE(DISTINCTCOUNT(OrderItems[product_id]), {DELIVERED})", INT, F_PR),
    ("Avg Item Price", f"CALCULATE(AVERAGE(OrderItems[price]), {DELIVERED})", CUR2, F_PR),
    ("Freight-to-Price Ratio",
     f"DIVIDE(CALCULATE(SUM(OrderItems[freight_value]), {DELIVERED}), CALCULATE(SUM(OrderItems[price]), {DELIVERED}))",
     PCT, F_PR),
    ("Sales Share (Category)",
     "DIVIDE([Item Sales], CALCULATE([Item Sales], REMOVEFILTERS(Products)))", PCT, F_PR),
    # Khách hàng
    ("Total Customers", "DISTINCTCOUNT(Orders[customer_unique_id])", INT, F_CU),
    ("New Customers", "CALCULATE([Total Customers], Orders[is_first_order] = 1)", INT, F_CU),
    ("Returning Customers", "CALCULATE([Total Customers], Orders[customer_order_seq] > 1)", INT, F_CU),
    ("Returning Customer Rate", "DIVIDE([Returning Customers], [Total Customers])", "0.00%", F_CU),
    ("Orders per Customer", "DIVIDE([Total Orders], [Total Customers])", "0.000", F_CU),
    ("Sales per Customer", "DIVIDE([Delivered Sales], [Total Customers])", CUR2, F_CU),
    ("Customer Share",
     "DIVIDE([Total Customers], CALCULATE([Total Customers], REMOVEFILTERS(Customers[order_count_group], Customers[order_count_sort])))",
     "0.00%", F_CU),
    # Thanh toán
    ("Payment Value", "SUM(Payments[payment_value])", CUR0, F_PA),
    ("Payment Transactions", "COUNTROWS(Payments)", INT, F_PA),
    ("Payment Value Share",
     "DIVIDE([Payment Value], CALCULATE([Payment Value], REMOVEFILTERS(Payments[payment_type])))", PCT, F_PA),
    ("Credit Card Share",
     "DIVIDE(CALCULATE([Payment Value], Payments[payment_type] = \"Credit card\"), [Payment Value])", PCT, F_PA),
    ("Avg Installments",
     "CALCULATE(AVERAGE(Payments[payment_installments]), Payments[payment_type] = \"Credit card\")", DEC1, F_PA),
    ("Installment Order Rate", "DIVIDE(CALCULATE([Total Orders], Orders[installments] > 1), [Total Orders])", PCT, F_PA),
    ("Voucher Order Rate", "DIVIDE(CALCULATE([Total Orders], Orders[uses_voucher] = 1), [Total Orders])", PCT, F_PA),
    ("Credit Card Orders", "CALCULATE(DISTINCTCOUNT(Payments[order_id]), Payments[payment_type] = \"Credit card\")", INT, F_PA),
    ("Order Share (Installments)",
     "DIVIDE([Total Orders], CALCULATE([Total Orders], REMOVEFILTERS(Orders[installment_bucket], Orders[installment_sort])))",
     PCT, F_PA),
]

# KPI có dòng so sánh cùng kỳ: (measure, kiểu chênh lệch, cao hơn là tốt? – None = trung tính)
#   pct = % thay đổi; pp = chênh điểm phần trăm; day = chênh số ngày; pt = chênh điểm số
KPI_DELTAS = [
    ("Total Orders", "pct", True), ("Delivered Orders", "pct", True), ("Delivered Sales", "pct", True),
    ("Avg Order Value", "pct", True), ("Cancellation Rate", "pp", False),
    ("Avg Delivery Days", "day", False), ("On-Time Delivery Rate", "pp", True), ("Avg Days Ahead of ETA", "day", None),
    ("Avg Days Late", "day", False), ("Freight-to-Value Ratio", "pp", False),
    ("Avg Review Score", "pt", True), ("5-Star Rate", "pp", True), ("Negative Review Rate", "pp", False),
    ("Comment Rate", "pp", None), ("Avg Score (Late Orders)", "pt", True),
    ("Active Sellers", "pct", True), ("Sales per Seller", "pct", True),
    ("Top 10% Seller Share", "pp", None), ("Avg Seller Prep Days", "day", False),
    ("Late Handover Rate", "pp", False),
    ("Categories Sold", "pct", True), ("Products Sold", "pct", True), ("Items Sold", "pct", True),
    ("Avg Item Price", "pct", None), ("Freight-to-Price Ratio", "pp", False),
    ("Total Customers", "pct", True), ("New Customers", "pct", True), ("Returning Customer Rate", "pp", True),
    ("Orders per Customer", "pct", True), ("Sales per Customer", "pct", True),
    ("Payment Value", "pct", True), ("Credit Card Share", "pp", None), ("Avg Installments", "pct", None),
    ("Installment Order Rate", "pp", None), ("Voucher Order Rate", "pp", None),
    ("Item Sales", "pct", True),  # dùng cho biểu đồ tăng trưởng theo danh mục
]
LIME, RED, GREY, NEUTRAL = "#C2FA5C", "#F26F6F", "#8C8C8C", "#D0D0D0"


def delta_measures(base, kind, higher_better, folder):
    """3 measure: giá trị chênh lệch, câu so sánh, màu.

    Kỳ hiện tại = các ngày thuộc năm mới nhất trong bộ lọc; kỳ so sánh = cùng khoảng ngày năm trước.
    """
    diff = "DIVIDE(_c - _p, _p)" if kind == "pct" else "_c - _p"
    delta = (
        "VAR _y = MAX('Date'[Year])\n"
        "VAR _cur = CALCULATETABLE(VALUES('Date'[Date]), KEEPFILTERS('Date'[Year] = _y))\n"
        "VAR _from = EDATE(MINX(_cur, [Date]), -12)\n"
        "VAR _to = EDATE(MAXX(_cur, [Date]), -12)\n"
        f"VAR _c = CALCULATE([{base}], _cur)\n"
        f"VAR _p = CALCULATE([{base}], REMOVEFILTERS('Date'), DATESBETWEEN('Date'[Date], _from, _to))\n"
        f"RETURN IF(NOT ISBLANK(_c) && NOT ISBLANK(_p), {diff})")
    shown = {"pct": 'FORMAT(ABS(d), "0.0%")', "pp": 'FORMAT(ABS(d) * 100, "0.0") & " pp"',
             "day": 'FORMAT(ABS(d), "0.0") & " days"', "pt": 'FORMAT(ABS(d), "0.00") & " pts"'}[kind]
    # làm tròn theo đơn vị hiển thị để không hiện "▼ 0.0 days"
    digits = {"pct": 3, "pp": 3, "day": 1, "pt": 2}[kind]
    text = (
        f"VAR d = ROUND([{base} Δ], {digits})\n"
        "VAR _y = MAX('Date'[Year])\n"
        "RETURN IF(ISBLANK(d), \"No prior-year data for this period\",\n"
        f"    IF(d > 0, \"▲ \", IF(d < 0, \"▼ \", \"■ \")) & {shown} & \" vs same period \" & (_y - 1))")
    up, down = (NEUTRAL, NEUTRAL) if higher_better is None else (LIME, RED) if higher_better else (RED, LIME)
    color = (f"VAR d = ROUND([{base} Δ], {digits})\n"
             f"RETURN SWITCH(TRUE(), ISBLANK(d) || d = 0, \"{GREY}\", d > 0, \"{up}\", \"{down}\")")
    sub = folder + "\\YoY"
    fmt = PCT if kind in ("pct", "pp") else DEC2
    return [(f"{base} Δ", delta, fmt, sub), (f"{base} Δ text", text, "", sub), (f"{base} Δ color", color, "", sub)]


def all_measures():
    folder = {m[0]: m[3] for m in MEASURES}
    out = list(MEASURES)
    for base, kind, hb in KPI_DELTAS:
        out += delta_measures(base, kind, hb, folder[base])
    return out


# ----------------------------------------------------------------- xuất TMDL
def indent(text, n):
    pad = "\t" * n
    return "\n".join(pad + line if line.strip() else "" for line in text.splitlines())


def table_tmdl(name, csv_name, cols):
    lines = [f"table {q(name)}", f"\tlineageTag: {tag('t', name)}"]
    if name == "Date":
        lines.append("\tdataCategory: Time")
    lines.append("")
    for col, typ, opt in cols:
        opts = dict(o.split("=") if "=" in o else (o, True) for o in opt.split(",") if o)
        lines.append(f"\tcolumn {q(col)}")
        lines.append(f"\t\tdataType: {TMDL_TYPE[typ]}")
        if "key" in opts:
            lines.append("\t\tisKey")
        if "h" in opts:
            lines.append("\t\tisHidden")
        if typ in FORMAT and not (typ == "i" and col.lower().endswith(("year",))):
            lines.append(f"\t\tformatString: {FORMAT[typ]}")
        lines.append(f"\t\tlineageTag: {tag('c', name, col)}")
        lines.append(f"\t\tsummarizeBy: {'sum' if 'sum' in opts else 'none'}")
        lines.append(f"\t\tsourceColumn: {col}")
        if "sort" in opts:
            lines.append(f"\t\tsortByColumn: {q(opts['sort'])}")
        lines.append("")
        lines.append("\t\tannotation SummarizationSetBy = Automatic")
        if typ == "dt":
            lines.append("")
            lines.append("\t\tannotation UnderlyingDateTimeDataType = Date")
        lines.append("")
    types = ", ".join(f'{{"{c}", {M_TYPE[t]}}}' for c, t, _ in cols)
    text_cols = ", ".join(f'"{c}"' for c, t, _ in cols if t == "s")
    m = (
        "let\n"
        f"    Source = Csv.Document(File.Contents(DataFolder & \"{csv_name}\"), [Delimiter = \",\", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),\n"
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),\n"
        # ô trống trong CSV được đọc là chuỗi rỗng → đổi thành null để không sinh nhóm "(trống)" trên biểu đồ
        f"    Nulls = Table.ReplaceValue(Promoted, \"\", null, Replacer.ReplaceValue, {{{text_cols}}}),\n"
        f"    Typed = Table.TransformColumnTypes(Nulls, {{{types}}}, \"en-US\")\n"
        "in\n"
        "    Typed")
    lines += [f"\tpartition {q(name)} = m", "\t\tmode: import", "\t\tsource =", indent(m, 4), "",
              "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(lines)


def measures_tmdl():
    lines = ["table _Measures", f"\tlineageTag: {tag('t', '_Measures')}", ""]
    for name, expr, fmt, folder in all_measures():
        if "\n" in expr:
            lines.append(f"\tmeasure {q(name)} =")
            lines.append(indent(expr, 3))
        else:
            lines.append(f"\tmeasure {q(name)} = {expr}")
        if fmt:
            lines.append(f"\t\tformatString: {fmt}")
        lines.append(f"\t\tdisplayFolder: {folder}")
        lines.append(f"\t\tlineageTag: {tag('m', name)}")
        lines.append("")
    lines += [
        "\tcolumn Dummy", "\t\tdataType: int64", "\t\tisHidden", "\t\tformatString: 0",
        f"\t\tlineageTag: {tag('c', '_Measures', 'Dummy')}", "\t\tsummarizeBy: none", "\t\tsourceColumn: Dummy", "",
        "\t\tannotation SummarizationSetBy = Automatic", "",
        "\tpartition _Measures = m", "\t\tmode: import", "\t\tsource =",
        indent("let\n    Source = #table(type table [Dummy = Int64.Type], {})\nin\n    Source", 4), "",
        "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(lines)


def build(data_folder):
    """Trả về dict {đường dẫn tương đối trong definition/: nội dung}."""
    files = {}
    files["database.tmdl"] = "database\n\tcompatibilityLevel: 1600\n"
    order = ["_Measures"] + list(TABLES)
    files["model.tmdl"] = "\n".join([
        "model Model",
        "\tculture: en-US",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: en-US",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        "annotation PBI_QueryOrder = [" + ",".join(f'"{t}"' for t in ["DataFolder"] + order) + "]",
        "",
        "annotation PBI_ProTooling = [\"DevMode\"]",
        "",
        *[f"ref table {q(t)}" for t in order],
        "",
    ])
    files["expressions.tmdl"] = (
        f"expression DataFolder = \"{data_folder}\" meta [IsParameterQuery=true, Type=\"Text\", IsParameterQueryRequired=true]\n"
        f"\tlineageTag: {tag('e', 'DataFolder')}\n\n"
        "\tannotation PBI_ResultType = Text\n")
    rel = []
    for frm, fc, to, tc, both in RELATIONSHIPS:
        rel.append(f"relationship {tag('r', frm, fc, to, tc)}")
        if both:
            rel.append("\tcrossFilteringBehavior: bothDirections")
        rel.append(f"\tfromColumn: {q(frm)}.{q(fc)}")
        rel.append(f"\ttoColumn: {q(to)}.{q(tc)}")
        rel.append("")
    files["relationships.tmdl"] = "\n".join(rel)
    files["tables/_Measures.tmdl"] = measures_tmdl()
    for name, (csv_name, cols) in TABLES.items():
        files[f"tables/{name}.tmdl"] = table_tmdl(name, csv_name, cols)
    return files
