"""
SAP BPCA Risk Analysis Dashboard (Bokeh + PyRFC)
Author: Edwin Rodriguez (Arthrex IT SAP COE)
Date: 2025-10-22

Enhancements:
 - Proper field slicing via OFFSET/LENGTH for alignment
 - Auto-truncate long fields for readability
 - Resizable / scrollable table columns
"""

import pandas as pd
from bokeh.models import (
    ColumnDataSource, TextInput, Select, Button,
    DataTable, TableColumn, Div
)
from bokeh.plotting import curdoc, figure
from bokeh.layouts import column, row
from sap_connector import connect_sso


# ---------------------------------------------------------------------
# Connect to SAP
# ---------------------------------------------------------------------
conn = connect_sso()


# ---------------------------------------------------------------------
# RFC helper
# ---------------------------------------------------------------------
def rfc_read_table(table, fields=None, options=None, rowcount=50, rowskips=0):
    """RFC_READ_TABLE with correct field slicing and auto-truncation."""
    payload = {
        "QUERY_TABLE": table,
        "ROWCOUNT": int(rowcount),
        "ROWSKIPS": int(rowskips),
    }
    if fields:
        payload["FIELDS"] = [{"FIELDNAME": f} for f in fields]
    if options:
        payload["OPTIONS"] = [{"TEXT": line} for line in options if line]

    result = conn.call("RFC_READ_TABLE", **payload)
    field_defs = result["FIELDS"]
    rows = result["DATA"]

    parsed_rows = []
    for row in rows:
        wa = row["WA"]
        parsed = {}
        for f in field_defs:
            name = f["FIELDNAME"]
            off = int(f["OFFSET"])
            length = int(f["LENGTH"])
            value = wa[off:off+length].strip()

            # Auto truncate overly long fields (e.g., OBJ_NAME)
            if len(value) > 80:
                value = value[:77] + "..."
            parsed[name] = value
        parsed_rows.append(parsed)

    df = pd.DataFrame(parsed_rows)
    return df


# ---------------------------------------------------------------------
# Chunked join logic
# ---------------------------------------------------------------------
def fetch_bpca_join(result_id=None, obj_type=None, limit=50):
    """Chunked field fetch with alignment-aware parsing."""
    print(f"📡 Fetching BPCA data (limit={limit}) with chunked RFC_READ_TABLE calls")

    # Split large tables into safe field groups
    field_chunks = [
        ["ID", "GUID", "AS4POS", "TRKORR", "PGMID", "OBJECT", "OBJ_NAME", "OBJ_CLASS_TYPE"],
        ["ID", "GUID", "OBJ_CLASS_VALUE", "DEVCLASS", "DLVUNIT", "OBJ_SOURCE", "EVENT", "EVENT_TYPE"],
        ["ID", "GUID", "CRITICALITY", "LOGICAL_COMP", "BFUNCTION", "TR_PGMID", "TR_OBJECT", "TR_OBJ_NAME"],
        ["ID", "GUID", "TAB_HAS_KEY", "SAP_CODE_MODIF", "SAP_CODE_AFFCC", "CUST_CODE", "ITERATION_NO"],
    ]

    tb_opts = []
    if result_id:
        tb_opts.append(f"ID = '{result_id}'")
    if obj_type:
        tb_opts.append(f"OBJECT = '{obj_type}'")

    tb_df_full = None
    for i, fields in enumerate(field_chunks, start=1):
        try:
            df_chunk = rfc_read_table(
                "AGS_BPCA_ISECTTB",
                fields=fields,
                options=tb_opts,
                rowcount=int(limit),
            )
            if df_chunk.empty:
                print(f"⚠️ Chunk {i} returned no data.")
                continue
            print(f"✅ Chunk {i}: {len(df_chunk)} rows, {len(fields)} cols")
            tb_df_full = df_chunk if tb_df_full is None else pd.merge(
                tb_df_full, df_chunk, on=["ID", "GUID"], how="outer"
            )
        except Exception as e:
            print(f"❌ Chunk {i} failed: {e}")

    if tb_df_full is None or tb_df_full.empty:
        print("❌ No data returned from AGS_BPCA_ISECTTB.")
        return pd.DataFrame()

    # Header merge
    it_fields = ["ID", "ITEM_ID", "SCOPE_TYPE", "SCOPE_ID", "GUID"]
    it_opts = [f"ID = '{result_id}'"] if result_id else []
    try:
        it_df = rfc_read_table("AGS_BPCA_ISECTIT", fields=it_fields, options=it_opts, rowcount=2000)
        print(f"✅ Header table rows: {len(it_df)}")
    except Exception as e:
        print(f"⚠️ Could not read header table: {e}")
        it_df = pd.DataFrame(columns=it_fields)

    merged = pd.merge(tb_df_full, it_df, on=["ID", "GUID"], how="inner")

    ordered_cols = [
        "ID", "ITEM_ID", "SCOPE_TYPE", "SCOPE_ID", "GUID",
        "AS4POS", "TRKORR", "PGMID", "OBJECT", "OBJ_NAME",
        "OBJ_CLASS_TYPE", "OBJ_CLASS_VALUE", "DEVCLASS", "DLVUNIT",
        "OBJ_SOURCE", "EVENT", "EVENT_TYPE", "CRITICALITY", "LOGICAL_COMP",
        "BFUNCTION", "TR_PGMID", "TR_OBJECT", "TR_OBJ_NAME", "TAB_HAS_KEY",
        "SAP_CODE_MODIF", "SAP_CODE_AFFCC", "CUST_CODE", "ITERATION_NO"
    ]
    merged = merged[[c for c in ordered_cols if c in merged.columns]]

    print(f"✅ Total merged rows: {len(merged)}")
    return merged.head(int(limit))


def fetch_bpca(result_id=None, obj_type=None, limit=50):
    """
    Fetch BPCA data from AGS_BPCA_GET_INTERSCTION_INFO
    using IV_RESULT_ID (auto-padded to 10 chars).
    Pulls:
        • ID, TRKORR, OBJ_NAME, OBJE from ET_BPCA_INTERSECTION
        • TEXT, CREATEDBY, CREATEDAT, UNUSED_OBJ_ from ES_BPCA_HEAD
    """
    if not result_id:
        print("⚠️ Please enter a Result ID to query.")
        return pd.DataFrame(columns=["ID", "TRKORR", "OBJ_NAME", "OBJE", "TEXT", "CREATEDBY", "CREATEDAT", "UNUSED_OBJ_"])

    try:
        # Normalize and pad the Result ID
        rid = result_id.strip()
        if rid.isdigit():
            rid = rid.zfill(10)
        print(f"📡 Calling FM AGS_BPCA_GET_INTERSCTION_INFO with IV_RESULT_ID={rid}")

        # Execute FM call
        result = conn.call("AGS_BPCA_GET_INTERSCTION_INFO", IV_RESULT_ID=rid)

        # --- Extract intersection table ---
        intersections = result.get("ET_BPCA_INTERSECTION", [])
        if not intersections:
            print("⚠️ FM returned no intersection data.")
            return pd.DataFrame(columns=["ID", "TRKORR", "OBJ_NAME", "OBJE", "TEXT", "CREATEDBY", "CREATEDAT", "UNUSED_OBJ_"])

        df_main = pd.DataFrame(intersections)

        # Keep only relevant columns for now
        expected_cols = ["ID", "TRKORR", "OBJ_NAME", "OBJE"]
        df_main = df_main[[c for c in expected_cols if c in df_main.columns]]

        # --- Extract header info ---
        head = result.get("ES_BPCA_HEAD", {})
        meta = {
            "TEXT": head.get("TEXT", ""),
            "CREATEDBY": head.get("CREATEDBY", ""),
            "CREATEDAT": head.get("CREATEDAT", ""),
            "UNUSED_OBJ_": head.get("UNUSED_OBJ_", ""),
        }

        # Apply same meta info to each row
        for k, v in meta.items():
            df_main[k] = v

        # Optional object type filter
        if obj_type and "OBJE" in df_main.columns:
            df_main = df_main[df_main["OBJE"].str.upper() == obj_type.upper()]

        # Truncate long text fields
        for col in df_main.columns:
            df_main[col] = df_main[col].astype(str).apply(lambda x: x[:77] + "..." if len(x) > 80 else x)

        # Apply row limit
        df_main = df_main.head(int(limit))

        print(f"✅ Retrieved {len(df_main)} rows with header info.")
        return df_main

    except Exception as e:
        print(f"❌ FM call failed: {e}")
        return pd.DataFrame(columns=["ID", "TRKORR", "OBJ_NAME", "OBJE", "TEXT", "CREATEDBY", "CREATEDAT", "UNUSED_OBJ_"])


# ---------------------------------------------------------------------
# UI setup
# ---------------------------------------------------------------------
df = pd.DataFrame(columns=["ID", "OBJECT", "OBJ_NAME", "OBJ_CLASS_TYPE", "DEVCLASS", "CRITICALITY"])
source = ColumnDataSource(df)

header = Div(text="<h2>BPCA Risk Analysis Dashboard</h2>")

result_input = TextInput(title="Result ID (required)", placeholder="e.g. 0000006411")
object_input = TextInput(title="Object Type (optional)", placeholder="e.g. PROG, CLAS, FUGR")

limit_select = Select(title="Max Rows", value="50", options=["25", "50", "75", "100", "200", "500"])
refresh_button = Button(label="Run Query", button_type="primary")


# ---------------------------------------------------------------------
# Table and Chart
# ---------------------------------------------------------------------
def build_columns(df):
    show_cols = df.columns.tolist()[:12] if not df.empty else ["ID", "OBJECT", "OBJ_NAME", "CRITICALITY"]
    return [TableColumn(field=c, title=c) for c in show_cols]


columns = build_columns(df)
data_table = DataTable(
    source=source,
    columns=columns,
    width=1400,
    height=420,
    scroll_to_selection=True,
    sortable=True,
    reorderable=True,
    selectable=True,
    fit_columns=False,
    sizing_mode="stretch_width",
    autosize_mode="fit_viewport"
)

def make_chart(df):
    if df.empty or "OBJECT" not in df.columns:
        p = figure(title="No Data Found", height=300)
        return p
    chart_df = df["OBJECT"].value_counts().reset_index()
    chart_df.columns = ["Object Type", "Count"]
    p = figure(
        x_range=chart_df["Object Type"].astype(str).tolist(),
        height=300,
        title="Object Type Distribution",
        toolbar_location=None,
        tools=""
    )
    p.vbar(x=chart_df["Object Type"], top=chart_df["Count"], width=0.8)
    p.xaxis.major_label_orientation = 1
    return p

chart = make_chart(df)


# ---------------------------------------------------------------------
# Callback
# ---------------------------------------------------------------------
def update_data():
    result_val = (result_input.value or "").strip()
    obj_val = (object_input.value or "").strip() or None
    limit_val = int(limit_select.value)

    new_df = fetch_bpca(result_val, obj_val, limit_val)
    source.data = ColumnDataSource.from_df(new_df)
    data_table.columns = build_columns(new_df)

    global chart
    chart = make_chart(new_df)
    layout.children[3] = chart


refresh_button.on_click(update_data)


# ---------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------
layout = column(
    header,
    row(result_input, object_input, limit_select, refresh_button),
    Div(text="<hr>"),
    chart,
    data_table,
)

curdoc().add_root(layout)
curdoc().title = "SAP BPCA Risk Dashboard"
