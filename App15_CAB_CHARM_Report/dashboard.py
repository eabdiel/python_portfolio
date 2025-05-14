import pandas as pd
import os
import sys
from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource, DataTable, TableColumn, Button, Select, Div, CustomJS, Paragraph
from bokeh.models.widgets.tables import HTMLTemplateFormatter, SelectEditor
from bokeh.plotting import figure
from bokeh.transform import cumsum
from math import pi
from bokeh.palettes import Category20, viridis

# Attempt to load export file
file_loaded = False
if os.path.exists("export.xlsx"):
    df = pd.read_excel("export.xlsx")
    file_loaded = True
elif os.path.exists("export.csv"):
    df = pd.read_csv("export.csv")
    file_loaded = True

if not file_loaded:
    curdoc().add_root(Paragraph(text="❌ Error: Please provide an 'export.xlsx' or 'export.csv' file in the same folder as this dashboard."))
    raise SystemExit("Missing 'export.xlsx' or 'export.csv'. Please place your file in the dashboard folder.")

# Format dates
for date_col in ["CAB Meeting Date", "Implementation Date"]:
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime('%Y-%m-%d')

def classify_priority(row):
    impact = row['Change Impact'].strip().lower()
    complexity = row['Change Complexity'].strip().lower()
    if impact == "low" and complexity == "low":
        return "Level 1"
    elif (impact == "medium" and complexity in ["low", "medium"]) or \
         (complexity == "medium" and impact in ["low", "medium"]) or \
         (impact == "high" and complexity == "low") or \
         (complexity == "high" and impact == "low"):
        return "Level 2"
    else:
        return "Level 3"

df["Priority Level"] = df.apply(classify_priority, axis=1)
df["Approval Status"] = "Pending Approval"
cols = df.columns.tolist()
cols.insert(0, cols.pop(cols.index("Approval Status")))
df = df[cols]

source = ColumnDataSource(df)
original_df = df.copy()

filter_columns = [
    "Priority Level", "Approval Status", "Change ID", "Status",
    "CAB Meeting Date", "Cycle Description"
]
filter_widgets = []
dropdown_refs = {}

for col in filter_columns:
    unique_vals = df[col].dropna().astype(str).unique().tolist()
    unique_vals = sorted(unique_vals)
    selector = Select(
        title=f"Filter by {col}",
        options=["All"] + unique_vals,
        width=200,
        name=col
    )
    selector.value = "All"
    filter_widgets.append(selector)
    dropdown_refs[col] = selector

template = """
    <div style="background:<%= 
        {'Approved for production':'lightgreen',
         'Conditionally Approved':'lightyellow',
         'Skipped':'lightgray',
         'Pending Approval':'lightcoral'}[value] %>;">
        <%= value %>
    </div>
"""
columns = []
for col in df.columns:
    if col == "Approval Status":
        columns.append(TableColumn(
            field=col, title=col,
            editor=SelectEditor(options=[
                "Approved for production",
                "Conditionally Approved",
                "Skipped",
                "Pending Approval"
            ]),
            formatter=HTMLTemplateFormatter(template=template)
        ))
    else:
        columns.append(TableColumn(field=col, title=col))

def make_interactive_pie_chart(column_name, title, linked_dropdown=None):
    data = df[column_name].value_counts().reset_index(name='value')
    data['angle'] = data['value'] / data['value'].sum() * 2 * pi
    palette = Category20[len(data)] if len(data) <= 20 else viridis(len(data))
    data['color'] = palette
    pie_source = ColumnDataSource(data)

    pie = figure(
        height=450, width=550, title=title,
        toolbar_location=None, tools="tap",
        tooltips="@index: @value",
        x_range=(-1.1, 1.6),
        match_aspect=True
    )

    pie.wedge(
        x=0, y=1, radius=0.8,
        start_angle=cumsum('angle', include_zero=True),
        end_angle=cumsum('angle'),
        line_color="white",
        fill_color='color',
        legend_field='index',
        source=pie_source,
        muted_alpha=0.2
    )

    pie.axis.visible = False
    pie.grid.visible = False
    pie.legend.orientation = "vertical"
    pie.legend.label_text_font_size = "8pt"
    pie.legend.spacing = 6
    pie.legend.label_standoff = 8
    pie.legend.click_policy = "mute"
    pie.add_layout(pie.legend[0], 'right')

    if linked_dropdown:
        pie.js_on_event('tap', CustomJS(args=dict(pie_source=pie_source, dropdown=linked_dropdown), code="""
            const selected = pie_source.selected.indices[0];
            if (selected == null || selected === undefined) return;
            const value = pie_source.data['index'][selected];
            dropdown.value = value;
        """))

    return pie

def persist_approval_status_edits():
    edited = source.to_df()
    original_df["Approval Status"] = original_df["Change ID"].map(
        edited.set_index("Change ID")["Approval Status"]
    ).fillna(original_df["Approval Status"])

def apply_filters():
    persist_approval_status_edits()
    filtered = original_df.copy()
    for selector in filter_widgets:
        colname = selector.name
        selected_val = selector.value
        if selected_val != "All":
            filtered = filtered[filtered[colname].astype(str) == str(selected_val)]
    source.data = filtered.to_dict(orient="list")

def reset_filters():
    persist_approval_status_edits()
    for selector in filter_widgets:
        selector.value = "All"
    source.data = original_df.to_dict(orient="list")

priority_pie = make_interactive_pie_chart("Priority Level", "Priority Level", linked_dropdown=dropdown_refs["Priority Level"])
status_pie = make_interactive_pie_chart("Status", "Status", linked_dropdown=dropdown_refs["Status"])
cycle_pie = make_interactive_pie_chart("Cycle Description", "Cycle Description", linked_dropdown=dropdown_refs["Cycle Description"])

apply_button = Button(label="Apply Filters", button_type="primary")
apply_button.on_click(apply_filters)

reset_button = Button(label="Reset Filters", button_type="warning")
reset_button.on_click(reset_filters)

save_button = Button(label="Save Report", button_type="success")
def save_callback():
    result_df = source.to_df()
    result_df.to_excel("export_with_approval.xlsx", index=False)
save_button.on_click(save_callback)

data_table = DataTable(
    source=source, columns=columns,
    width=1500, height=300,
    editable=True, reorderable=True
)

layout = column(
    row(priority_pie, status_pie, cycle_pie),
    Div(text="<h3>Table Filters</h3>"),
    row(*filter_widgets),
    row(apply_button, reset_button),
    data_table,
    save_button
)

curdoc().add_root(layout)
curdoc().title = "Change Document Dashboard"
