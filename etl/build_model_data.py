"""Làm sạch dữ liệu Olist và xuất các bảng mô hình sao cho Power BI.

Chạy:  python3 etl/build_model_data.py
Đầu vào: 9 file CSV gốc ở thư mục gốc dự án.
Đầu ra:  data_model/*.csv (UTF-8, dấu phẩy, ngày giờ dạng ISO).

Phạm vi phân tích: đơn đặt từ 01/01/2017 đến 31/08/2018 (20 tháng đủ dữ liệu).
Giai đoạn 09–12/2016 và 09–10/2018 rất thưa (353 đơn, ~0,35%) nên bị loại.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_model"
OUT.mkdir(exist_ok=True)

START, END = pd.Timestamp("2017-01-01"), pd.Timestamp("2018-09-01")  # END loại trừ


def read(name, **kw):
    return pd.read_csv(ROOT / f"olist_{name}_dataset.csv", **kw)


orders = read("orders", parse_dates=[
    "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date"])
items = read("order_items", parse_dates=["shipping_limit_date"])
payments = read("order_payments")
reviews = read("order_reviews", parse_dates=["review_creation_date", "review_answer_timestamp"])
customers = read("customers", dtype={"customer_zip_code_prefix": str})
sellers = read("sellers", dtype={"seller_zip_code_prefix": str})
products = read("products")
cat_en = pd.read_csv(ROOT / "product_category_name_translation.csv", encoding="utf-8-sig")

# ---------------------------------------------------------------- bảng tra cứu
STATES = {
    "AC": ("Acre", "North"), "AL": ("Alagoas", "Northeast"), "AP": ("Amapá", "North"),
    "AM": ("Amazonas", "North"), "BA": ("Bahia", "Northeast"), "CE": ("Ceará", "Northeast"),
    "DF": ("Distrito Federal", "Center-West"), "ES": ("Espírito Santo", "Southeast"),
    "GO": ("Goiás", "Center-West"), "MA": ("Maranhão", "Northeast"), "MT": ("Mato Grosso", "Center-West"),
    "MS": ("Mato Grosso do Sul", "Center-West"), "MG": ("Minas Gerais", "Southeast"),
    "PA": ("Pará", "North"), "PB": ("Paraíba", "Northeast"), "PR": ("Paraná", "South"),
    "PE": ("Pernambuco", "Northeast"), "PI": ("Piauí", "Northeast"), "RJ": ("Rio de Janeiro", "Southeast"),
    "RN": ("Rio Grande do Norte", "Northeast"), "RS": ("Rio Grande do Sul", "South"),
    "RO": ("Rondônia", "North"), "RR": ("Roraima", "North"), "SC": ("Santa Catarina", "South"),
    "SP": ("São Paulo", "Southeast"), "SE": ("Sergipe", "Northeast"), "TO": ("Tocantins", "North"),
}
REGION_ORDER = {"Southeast": 1, "South": 2, "Northeast": 3, "Center-West": 4, "North": 5}

# Tên danh mục tiếng Anh dễ đọc (từ bảng dịch gốc, sửa lỗi chính tả/viết tắt)
CATEGORY_NAME = {
    "health_beauty": "Health & Beauty", "computers_accessories": "Computer Accessories", "auto": "Auto",
    "bed_bath_table": "Bed, Bath & Table", "furniture_decor": "Furniture & Decor",
    "sports_leisure": "Sports & Leisure", "perfumery": "Perfumery", "housewares": "Housewares",
    "telephony": "Telephony", "watches_gifts": "Watches & Gifts", "food_drink": "Food & Drink", "baby": "Baby",
    "stationery": "Stationery", "tablets_printing_image": "Tablets & Printing", "toys": "Toys",
    "fixed_telephony": "Fixed Telephony", "garden_tools": "Garden Tools",
    "fashion_bags_accessories": "Bags & Accessories", "small_appliances": "Small Appliances",
    "consoles_games": "Consoles & Games", "audio": "Audio", "fashion_shoes": "Shoes", "cool_stuff": "Cool Stuff",
    "luggage_accessories": "Luggage & Accessories", "air_conditioning": "Air Conditioning",
    "construction_tools_construction": "Construction Tools",
    "kitchen_dining_laundry_garden_furniture": "Kitchen, Laundry & Garden Furniture",
    "costruction_tools_garden": "Garden Construction Tools", "fashion_male_clothing": "Men's Clothing",
    "pet_shop": "Pet Shop", "office_furniture": "Office Furniture", "market_place": "Marketplace",
    "electronics": "Electronics", "home_appliances": "Home Appliances", "party_supplies": "Party Supplies",
    "home_confort": "Home Comfort", "costruction_tools_tools": "Hand Tools",
    "agro_industry_and_commerce": "Agro Industry & Commerce",
    "furniture_mattress_and_upholstery": "Mattress & Upholstery", "books_technical": "Technical Books",
    "home_construction": "Home Construction", "musical_instruments": "Musical Instruments",
    "furniture_living_room": "Living Room Furniture", "construction_tools_lights": "Lighting",
    "industry_commerce_and_business": "Industry & Business", "food": "Food", "art": "Art",
    "furniture_bedroom": "Bedroom Furniture", "books_general_interest": "General Books",
    "construction_tools_safety": "Safety Equipment", "fashion_underwear_beach": "Underwear & Swimwear",
    "fashion_sport": "Sportswear", "signaling_and_security": "Signaling & Security", "computers": "Computers",
    "christmas_supplies": "Christmas Supplies", "fashio_female_clothing": "Women's Clothing",
    "home_appliances_2": "Large Home Appliances", "books_imported": "Imported Books", "drinks": "Drinks",
    "cine_photo": "Cine & Photo", "la_cuisine": "La Cuisine", "music": "Music",
    "home_comfort_2": "Home Comfort (Other)", "small_appliances_home_oven_and_coffee": "Ovens & Coffee Makers",
    "cds_dvds_musicals": "CDs & DVDs", "dvds_blu_ray": "DVDs & Blu-ray", "flowers": "Flowers",
    "arts_and_craftmanship": "Arts & Crafts", "diapers_and_hygiene": "Diapers & Hygiene",
    "fashion_childrens_clothes": "Children's Clothing", "security_and_services": "Security & Services",
    "pc_gamer": "PC Gaming", "portateis_cozinha_e_preparadores_de_alimentos": "Portable Kitchen Appliances",
}
STATUS_GROUP = {"delivered": ("Delivered", 1), "canceled": ("Canceled", 2), "unavailable": ("Unavailable", 3)}
PAY_NAME = {"credit_card": "Credit card", "boleto": "Boleto", "voucher": "Voucher",
            "debit_card": "Debit card", "not_defined": "Not defined"}
INSTALLMENT_LABELS = ["1x", "2–3x", "4–6x", "7–10x", "11x+"]


def bucket(values, edges, labels):
    """Gán nhãn và thứ tự sắp xếp theo các khoảng [edges[i], edges[i+1])."""
    idx = pd.Series(pd.cut(values, bins=edges, labels=False, right=False), index=values.index)
    lab = idx.map(lambda i: labels[int(i)] if pd.notna(i) else None)
    return lab, (idx + 1).astype("Int64")


def days(delta):
    return (delta.dt.total_seconds() / 86400).round(2)


# ---------------------------------------------------------------- đơn hàng
orders = orders.merge(customers, on="customer_id", how="left")
# Thứ tự đơn của mỗi khách tính trên toàn bộ lịch sử, trước khi cắt phạm vi
orders = orders.sort_values(["customer_unique_id", "order_purchase_timestamp"])
orders["customer_order_seq"] = orders.groupby("customer_unique_id").cumcount() + 1
orders = orders[(orders.order_purchase_timestamp >= START) & (orders.order_purchase_timestamp < END)].copy()

grp = orders.order_status.map(lambda s: STATUS_GROUP.get(s, ("In progress", 4)))
orders["status_group"] = grp.str[0]
orders["status_sort"] = grp.str[1]
orders["is_delivered"] = (orders.order_status == "delivered").astype(int)
orders["is_canceled"] = orders.order_status.isin(["canceled", "unavailable"]).astype(int)

it = items.groupby("order_id").agg(n_items=("order_item_id", "size"), n_products=("product_id", "nunique"),
                                   n_sellers=("seller_id", "nunique"), items_value=("price", "sum"),
                                   freight_value=("freight_value", "sum"))
orders = orders.merge(it, on="order_id", how="left")
for c in ["n_items", "n_products", "n_sellers"]:
    orders[c] = orders[c].fillna(0).astype(int)
orders[["items_value", "freight_value"]] = orders[["items_value", "freight_value"]].fillna(0).round(2)
orders["order_value"] = (orders.items_value + orders.freight_value).round(2)

pay_main = (payments.sort_values("payment_value", ascending=False).drop_duplicates("order_id")
            .set_index("order_id").payment_type.map(PAY_NAME))
pay = payments.groupby("order_id").agg(payment_value=("payment_value", "sum"),
                                       installments=("payment_installments", "max"),
                                       n_payment_types=("payment_type", "nunique"))
pay["uses_voucher"] = payments.assign(v=payments.payment_type.eq("voucher")).groupby("order_id").v.max().astype(int)
pay["payment_type_main"] = pay_main
orders = orders.merge(pay, on="order_id", how="left")
orders["payment_value"] = orders.payment_value.fillna(0).round(2)
orders["installments"] = orders.installments.fillna(0).astype(int)
orders["uses_voucher"] = orders.uses_voucher.fillna(0).astype(int)
orders["payment_type_main"] = orders.payment_type_main.fillna("Not defined")
orders["installment_bucket"], orders["installment_sort"] = bucket(
    orders.installments.clip(lower=1), [1, 2, 4, 7, 11, 99], INSTALLMENT_LABELS)

# Đánh giá: mỗi đơn lấy phản hồi mới nhất
rv = reviews.sort_values("review_answer_timestamp").drop_duplicates("order_id", keep="last").set_index("order_id")
orders["review_score"] = orders.order_id.map(rv.review_score).astype("Int64")
orders["has_review_comment"] = orders.order_id.map(rv.review_comment_message.notna()).fillna(False).astype(int)
orders["review_label"] = orders.review_score.map(lambda v: None if pd.isna(v) else f"{int(v)}★")
orders["review_sentiment"] = orders.review_score.map(
    lambda s: None if pd.isna(s) else ("Positive (4–5★)" if s >= 4 else "Neutral (3★)" if s == 3 else "Negative (1–2★)"))

# Thời gian giao hàng (ngày)
o = orders
o["delivery_days"] = days(o.order_delivered_customer_date - o.order_purchase_timestamp)
o["approval_hours"] = ((o.order_approved_at - o.order_purchase_timestamp).dt.total_seconds() / 3600).round(2)
o["handling_days"] = days(o.order_delivered_carrier_date - o.order_approved_at)
o["transit_days"] = days(o.order_delivered_customer_date - o.order_delivered_carrier_date)
o["estimated_days"] = days(o.order_estimated_delivery_date - o.order_purchase_timestamp)
o["delay_days"] = (o.order_delivered_customer_date.dt.normalize() - o.order_estimated_delivery_date).dt.days
# Chỉ giữ chỉ số giao hàng cho đơn đã giao có ngày giao hợp lệ
valid = (o.is_delivered == 1) & o.order_delivered_customer_date.notna()
for c in ["delivery_days", "transit_days", "delay_days"]:
    o.loc[~valid, c] = np.nan
o.loc[o.handling_days < 0, "handling_days"] = np.nan  # vài bản ghi lỗi thời gian
o.loc[o.transit_days < 0, "transit_days"] = np.nan
o["is_late"] = np.where(valid, (o.delay_days > 0).astype(int), np.nan)
o["delivery_bucket"], o["delivery_bucket_sort"] = bucket(
    o.delivery_days, [0, 4, 8, 15, 22, 31, 9999],
    ["0–3 days", "4–7 days", "8–14 days", "15–21 days", "22–30 days", "30+ days"])
o["delay_bucket"], o["delay_bucket_sort"] = bucket(
    o.delay_days, [-9999, -14, -7, 0, 1, 4, 8, 9999],
    ["Early 15+ d", "Early 8–14 d", "Early 1–7 d", "On due date", "Late 1–3 d", "Late 4–7 d", "Late 8+ d"])
o["purchase_date"] = o.order_purchase_timestamp.dt.normalize()
o["purchase_hour"] = o.order_purchase_timestamp.dt.hour
o["is_first_order"] = (o.customer_order_seq == 1).astype(int)

fact_orders = o[[
    "order_id", "customer_unique_id", "customer_state", "customer_city", "order_status", "status_group",
    "status_sort", "purchase_date", "order_purchase_timestamp", "order_approved_at",
    "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date",
    "is_delivered", "is_canceled", "n_items", "n_products", "n_sellers", "items_value", "freight_value",
    "order_value", "payment_value", "payment_type_main", "installments", "installment_bucket",
    "installment_sort", "uses_voucher", "review_score", "review_label", "has_review_comment", "review_sentiment",
    "delivery_days", "approval_hours", "handling_days", "transit_days", "estimated_days", "delay_days",
    "is_late", "delivery_bucket", "delivery_bucket_sort", "delay_bucket", "delay_bucket_sort",
    "purchase_hour", "customer_order_seq", "is_first_order"]].rename(columns={
        "order_purchase_timestamp": "purchase_ts", "order_approved_at": "approved_ts",
        "order_delivered_carrier_date": "carrier_ts", "order_delivered_customer_date": "delivered_ts",
        "order_estimated_delivery_date": "estimated_date"})
fact_orders["customer_city"] = fact_orders.customer_city.str.title()
for c in ["is_late", "delay_days"]:
    fact_orders[c] = fact_orders[c].astype("Int64")
scope_ids = set(fact_orders.order_id)

# ---------------------------------------------------------------- dòng sản phẩm
fi = items[items.order_id.isin(scope_ids)].merge(
    o[["order_id", "order_delivered_carrier_date"]], on="order_id", how="left")
fi["item_value"] = (fi.price + fi.freight_value).round(2)
has_carrier = fi.order_delivered_carrier_date.notna()
fi["seller_ship_late"] = np.where(has_carrier, (fi.order_delivered_carrier_date > fi.shipping_limit_date).astype(int), np.nan)
fact_items = fi[["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date",
                 "price", "freight_value", "item_value", "seller_ship_late"]].rename(
    columns={"shipping_limit_date": "shipping_limit_ts"})
fact_items["seller_ship_late"] = fact_items.seller_ship_late.astype("Int64")

# ---------------------------------------------------------------- thanh toán
fp = payments[payments.order_id.isin(scope_ids)].copy()
fp["payment_type"] = fp.payment_type.map(PAY_NAME)
fp["installments_bucket"], fp["installments_sort"] = bucket(
    fp.payment_installments.clip(lower=1), [1, 2, 4, 7, 11, 99], INSTALLMENT_LABELS)
fact_payments = fp[["order_id", "payment_sequential", "payment_type", "payment_installments",
                    "installments_bucket", "installments_sort", "payment_value"]]

# ---------------------------------------------------------------- chiều sản phẩm
p = products.merge(cat_en, on="product_category_name", how="left")
p["category_pt"] = p.product_category_name.fillna("sem_categoria")
key = p.product_category_name_english.fillna(p.product_category_name)
p["category"] = key.map(CATEGORY_NAME).fillna("Uncategorized")
p["volume_cm3"] = p.product_length_cm * p.product_height_cm * p.product_width_cm
p["photos_bucket"], p["photos_sort"] = bucket(p.product_photos_qty.fillna(0), [0, 1, 2, 4, 99],
                                              ["No photo", "1 photo", "2–3 photos", "4+ photos"])
dim_product = p[["product_id", "category", "category_pt", "product_photos_qty", "photos_bucket", "photos_sort",
                 "product_weight_g", "volume_cm3", "product_description_lenght"]].rename(
    columns={"product_photos_qty": "photos_qty", "product_weight_g": "weight_g",
             "product_description_lenght": "description_length"})
for c in ["photos_qty", "description_length"]:
    dim_product[c] = dim_product[c].astype("Int64")

# ---------------------------------------------------------------- chiều người bán
delivered_items = fact_items[fact_items.order_id.isin(o.loc[o.is_delivered == 1, "order_id"])]
seller_rev = delivered_items.groupby("seller_id").item_value.sum()
s = sellers.copy()
s["seller_city"] = s.seller_city.str.title()
s["seller_region"] = s.seller_state.map(lambda x: STATES.get(x, (x, "Other"))[1])
s["seller_code"] = "S-" + s.seller_id.str[:6].str.upper()
s["revenue_scope"] = s.seller_id.map(seller_rev).fillna(0).round(2)
s["revenue_tier"], s["revenue_tier_sort"] = bucket(
    s.revenue_scope, [0, 1000, 5000, 20000, 100000, 1e12],
    ["< R$1K", "R$1K–5K", "R$5K–20K", "R$20K–100K", "R$100K+"])
first_sale = fact_items.merge(o[["order_id", "purchase_date"]], on="order_id").groupby("seller_id").purchase_date.min()
s["first_sale_date"] = s.seller_id.map(first_sale)
dim_seller = s[s.seller_id.isin(fact_items.seller_id)][[
    "seller_id", "seller_code", "seller_city", "seller_state", "seller_region", "revenue_scope",
    "revenue_tier", "revenue_tier_sort", "first_sale_date"]]

# ---------------------------------------------------------------- chiều khách hàng
c = o.groupby("customer_unique_id").agg(
    first_order_date=("purchase_date", "min"), n_orders=("order_id", "size"),
    lifetime_value=("order_value", lambda v: v[o.loc[v.index, "is_delivered"] == 1].sum()))
c["lifetime_value"] = c.lifetime_value.round(2)
c["order_count_group"], c["order_count_sort"] = bucket(c.n_orders, [1, 2, 3, 4, 999], ["1 order", "2 orders", "3 orders", "4+ orders"])
c["customer_type"] = np.where(c.n_orders > 1, "Repeat", "One-time")
dim_customer = c.reset_index()

# ---------------------------------------------------------------- chiều bang & ngày
dim_state = pd.DataFrame([(k, v[0], v[1], REGION_ORDER[v[1]]) for k, v in STATES.items()],
                         columns=["state", "state_name", "region", "region_sort"])
d = pd.DataFrame({"Date": pd.date_range(START, END - pd.Timedelta(days=1), freq="D")})
d["Year"] = d.Date.dt.year
d["Quarter"] = "Q" + d.Date.dt.quarter.astype(str)
d["MonthNo"] = d.Date.dt.month
d["Month"] = d.Date.dt.strftime("%b")
d["YearMonth"] = d.Date.dt.strftime("%b %y")
d["YearMonthKey"] = d.Year * 100 + d.MonthNo
d["MonthStart"] = d.Date.dt.to_period("M").dt.to_timestamp()
d["Weekday"] = d.Date.dt.dayofweek.map(lambda i: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i])
d["WeekdayNo"] = d.Date.dt.dayofweek + 1
dim_date = d

# ---------------------------------------------------------------- xuất file
tables = {"fact_orders": fact_orders, "fact_order_items": fact_items, "fact_payments": fact_payments,
          "dim_product": dim_product, "dim_seller": dim_seller, "dim_customer": dim_customer,
          "dim_state": dim_state, "dim_date": dim_date}
for name, df in tables.items():
    df = df.copy()
    # Cột chỉ chứa ngày (giờ luôn 00:00) xuất dạng yyyy-mm-dd để Power Query đọc là kiểu date
    for c in df.select_dtypes("datetime").columns:
        v = df[c].dropna()
        if (v == v.dt.normalize()).all():
            df[c] = df[c].dt.strftime("%Y-%m-%d")
    df.to_csv(OUT / f"{name}.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    print(f"{name:18s} {len(df):>8,} dòng  {df.shape[1]:>3} cột")
