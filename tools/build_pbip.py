#!/usr/bin/env python3
"""Sinh project Power BI Olist.pbip (semantic model TMDL + report PBIR, 7 trang).

Chạy:
    python3 tools/build_pbip.py --fonts <thư mục font Segoe> [--schemas <thư mục JSON schema PBIR>]

--fonts   : chứa segoeui.ttf, seguisb.ttf, segoeuib.ttf, seguibl.ttf, SegoeIcons.ttf (để vẽ ảnh nền).
            Bỏ qua nếu muốn giữ ảnh nền đã có.
--schemas : (tuỳ chọn) bản sao repo microsoft/json-schemas .../report/definition để kiểm tra file sinh ra.
"""
import argparse
import json
import shutil
import uuid
from pathlib import Path

import backgrounds
import model_tmdl
from layout import (AMBER, BG, CX, CYAN, GRID, KPI_W, KPI_X, KPI_Y, L2, L3, LIME, MUTED, NAV, NAV_H, NAV_STEP, NAV_Y,
                    PAGE_H, PAGE_W, PANEL, R2, R3, RED, SUBTLE, TEXT, WHITE_SERIES)

ROOT = Path(__file__).resolve().parents[1]
NAME = "Olist"
DATA_FOLDER = "Y:\\Desktop\\Olist_analyst\\data_model\\"
SCHEMA_BASE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
VC_SCHEMA = SCHEMA_BASE + "visualContainer/2.7.0/schema.json"
PAGE_SCHEMA = SCHEMA_BASE + "page/2.1.0/schema.json"
REPORT_SCHEMA = SCHEMA_BASE + "report/3.2.0/schema.json"
THEME_FILE = "OlistDark.json"
BASE_THEME = "Fluent2-CY26SU03"


# ============================================================ biểu thức PBIR
def L(v):
    return {"expr": {"Literal": {"Value": v}}}


def S(v):
    return L("'" + str(v).replace("'", "''") + "'")


def D(v):
    return L(f"{v}D")


def I(v):
    return L(f"{v}L")


def B(v):
    return L("true" if v else "false")


def C(hex_):
    return {"solid": {"color": S(hex_)}}


def M(name, entity="_Measures"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": name}}


def COL(entity, name):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": name}}


def CM(measure):
    """Màu lấy theo giá trị measure (định dạng có điều kiện kiểu field value)."""
    return {"solid": {"color": {"expr": M(measure)}}}


def props(selector=None, **kw):
    o = {"properties": kw}
    if selector:
        o["selector"] = selector
    return o


DEFAULT = {"id": "default"}
ALL_POINTS = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}


def qref(f):
    k = next(iter(f))
    return f"{f[k]['Expression']['SourceRef']['Entity']}.{f[k]['Property']}"


def proj(f, display=None, active=None):
    k = next(iter(f))
    d = {"field": f, "queryRef": qref(f), "nativeQueryRef": f[k]["Property"]}
    if display:
        d["displayName"] = display
    if active is not None:
        d["active"] = active
    return d


def series_fill(measure, color):
    return props({"metadata": qref(M(measure))}, fill=C(color))


def value_fill(entity, col, value, color):
    sel = {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": COL(entity, col),
                                                "Right": {"Literal": {"Value": "'" + value + "'"}}}}}]}
    return props(sel, fill=C(color))


def topn_filter(entity, col, measure, n, name):
    return {
        "name": name, "field": COL(entity, col), "type": "TopN",
        "filter": {
            "Version": 2,
            "From": [
                {"Name": "subquery", "Type": 2, "Expression": {"Subquery": {"Query": {
                    "Version": 2,
                    "From": [{"Name": "t", "Entity": entity, "Type": 0}, {"Name": "m", "Entity": "_Measures", "Type": 0}],
                    "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": col}, "Name": "field"}],
                    "OrderBy": [{"Direction": 2, "Expression": {
                        "Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": measure}}}],
                    "Top": n}}}},
                {"Name": "t", "Entity": entity, "Type": 0},
            ],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": col}}],
                "Table": {"SourceRef": {"Source": "subquery"}}}}}],
        },
    }


def not_blank_filter(entity, col, name):
    """Bộ lọc visual: bỏ giá trị trống của cột (vd. đơn chưa giao không có nhóm thời gian giao)."""
    ref = {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": col}}
    return {"name": name, "field": COL(entity, col), "type": "Advanced",
            "filter": {"Version": 2, "From": [{"Name": "t", "Entity": entity, "Type": 0}],
                       "Where": [{"Condition": {"Not": {"Expression": {"Comparison": {
                           "ComparisonKind": 0, "Left": ref, "Right": {"Literal": {"Value": "null"}}}}}}}]}}


def exclude_filter(entity, col, values, name):
    ref = {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": col}}
    return {"name": name, "field": COL(entity, col), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "t", "Entity": entity, "Type": 0}],
                       "Where": [{"Condition": {"Not": {"Expression": {"In": {
                           "Expressions": [ref], "Values": [[{"Literal": {"Value": f"'{v}'"}}] for v in values]}}}}}]}}


# ============================================================ khung & visual
def frame(title=None, subtitle=None, panel=True, header=True):
    title_props = {"show": B(bool(title))}
    if title:
        title_props.update(text=S(title), fontColor=C(TEXT), fontSize=D(12), fontFamily=S("Segoe UI Semibold"))
    sub_props = {"show": B(bool(subtitle))}
    if subtitle:
        sub_props.update(text=S(subtitle), fontColor=C(SUBTLE), fontSize=D(9))
    vco = {
        "title": [props(**title_props)],
        "subTitle": [props(**sub_props)],
        "background": [props(show=B(panel), color=C(PANEL), transparency=D(0))],
        "border": [props(show=B(panel), color=C(PANEL), radius=D(14), width=D(1))],
        "dropShadow": [props(show=B(False))],
        "padding": [props(top=D(8 if panel else 0), bottom=D(8 if panel else 0), left=D(14 if panel else 0),
                          right=D(14 if panel else 0))],
    }
    if not header:
        vco["visualHeader"] = [props(show=B(False))]
    return vco


def container(name, pos, visual, z=0, filters=None, how_created=None):
    x, y, w, h = pos
    d = {"$schema": VC_SCHEMA, "name": name,
         "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
         "visual": visual}
    if filters:
        d["filterConfig"] = {"filters": filters}
    if how_created:
        d["howCreated"] = how_created
    return d


def axes(sec=False, cat_font=9, val_show=True):
    va = dict(show=B(val_show), labelColor=C(SUBTLE), fontSize=D(8), showAxisTitle=B(False), gridlineShow=B(True),
              gridlineColor=C(GRID), gridlineStyle=S("dotted"))
    if sec:
        va.update(secShow=B(True), secLabelColor=C(SUBTLE), secFontSize=D(8), secShowAxisTitle=B(False))
    return {
        "categoryAxis": [props(show=B(True), labelColor=C(MUTED), fontSize=D(cat_font), showAxisTitle=B(False),
                               gridlineShow=B(False))],
        "valueAxis": [props(**va)],
        "legend": [props(show=B(True), position=S("Top"), labelColor=C("#CFCFCF"), fontSize=D(9))],
    }


def labels(show=True, units=0, size=8, hide=(), position=None, precision=None, density=None, background=False):
    extra = {}
    if position:
        extra["labelPosition"] = S(position)
    if precision is not None:
        extra["labelPrecision"] = I(precision)
    if density is not None:
        extra["labelDensity"] = I(density)
    if background:
        extra.update(enableBackground=B(True), backgroundColor=C(PANEL), backgroundTransparency=D(15))
    o = [props(show=B(show), color=C("#E6E6E6"), fontSize=D(size), labelDisplayUnits=D(units), **extra)]
    o += [props({"metadata": qref(M(m))}, show=B(False)) for m in hide]
    return o


def chart(vtype, roles, title, objects=None, sort=None, subtitle=None, legend=True):
    query = {"queryState": {role: {"projections": [proj(*p) for p in items]} for role, items in roles.items() if items}}
    if sort:
        query["sortDefinition"] = {"sort": [{"field": f, "direction": d} for f, d in sort], "isDefaultSort": False}
    objs = objects or {}
    if not legend:
        objs.setdefault("legend", [props(show=B(False))])
    return {"visualType": vtype, "query": query, "objects": objs,
            "visualContainerObjects": frame(title, subtitle), "drillFilterOtherVisuals": True}


def merge(*dicts):
    out = {}
    for d in dicts:
        out.update(d)
    return out


# ------------------------------------------------------------- loại biểu đồ
def combo(cat, cols, lines, title, col_colors=(), line_colors=(WHITE_SERIES,), stacked=False, col_units=0,
          subtitle=None, cat_font=9):
    """Cột (+ đường trục phụ). cols/lines: list (measure, nhãn)."""
    # lineClusteredColumnComboChart bỏ qua màu cột theo series → dùng bản stacked (1 series trông như nhau)
    vtype = "lineStackedColumnComboChart"
    roles = {"Category": [(cat, None)], "Y": [(M(m), n) for m, n in cols], "Y2": [(M(m), n) for m, n in lines]}
    fills = [series_fill(m, c) for (m, _), c in zip(cols, col_colors)]
    if len(cols) == 1 and col_colors:
        fills.insert(0, props(fill=C(col_colors[0])))  # 1 series cột: Power BI bỏ qua selector theo measure
    fills += [series_fill(m, c) for (m, _), c in zip(lines, line_colors)]
    objs = axes(sec=True, cat_font=cat_font)
    objs["dataPoint"] = fills
    objs["labels"] = labels(units=col_units, hide=[m for m, _ in lines])
    objs["lineStyles"] = [props(strokeWidth=D(2.5), showMarker=B(True), markerSize=D(4))]
    return chart(vtype, roles, title, objs, subtitle=subtitle)


def bars(cat, measure, title, display=None, horizontal=True, color=LIME, cond=None, sort="desc", units=0,
         tooltips=(), subtitle=None, val_axis=False, label_pos=None, cat_font=9, sort_by_category=False,
         precision=None):
    vtype = "clusteredBarChart" if horizontal else "clusteredColumnChart"
    roles = {"Category": [(cat, None)], "Y": [(M(measure), display)],
             "Tooltips": [(M(t), None) for t in tooltips]}
    objs = axes(val_show=val_axis, cat_font=cat_font)
    objs["legend"] = [props(show=B(False))]
    objs["dataPoint"] = [props(fill=C(color))]
    if cond:
        objs["dataPoint"].append(props(ALL_POINTS, fill=CM(cond)))
    objs["labels"] = labels(units=units, size=8.5, position=label_pos, precision=precision, background=horizontal)
    direction = "Descending" if sort == "desc" else "Ascending"
    order = [(cat if sort_by_category else M(measure), direction)]
    return chart(vtype, roles, title, objs, sort=order, subtitle=subtitle)


def table(columns, title, sort_field, subtitle=None, direction="Descending"):
    roles = {"Values": [(f, n) for f, n in columns]}
    objs = {
        "columnHeaders": [props(fontColor=C(LIME), backColor=C(PANEL), fontSize=D(9), bold=B(True),
                                wordWrap=B(True))],
        "values": [props(fontColorPrimary=C("#E6E6E6"), backColorPrimary=C(PANEL), fontColorSecondary=C("#E6E6E6"),
                         backColorSecondary=C("#222322"), fontSize=D(9))],
        "grid": [props(gridHorizontal=B(True), gridHorizontalColor=C(GRID), gridVertical=B(False),
                       outlineColor=C(GRID), rowPadding=D(4))],
        "total": [props(totals=B(False))],
    }
    sort_f = M(sort_field) if isinstance(sort_field, str) else sort_field
    return chart("tableEx", roles, title, objs, sort=[(sort_f, direction)], subtitle=subtitle)


def kpi_visuals(k, measure, label, units=1, precision=None):
    """Card giá trị (nhãn phía trên) + card dòng so sánh cùng kỳ."""
    x, y = KPI_X[k], KPI_Y
    value_props = dict(fontSize=D(25), bold=B(True), fontColor=C(TEXT), horizontalAlignment=S("left"),
                       labelDisplayUnits=I(units))
    if precision is not None:
        value_props["labelPrecision"] = I(precision)
    no_pad = [props(DEFAULT, paddingUniform=I(0), topOuterMargin=I(0), bottomOuterMargin=I(0),
                    leftOuterMargin=I(0), rightOuterMargin=I(0))]
    value = {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [proj(M(measure), label)]}}},
        "objects": {
            "value": [props(DEFAULT, **value_props)],
            "label": [props(DEFAULT, show=B(True), position=S("aboveValue"), fontSize=D(11),
                            fontColor=C("#D6D6D6"), horizontalAlignment=S("left"))],
            "outline": [props(DEFAULT, show=B(False))],
            "accentBar": [props(DEFAULT, show=B(False))],
            "layout": no_pad,
        },
        "visualContainerObjects": frame(panel=False, header=False),
        "drillFilterOtherVisuals": True,
    }
    delta = {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [proj(M(measure + " Δ text"), "vs. same period last year")]}}},
        "objects": {
            "value": [props(DEFAULT, fontSize=D(9.5), fontColor=CM(measure + " Δ color"),
                            horizontalAlignment=S("left"))],
            "label": [props(DEFAULT, show=B(False))],
            "outline": [props(DEFAULT, show=B(False))],
            "accentBar": [props(DEFAULT, show=B(False))],
            "layout": no_pad,
        },
        "visualContainerObjects": frame(panel=False, header=False),
        "drillFilterOtherVisuals": True,
    }
    return [container(f"kpi{k + 1}_value", (x + 16, y + 12, KPI_W - 64, 84), value, z=100 + k),
            container(f"kpi{k + 1}_delta", (x + 16, y + 98, KPI_W - 24, 28), delta, z=110 + k)]


def textbox(name, pos, paragraphs, z=0):
    visual = {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": t, "textStyle": st} for t, st in para]} for para in paragraphs]}}]},
        "visualContainerObjects": frame(panel=False, header=False),
        "drillFilterOtherVisuals": True,
    }
    return container(name, pos, visual, z=z)


def slicer(name, pos, fields, header, group, z):
    visual = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [proj(f, active=True) for f in fields]}}},
        "objects": {
            "data": [props(mode=S("Dropdown"))],
            "header": [props(show=B(True), text=S(header), fontColor=C("#D9D9D9"), textSize=D(10),
                             fontFamily=S("Segoe UI"))],
            "items": [props(fontColor=C(TEXT), background=C(PANEL), textSize=D(10))],
            "selection": [props(singleSelect=B(False), selectAllCheckboxEnabled=B(True))],
            "general": [props(outlineColor=C("#4A4B4A"), outlineWeight=D(1))],
        },
        "visualContainerObjects": frame(panel=False, header=False),
        "syncGroup": {"groupName": group, "fieldChanges": True, "filterChanges": True},
        "drillFilterOtherVisuals": True,
    }
    return container(name, pos, visual, z=z)


def nav_button(i, target):
    visual = {
        "visualType": "actionButton",
        "objects": {
            "icon": [props(DEFAULT, show=B(False), shapeType=S("blank"))],
            "text": [props(DEFAULT, show=B(False))],
            "outline": [props(DEFAULT, show=B(False))],
            "fill": [props(DEFAULT, show=B(True), fillColor=C("#FFFFFF"), transparency=D(100)),
                     props({"id": "hover"}, show=B(True), fillColor=C("#FFFFFF"), transparency=D(90))],
            "shape": [props(tileShape=S("rectangleRounded"), rectangleRoundedCurve=I(12))],
        },
        "visualContainerObjects": {
            "visualLink": [props(show=B(True), type=S("PageNavigation"), navigationSection=S(target))],
            "title": [props(show=B(False))],
            "background": [props(show=B(False))],
            "border": [props(show=B(False))],
            "dropShadow": [props(show=B(False))],
            "visualHeader": [props(show=B(False))],
        },
        "drillFilterOtherVisuals": True,
    }
    pos = (14, NAV_Y + i * NAV_STEP, 208, NAV_H)
    return container(f"nav_{target}", pos, visual, z=2000 + i, how_created="InsertVisualButton")


# ============================================================ nội dung 7 trang
YM = COL("Date", "YearMonth")
TS = {"fontFamily": "Segoe UI"}


def line(cat, measures, title, colors=(LIME,), label_units=1, subtitle=None, cat_font=8):
    """Biểu đồ đường; measures: list (measure, nhãn)."""
    roles = {"Category": [(cat, None)], "Y": [(M(m), n) for m, n in measures]}
    objs = axes(cat_font=cat_font)
    objs["dataPoint"] = [series_fill(m, c) for (m, _), c in zip(measures, colors)]
    objs["labels"] = labels(units=label_units, size=8, precision=0, density=15)
    objs["lineStyles"] = [props(strokeWidth=D(2.5), showMarker=B(True), markerSize=D(5))]
    if len(measures) == 1:
        objs["legend"] = [props(show=B(False))]
    return chart("lineChart", roles, title, objs, subtitle=subtitle)


def page_overview():
    kpis = [("Total Orders", "Total Orders", 1, None, "\ue7bf"),
            ("Delivered Orders", "Delivered Orders", 1, None, "\ue806"),
            ("Delivered Sales", "Delivered Sales", 0, 2, "\ueafc"),
            ("Avg Order Value", "Average Order Value", 1, 2, "\ue8ec"),
            ("Cancellation Rate", "Cancellation Rate", 1, None, "\uea39")]
    charts = [
        ("sales_month", L2, combo(YM, [("Delivered Sales", "Delivered Sales (R$)")],
                                  [("Delivered Orders", "Delivered Orders")],
                                  "Monthly Sales & Delivered Orders", col_colors=[LIME], cat_font=8)),
        ("sales_state", R2, bars(COL("States", "state"), "Delivered Sales", "Delivered Sales by Customer State",
                                 "Delivered Sales", tooltips=["Sales Share (State)", "Delivered Orders"],
                                 subtitle="Top 10 states"),
         [topn_filter("States", "state", "Delivered Sales", 10, "top10_state")]),
        ("aov_month", L3, line(YM, [("Avg Order Value", "Average Order Value")], "Average Order Value by Month",
                               subtitle="Delivered sales ÷ delivered orders (R$)")),
        ("status_month", R3, combo(YM, [("Orders Canceled", "Canceled"), ("Orders Unavailable", "Unavailable"),
                                        ("Orders In Progress", "In progress")],
                                   [("Cancellation Rate", "Cancellation rate")],
                                   "Orders Not Delivered by Month", col_colors=[RED, AMBER, SUBTLE],
                                   line_colors=[WHITE_SERIES], stacked=True, cat_font=8)),
    ]
    return dict(id="overview", title="BUSINESS OVERVIEW",
                subtitle="Sales performance and order health.", kpis=kpis, charts=charts)


def page_delivery():
    kpis = [("Avg Delivery Days", "Avg Delivery Days", 1, 1, "\ue916"),
            ("On-Time Delivery Rate", "On-Time Delivery Rate", 1, None, "\ue73e"),
            ("Avg Days Ahead of ETA", "Avg Days Ahead of ETA", 1, 1, "\ue823"),
            ("Avg Days Late", "Avg Days Late", 1, 1, "\ue7ba"),
            ("Freight-to-Value Ratio", "Freight / Goods Value", 1, None, "\ue7b8")]
    region = COL("States", "region")
    stages = chart("barChart",
                   {"Category": [(region, None)],
                    "Y": [(M("Avg Approval Days"), "Approval"), (M("Avg Seller Handling Days"), "Seller handling"),
                          (M("Avg Carrier Transit Days"), "Carrier transit")]},
                   "Delivery Time Breakdown by Region (days)",
                   merge(axes(val_show=False), {
                       "dataPoint": [series_fill("Avg Approval Days", SUBTLE),
                                     series_fill("Avg Seller Handling Days", AMBER),
                                     series_fill("Avg Carrier Transit Days", LIME)],
                       "labels": [props(show=B(True), color=C("#111111"), fontSize=D(8.5), labelDisplayUnits=D(0))]}),
                   sort=[(region, "Ascending")])
    charts = [
        ("days_month", L2, combo(YM, [("Avg Delivery Days", "Avg delivery time (days)")],
                                 [("Late Delivery Rate", "Late delivery rate")],
                                 "Delivery Time & Late Delivery Rate by Month", col_colors=[LIME],
                                 line_colors=[RED], cat_font=8)),
        ("days_state", R2, bars(COL("States", "state"), "Avg Delivery Days", "Avg Delivery Time by State (days)",
                                "Avg delivery time", cond="Late Rate Color",
                                tooltips=["Late Delivery Rate", "Delivered Orders"],
                                subtitle="Color = late rate: green < 8% · amber 8–12% · red ≥ 12%")),
        ("days_dist", L3, bars(COL("Orders", "delivery_bucket"), "Order Share (Delivery Time)",
                               "Delivery Time Distribution", "Share of orders", horizontal=False,
                               tooltips=["Delivered Orders", "Avg Review Score"], sort="asc", sort_by_category=True,
                               subtitle="Days from purchase to customer delivery"),
         [not_blank_filter("Orders", "delivery_bucket", "nb_delivery_bucket")]),
        ("stages_region", R3, stages),
    ]
    return dict(id="delivery", title="DELIVERY PERFORMANCE",
                subtitle="Speed, reliability and freight cost.", kpis=kpis, charts=charts)


def page_experience():
    kpis = [("Avg Review Score", "Avg Review Score", 1, 2, "\ue734"),
            ("5-Star Rate", "5-Star Review Rate", 1, None, "\ue735"),
            ("Negative Review Rate", "1–2 Star Review Rate", 1, None, "\ue8e0"),
            ("Comment Rate", "Reviews with Comments", 1, None, "\ue91c"),
            ("Avg Score (Late Orders)", "Avg Score – Late Orders", 1, 2, "\ue7ba")]
    charts = [
        ("score_delay", L2, bars(COL("Orders", "delay_bucket"), "Avg Review Score",
                                 "Review Score vs. Delivery Timeliness", "Avg review score", horizontal=False,
                                 cond="Score Color", tooltips=["Reviews", "Negative Review Rate"],
                                 sort="asc", sort_by_category=True,
                                 subtitle="Actual vs. estimated delivery date · green ≥ 4 · amber 3–4 · red < 3"),
         [not_blank_filter("Orders", "delay_bucket", "nb_delay_bucket")]),
        ("score_dist", R2, bars(COL("Orders", "review_label"), "Review Share", "Review Score Distribution",
                                "Share of reviews", cond="Star Color", tooltips=["Reviews"], sort="desc",
                                sort_by_category=True),
         [not_blank_filter("Orders", "review_label", "nb_review_label")]),
        ("score_month", L3, combo(YM, [("Negative Review Rate", "1–2 star rate")],
                                  [("Avg Review Score", "Avg review score")],
                                  "Review Score & Negative Rate by Month", col_colors=["#7A3B3B"],
                                  line_colors=[LIME], cat_font=8)),
        ("score_cat", R3, bars(COL("Products", "category"), "Avg Score (100+ Reviews)",
                               "Lowest-Rated Categories", "Avg review score", cond="Score Color",
                               tooltips=["Reviews", "Late Delivery Rate"], sort="asc",
                               subtitle="Categories with 100+ reviews · scroll for more")),
    ]
    return dict(id="experience", title="CUSTOMER EXPERIENCE",
                subtitle="Satisfaction levels and what drives them.", kpis=kpis, charts=charts)


def page_sellers():
    kpis = [("Active Sellers", "Active Sellers", 1, None, "\ue719"),
            ("Sales per Seller", "Sales per Seller", 1, 0, "\ueafc"),
            ("Top 10% Seller Share", "Top-10% Seller Share", 1, None, "\ueb05"),
            ("Avg Seller Prep Days", "Avg Seller Prep Days", 1, 1, "\ue916"),
            ("Late Handover Rate", "Late Handover Rate", 1, None, "\ue7ba")]
    tier = table([(COL("Sellers", "revenue_tier"), "Seller sales tier"),
                  (M("Active Sellers"), "Sellers"), (M("Item Sales"), "Sales"),
                  (M("Sales Share (Seller)"), "Sales share"), (M("Sales per Seller"), "Sales / seller"),
                  (M("Avg Review Score"), "Avg score"), (M("Late Handover Rate"), "Late handover")],
                 "Seller Tiers by Sales", COL("Sellers", "revenue_tier"), direction="Ascending",
                 subtitle="Tier = seller's delivered sales over Jan 2017 – Aug 2018")
    charts = [
        ("sellers_month", L2, combo(YM, [("Active Sellers", "Active sellers")], [("New Sellers", "New sellers")],
                                    "Active & New Sellers by Month", col_colors=[LIME], cat_font=8)),
        ("top_sellers", R2, bars(COL("Sellers", "seller_code"), "Item Sales", "Top 10 Sellers by Sales", "Sales",
                                 tooltips=["Items Sold", "Avg Review Score", "Late Delivery Rate"]),
         [topn_filter("Sellers", "seller_code", "Item Sales", 10, "top10_seller")]),
        ("seller_tier", L3, tier),
        ("seller_state", R3, bars(COL("Sellers", "seller_state"), "Active Sellers", "Active Sellers by Seller State",
                                  "Active sellers", tooltips=["Item Sales", "Sales Share (Seller)"],
                                  subtitle="Top 10 states"),
         [topn_filter("Sellers", "seller_state", "Active Sellers", 10, "top10_seller_state")]),
    ]
    return dict(id="sellers", title="SELLER PERFORMANCE",
                subtitle="Seller base, sales concentration and fulfilment quality.", kpis=kpis, charts=charts)


def page_products():
    kpis = [("Categories Sold", "Categories Sold", 1, None, "\ueca5"),
            ("Products Sold", "Unique Products Sold", 1, None, "\uf158"),
            ("Items Sold", "Items Sold", 1, None, "\ue7bf"),
            ("Avg Item Price", "Avg Item Price", 1, 2, "\ue8ec"),
            ("Freight-to-Price Ratio", "Freight / Item Price", 1, None, "\ue806")]
    cat = COL("Products", "category")
    cat_table = table([(cat, "Category"), (M("Item Sales"), "Sales"), (M("Sales Share (Category)"), "Share"),
                       (M("Items Sold"), "Items"), (M("Avg Item Price"), "Avg price"),
                       (M("Freight-to-Price Ratio"), "Freight/price"), (M("Avg Review Score"), "Avg score"),
                       (M("Late Delivery Rate"), "Late rate")],
                      "Category Scorecard", "Item Sales", subtitle="Sorted by sales · scroll for more")
    growth = bars(cat, "Item Sales Δ", "YoY Sales Growth – Top 10 Categories", "YoY growth",
                  cond="Item Sales Δ color", tooltips=["Item Sales"],
                  subtitle="Latest year in filter vs. same period of prior year")
    charts = [
        ("top_cat", L3, bars(cat, "Item Sales", "Top 10 Categories by Sales", "Sales",
                             tooltips=["Sales Share (Category)", "Items Sold", "Avg Item Price"]),
         [topn_filter("Products", "category", "Item Sales", 10, "top10_cat")]),
        ("cat_growth", R2, growth, [topn_filter("Products", "category", "Item Sales", 10, "top10_cat_g")]),
        ("cat_table", L2, cat_table),
        ("qty_month", R3, combo(YM, [("Items Sold", "Items sold")], [("Avg Item Price", "Avg item price")],
                                "Items Sold & Avg Price by Month", col_colors=[LIME], cat_font=8)),
    ]
    return dict(id="products", title="PRODUCT PERFORMANCE",
                subtitle="Category contribution, pricing and freight burden.", kpis=kpis, charts=charts)


def page_customers():
    kpis = [("Total Customers", "Customers", 1, None, "\ue716"),
            ("New Customers", "New Customers", 1, None, "\ue8fa"),
            ("Returning Customer Rate", "Returning Rate", 1, None, "\ue777"),
            ("Orders per Customer", "Orders per Customer", 1, 3, "\ue7bf"),
            ("Sales per Customer", "Sales per Customer", 1, 2, "\ueafc")]
    hours = bars(COL("Orders", "purchase_hour"), "Total Orders", "Orders by Hour of Day", "Orders",
                 horizontal=False, sort="asc", sort_by_category=True, tooltips=["Avg Order Value"],
                 subtitle="Purchase timestamp (local time)")
    hours["objects"]["labels"] = labels(show=False)
    hours["objects"]["categoryAxis"] = [props(show=B(True), labelColor=C(MUTED), fontSize=D(8), showAxisTitle=B(False),
                                              gridlineShow=B(False), axisType=S("Categorical"))]
    hours["objects"]["valueAxis"] = axes()["valueAxis"]
    charts = [
        ("cust_month", L2, combo(YM, [("New Customers", "New"), ("Returning Customers", "Returning")],
                                 [("Returning Customer Rate", "Returning rate")],
                                 "New vs. Returning Customers by Month", col_colors=[LIME, CYAN],
                                 line_colors=[WHITE_SERIES], stacked=True, cat_font=8)),
        ("cust_state", R2, bars(COL("States", "state"), "Total Customers", "Customers by State", "Customers",
                                tooltips=["Sales per Customer", "Returning Customer Rate"], subtitle="Top 10 states"),
         [topn_filter("States", "state", "Total Customers", 10, "top10_cust_state")]),
        ("hours", L3, hours),
        ("order_count", R3, bars(COL("Customers", "order_count_group"), "Customer Share",
                                 "Orders per Customer Distribution", "Share of customers", horizontal=False,
                                 tooltips=["Total Customers", "Sales per Customer"], sort="asc", sort_by_category=True,
                                 subtitle="Orders placed by each customer over Jan 2017 – Aug 2018")),
    ]
    return dict(id="customers", title="CUSTOMER INSIGHTS",
                subtitle="Customer base, retention and shopping behavior.", kpis=kpis, charts=charts)


PAY_COLORS = {"Credit card": LIME, "Boleto": WHITE_SERIES, "Voucher": AMBER, "Debit card": CYAN,
              "Not defined": SUBTLE}


def page_payments():
    kpis = [("Payment Value", "Total Payment Value", 0, 2, "\ue8c7"),
            ("Credit Card Share", "Credit Card Share", 1, None, "\ueb05"),
            ("Avg Installments", "Avg Installments (CC)", 1, 1, "\ue8ef"),
            ("Installment Order Rate", "Installment Order Rate", 1, None, "\ue823"),
            ("Voucher Order Rate", "Orders Using Vouchers", 1, None, "\ue8ec")]
    ptype = COL("Payments", "payment_type")
    type_fills = [value_fill("Payments", "payment_type", k, v) for k, v in PAY_COLORS.items()]
    mix = chart("hundredPercentStackedColumnChart",
                {"Category": [(YM, None)], "Series": [(ptype, "Payment method")], "Y": [(M("Payment Value"), None)]},
                "Payment Mix by Month (share of value)",
                merge(axes(cat_font=8), {"dataPoint": type_fills, "labels": labels(show=False)}))
    donut = chart("donutChart", {"Category": [(ptype, "Payment method")], "Y": [(M("Payment Value"), None)]},
                  "Payment Value by Method",
                  {"dataPoint": type_fills,
                   "labels": [props(show=B(True), color=C("#E6E6E6"), fontSize=D(9), labelStyle=S("Percent of total"))],
                   "legend": [props(show=B(True), position=S("Bottom"), labelColor=C("#CFCFCF"), fontSize=D(9))],
                   "slices": [props(innerRadiusRatio=I(62))]},
                  sort=[(M("Payment Value"), "Descending")])
    inst = COL("Orders", "installment_bucket")
    charts = [
        ("pay_mix", L2, mix, [exclude_filter("Payments", "payment_type", ["Not defined"], "ex_not_defined")]),
        ("pay_donut", R2, donut, [exclude_filter("Payments", "payment_type", ["Not defined"], "ex_not_defined")]),
        ("inst_dist", L3, bars(inst, "Order Share (Installments)", "Orders by Number of Installments",
                               "Share of orders", horizontal=False, sort="asc", sort_by_category=True,
                               tooltips=["Total Orders"])),
        ("inst_aov", R3, bars(inst, "Avg Order Value", "Average Order Value by Installments", "Avg order value",
                              horizontal=False, sort="asc", sort_by_category=True, tooltips=["Delivered Orders"],
                              color=WHITE_SERIES)),
    ]
    return dict(id="payments", title="PAYMENTS",
                subtitle="Payment methods and installment behavior.", kpis=kpis, charts=charts)


PAGES = [page_overview(), page_delivery(), page_experience(), page_sellers(), page_products(), page_customers(),
         page_payments()]
for _p, (_label, _, _pid) in zip(PAGES, NAV):
    assert _p["id"] == _pid
    _p["label"] = _label
    _p["bg"] = f"bg_{_pid}.png"
    _p["kpi_icons"] = [k[4] for k in _p["kpis"]]

FOOTER = ("Sales = item price + freight of delivered orders · Cancellation = canceled + unavailable orders · "
          "YoY = latest year in the filter vs. the same period of the prior year · Scope: Jan 2017 – Aug 2018")


def page_visuals(page):
    vs = [textbox("header", (CX, 16, 860, 90), [
        [(page["title"], {**TS, "fontSize": "28pt", "fontWeight": "bold", "color": TEXT})],
        [(page["subtitle"], {**TS, "fontSize": "13pt", "color": MUTED})]], z=10)]
    vs.append(slicer("slicer_time", (1124, 22, 220, 70), [COL("Date", "Year"), COL("Date", "Month")],
                     "Order Date", "time", z=3000))
    vs.append(slicer("slicer_state", (1360, 22, 220, 70), [COL("States", "state_name")],
                     "Customer State", "state", z=3001))
    for k, (measure, label, units, prec, _) in enumerate(page["kpis"]):
        vs += kpi_visuals(k, measure, label, units, prec)
    for z, item in enumerate(page["charts"]):
        name, pos, visual = item[:3]
        filters = item[3] if len(item) > 3 else None
        vs.append(container(name, pos, visual, z=200 + z, filters=filters))
    vs.append(textbox("footer", (CX, 874, 1320, 22),
                      [[(FOOTER, {**TS, "fontSize": "8pt", "color": "#6F6F6F"})]], z=20))
    vs += [nav_button(i, pid) for i, (_, _, pid) in enumerate(NAV)]
    return vs


# ============================================================ theme
def theme():
    sol = lambda c: {"solid": {"color": c}}  # noqa: E731
    return {
        "name": "Olist Dark",
        "dataColors": [LIME, WHITE_SERIES, RED, AMBER, CYAN, SUBTLE, "#A78BFA", "#2DD4BF"],
        "foreground": TEXT, "foregroundNeutralSecondary": MUTED, "foregroundNeutralTertiary": SUBTLE,
        "background": PANEL, "backgroundLight": "#242524", "backgroundNeutral": "#2E2F2E",
        "tableAccent": LIME, "good": LIME, "neutral": AMBER, "bad": RED,
        "maximum": LIME, "center": AMBER, "minimum": RED,
        "textClasses": {
            "callout": {"fontSize": 26, "fontFace": "Segoe UI Bold", "color": TEXT},
            "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": TEXT},
            "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": TEXT},
            "label": {"fontSize": 9, "fontFace": "Segoe UI", "color": MUTED},
        },
        "visualStyles": {
            "*": {"*": {
                "background": [{"show": True, "color": sol(PANEL), "transparency": 0}],
                "border": [{"show": True, "color": sol(PANEL), "radius": 14}],
                "dropShadow": [{"show": False}],
                "title": [{"fontColor": sol(TEXT), "fontSize": 12, "fontFamily": "Segoe UI Semibold"}],
                "subTitle": [{"fontColor": sol(SUBTLE), "fontSize": 9}],
                "visualHeader": [{"background": sol(PANEL), "foreground": sol(MUTED), "border": sol(PANEL),
                                  "transparency": 0}],
                "visualTooltip": [{"background": sol("#262726"), "titleFontColor": sol(MUTED),
                                   "valueFontColor": sol(TEXT), "fontSize": 9}],
                "categoryAxis": [{"labelColor": sol(MUTED), "fontSize": 9, "showAxisTitle": False,
                                  "gridlineShow": False}],
                "valueAxis": [{"labelColor": sol(SUBTLE), "fontSize": 8, "showAxisTitle": False,
                               "gridlineColor": sol(GRID), "gridlineStyle": "dotted"}],
                "labels": [{"color": sol("#E6E6E6"), "fontSize": 8}],
                "legend": [{"labelColor": sol("#CFCFCF"), "fontSize": 9}],
            }},
            "page": {"*": {
                "background": [{"color": sol(BG), "transparency": 0}],
                "outspace": [{"color": sol(BG), "transparency": 0}],
            }},
            "slicer": {"*": {
                "items": [{"fontColor": sol(TEXT), "background": sol(PANEL), "textSize": 10}],
                "header": [{"fontColor": sol("#D9D9D9"), "textSize": 10}],
            }},
            "tableEx": {"*": {
                "columnHeaders": [{"fontColor": sol(LIME), "backColor": sol(PANEL), "fontSize": 9.5}],
                "values": [{"fontColorPrimary": sol("#E6E6E6"), "backColorPrimary": sol(PANEL),
                            "fontColorSecondary": sol("#E6E6E6"), "backColorSecondary": sol("#222322"),
                            "fontSize": 9.5}],
                "grid": [{"gridHorizontal": True, "gridHorizontalColor": sol(GRID), "gridVertical": False,
                          "outlineColor": sol(GRID), "rowPadding": 4}],
            }},
        },
    }


# ============================================================ ghi file
def write_text(path, text):
    """Ghi file; xoá bản cũ trước vì file do Power BI (qua Parallels) lưu thuộc root, chỉ xoá được chứ không ghi đè."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    path.write_text(text, encoding="utf-8")


def write_json(path, obj):
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


def platform(kind, display, seed):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": kind, "displayName": display},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid5(model_tmdl.NS, seed))},
    }


def build_model(out):
    sm = out / f"{NAME}.SemanticModel"
    definition = sm / "definition"
    # Giữ thư mục cultures/ do Power BI tự tạo (thuộc root); xoá các file TMDL cũ còn lại
    if definition.exists():
        for f in definition.rglob("*.tmdl"):
            if f.parent.name != "cultures":
                f.unlink()
    files = model_tmdl.build(DATA_FOLDER)
    if (definition / "cultures" / "en-US.tmdl").exists():
        files["model.tmdl"] += "\nref cultureInfo en-US\n"
    for rel, text in files.items():
        write_text(definition / rel, text)
    write_json(sm / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}})
    write_json(sm / ".platform", platform("SemanticModel", NAME, "model"))


def build_report(out, fonts):
    rp = out / f"{NAME}.Report"
    definition = rp / "definition"
    if definition.exists():
        shutil.rmtree(definition)
    res = rp / "StaticResources"
    reg = res / "RegisteredResources"
    write_json(reg / THEME_FILE, theme())
    base = res / "SharedResources" / "BaseThemes" / f"{BASE_THEME}.json"
    if not base.exists():
        src = Path(__file__).with_name(f"{BASE_THEME}.json")
        base.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, base)
    if fonts:
        backgrounds.build_all(reg, fonts, PAGES)

    write_json(rp / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    write_json(rp / ".platform", platform("Report", NAME, "report"))
    write_json(definition / "version.json", {
        "$schema": SCHEMA_BASE + "versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    at_import = {"visual": "2.7.0", "report": "3.2.0", "page": "2.3.1"}
    write_json(definition / "report.json", {
        "$schema": REPORT_SCHEMA,
        "themeCollection": {
            "baseTheme": {"name": BASE_THEME, "reportVersionAtImport": at_import, "type": "SharedResources"},
            "customTheme": {"name": THEME_FILE, "reportVersionAtImport": at_import, "type": "RegisteredResources"},
        },
        "objects": {
            "section": [props(verticalAlignment=S("Middle"))],
            "outspacePane": [props(expanded=B(False))],
        },
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": THEME_FILE, "path": THEME_FILE, "type": "CustomTheme"}]
                      + [{"name": p["bg"], "path": p["bg"], "type": "Image"} for p in PAGES]},
        ],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
    })
    write_json(definition / "pages" / "pages.json", {
        "$schema": SCHEMA_BASE + "pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p["id"] for p in PAGES], "activePageName": PAGES[0]["id"]})
    for p in PAGES:
        pdir = definition / "pages" / p["id"]
        image = {"name": S(p["bg"]),
                 "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1,
                                                          "ItemName": p["bg"]}}},
                 "scaling": S("Fit")}
        write_json(pdir / "page.json", {
            "$schema": PAGE_SCHEMA, "name": p["id"], "displayName": p["label"], "displayOption": "FitToPage",
            "height": PAGE_H, "width": PAGE_W,
            "objects": {"background": [props(image={"image": image}, transparency=D(0))],
                        "outspace": [props(color=C(BG), transparency=D(0))]},
        })
        for v in page_visuals(p):
            write_json(pdir / "visuals" / v["name"] / "visual.json", v)


def build_pbip(out):
    write_json(out / f"{NAME}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}})


# ============================================================ kiểm tra schema
def validate(out, schema_dir):
    from jsonschema.validators import validator_for
    from referencing import Registry, Resource

    schema_dir = Path(schema_dir)

    def retrieve(uri):
        rel = uri.split("report/definition/", 1)[1].replace("schema.embedded.json", "schema-embedded.json")
        return Resource.from_contents(json.loads((schema_dir / rel).read_text()))

    registry = Registry(retrieve=retrieve)
    cache, n_err, n_files = {}, 0, 0
    for f in sorted((out / f"{NAME}.Report" / "definition").rglob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        uri = doc.get("$schema", "")
        if "report/definition/" not in uri:
            continue
        if uri not in cache:
            schema = retrieve(uri).contents
            cache[uri] = validator_for(schema)(schema, registry=registry)
        errors = list(cache[uri].iter_errors(doc))
        n_files += 1
        for e in errors[:3]:
            n_err += 1
            print(f"  ✗ {f.relative_to(out)}: {'/'.join(map(str, e.absolute_path))}: {e.message[:200]}")
    print(f"Kiểm tra schema: {n_files} file, {n_err} lỗi")
    return n_err == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fonts", help="thư mục chứa font Segoe (để vẽ ảnh nền)")
    ap.add_argument("--schemas", help="thư mục JSON schema PBIR (report/definition) để kiểm tra")
    ap.add_argument("--out", default=str(ROOT))
    a = ap.parse_args()
    out = Path(a.out)
    build_model(out)
    build_report(out, a.fonts)
    build_pbip(out)
    # Parallels hiển thị file của user Mac (quyền 644) là ReadOnly trong Windows → Power BI mở ở chế độ chỉ đọc
    for target in [out / f"{NAME}.pbip", out / f"{NAME}.Report", out / f"{NAME}.SemanticModel"]:
        for f in [target, *target.rglob("*")] if target.is_dir() else [target]:
            try:
                f.chmod(0o777 if f.is_dir() else 0o666)
            except PermissionError:  # file do Power BI lưu (root) – Windows vẫn ghi được
                pass
    n_measures = len(model_tmdl.all_measures())
    print(f"Đã sinh {NAME}.pbip: {len(PAGES)} trang, {n_measures} measure")
    if a.schemas:
        validate(out, a.schemas)


if __name__ == "__main__":
    main()
