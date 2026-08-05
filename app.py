import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output, State, ctx

# --- Data pull ---
tickers = ["RY.TO", "TD.TO", "BMO.TO", "BNS.TO", "CM.TO"]
bank_names = {
    "RY.TO": "Royal Bank",
    "TD.TO": "TD Bank",
    "BMO.TO": "Bank of Montreal",
    "BNS.TO": "Scotiabank",
    "CM.TO": "CIBC"
}
colors = {
    "RY.TO": "#6B8CAE",
    "TD.TO": "#7FA88C",
    "BMO.TO": "#B08968",
    "BNS.TO": "#C9A227",
    "CM.TO": "#A6656E",
}

data = yf.download(tickers, start="2025-01-01", end="2026-08-04", group_by="ticker")

# --- BoC announcement dates ---
boc_dates = pd.to_datetime([
    "2025-01-29", "2025-03-12", "2025-04-16", "2025-06-04",
    "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-10", "2026-07-15"
])

all_dates = data.index
is_announcement = all_dates.isin(boc_dates)
announcement_flags = pd.Series(is_announcement, index=all_dates, name="is_announcement")

# --- Returns ---
returns = pd.DataFrame(index=data.index)
for ticker in tickers:
    returns[ticker] = data[ticker]["Close"].pct_change() * 100
returns["is_announcement"] = announcement_flags

# --- Comparison table ---
abs_returns = returns[tickers].abs()
abs_returns["is_announcement"] = returns["is_announcement"]
comparison = abs_returns.groupby("is_announcement")[tickers].mean()
comparison.index = ["Normal Day", "Announcement Day"]

CHART_FONT = dict(family="Inter, sans-serif", color="#0F1B2D", size=11)
CHART_LAYOUT = dict(
    template="plotly_white",
    font=CHART_FONT,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=16, t=52, b=44),
    height=400,
    autosize=True,
    hoverlabel=dict(font_size=12, font_family="Inter, sans-serif", bgcolor="#0F1B2D", font_color="#F4F6F8"),
)

# --- Fig 1: Grouped bar ---
sorted_tickers = comparison.loc["Announcement Day"].sort_values(ascending=False).index

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=[bank_names[t] for t in sorted_tickers],
    y=comparison.loc["Normal Day", sorted_tickers],
    name="Normal Day",
    marker_color=[colors[t] for t in sorted_tickers],
    opacity=0.45,
    hovertemplate="%{x}<br>Normal Day: %{y:.2f}%<extra></extra>",
    showlegend=False
))
fig1.add_trace(go.Bar(
    x=[bank_names[t] for t in sorted_tickers],
    y=comparison.loc["Announcement Day", sorted_tickers],
    name="Announcement Day",
    marker_color=[colors[t] for t in sorted_tickers],
    opacity=1.0,
    hovertemplate="%{x}<br>Announcement Day: %{y:.2f}%<extra></extra>",
    showlegend=False
))
fig1.add_trace(go.Bar(x=[None], y=[None], name="Normal Day", marker_color="#999999", opacity=0.45))
fig1.add_trace(go.Bar(x=[None], y=[None], name="Announcement Day", marker_color="#999999", opacity=1.0))
fig1.update_layout(
    **CHART_LAYOUT,
    title=dict(text="Normal Days vs. Announcement Days", font=dict(size=14, family="Inter, sans-serif", color="#0F1B2D")),
    yaxis_title="Average Absolute % Move",
    barmode="group",
    legend_title="Day Type",
    xaxis=dict(showgrid=False, zeroline=False, tickangle=0),
    yaxis=dict(showgrid=True, gridcolor="rgba(15,27,45,0.06)", zeroline=False),
    bargap=0.3,
    bargroupgap=0.1
)
fig1.update_layout(height=420)

# --- Fig 2: Headline "who reacts most" chart ---
fig2 = go.Figure()
impact_diff = comparison.loc["Announcement Day"] - comparison.loc["Normal Day"]
impact_diff_sorted = impact_diff.sort_values(ascending=False)
bank_labels = [bank_names[t] for t in impact_diff_sorted.index]
bar_colors = [colors[t] for t in impact_diff_sorted.index]
fig2.add_trace(go.Bar(
    x=bank_labels,
    y=impact_diff_sorted.values,
    marker_color=bar_colors,
    text=[f"{v:+.2f}%" for v in impact_diff_sorted.values],
    textposition="outside",
    textfont=dict(family="Inter, sans-serif", size=12, color="#0F1B2D"),
    hovertemplate="%{x}<br>Impact: %{y:+.2f}%<extra></extra>",
))
fig2.update_layout(
    template="plotly_white",
    font=CHART_FONT,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=420,
    autosize=True,
    hoverlabel=dict(font_size=12, font_family="Inter, sans-serif", bgcolor="#0F1B2D", font_color="#F4F6F8"),
    title=dict(text="Who Reacts Most?", font=dict(size=14, family="Inter, sans-serif", color="#0F1B2D")),
    yaxis_title="Change in Avg. Absolute Move (%)",
    showlegend=False,
    margin=dict(l=48, r=24, t=72, b=48),
    xaxis=dict(showgrid=False, zeroline=False, tickangle=0),
    yaxis=dict(showgrid=True, gridcolor="rgba(15,27,45,0.06)", zeroline=False, range=[-0.35, 0.45]),
)
fig2.add_hline(y=0, line_width=1, line_color="#0F1B2D", opacity=0.35)

# --- Fig 3: Correlation heatmap ---
corr_matrix = returns[tickers].corr()
corr_matrix.index = [bank_names[t] for t in tickers]
corr_matrix.columns = [bank_names[t] for t in tickers]
fig3 = px.imshow(
    corr_matrix,
    text_auto=".2f",
    color_continuous_scale="Blues",
    zmin=0, zmax=1,
    title="How Closely Do the Big Five Move Together?"
)
fig3.update_traces(hovertemplate="%{y} vs %{x}<br>Correlation: %{z:.2f}<extra></extra>")
fig3.update_layout(
    **CHART_LAYOUT,
    title=dict(text="How Closely Do the Big Five Move Together?", font=dict(size=14, family="Inter, sans-serif", color="#0F1B2D")),
    coloraxis_colorbar=dict(title="Corr", thickness=12, len=0.7),
)
fig3.update_layout(height=420)

# --- Summary Table ---
summary_table = pd.DataFrame({
    "Bank": [bank_names[t] for t in tickers],
    "Normal Day Avg Move (%)": comparison.loc["Normal Day"].round(3).values,
    "Announcement Day Avg Move (%)": comparison.loc["Announcement Day"].round(3).values,
    "Difference (%)": (comparison.loc["Announcement Day"] - comparison.loc["Normal Day"]).round(3).values
})
summary_table = summary_table.sort_values("Difference (%)", ascending=False)

TABLE_CELL = {
    "textAlign": "center",
    "fontFamily": "Inter, sans-serif",
    "padding": "11px 14px",
    "fontSize": "13px",
    "color": "#0F1B2D",
    "border": "none",
    "backgroundColor": "#FFFFFF",
    "minWidth": "96px",
    "width": "120px",
    "maxWidth": "180px",
    "whiteSpace": "nowrap",
}
TABLE_HEADER = {
    "backgroundColor": "#EEF1F5",
    "fontWeight": "600",
    "color": "#0F1B2D",
    "fontFamily": "Inter, sans-serif",
    "fontSize": "11px",
    "textTransform": "uppercase",
    "letterSpacing": "0.06em",
    "border": "none",
    "padding": "11px 14px",
    "whiteSpace": "nowrap",
}

table_component = dash_table.DataTable(
    data=summary_table.to_dict("records"),
    columns=[{"name": c, "id": c} for c in summary_table.columns],
    style_cell=TABLE_CELL,
    style_header=TABLE_HEADER,
    style_cell_conditional=[
        {
            "if": {"column_id": "Bank"},
            "position": "sticky",
            "left": 0,
            "zIndex": 1,
            "minWidth": "120px",
            "width": "140px",
            "backgroundColor": "#FFFFFF",
        },
    ],
    style_header_conditional=[
        {
            "if": {"column_id": "Bank"},
            "position": "sticky",
            "left": 0,
            "zIndex": 2,
            "backgroundColor": "#EEF1F5",
        },
    ],
    style_data_conditional=[
        {"if": {"row_index": "odd"}, "backgroundColor": "#F4F6F8"},
        {
            "if": {"column_id": "Bank", "row_index": "odd"},
            "backgroundColor": "#F4F6F8",
        },
    ],
    style_table={"overflowX": "auto", "minWidth": "100%", "borderRadius": "8px"},
)

# --- Fig 4: Time series with dropdown ---
fig4 = go.Figure()
for ticker in tickers:
    fig4.add_trace(go.Scatter(
        x=data[ticker].index,
        y=data[ticker]["Close"],
        name=bank_names[ticker],
        line=dict(color=colors[ticker], width=2),
        hovertemplate="%{x|%b %d, %Y}<br>$%{y:.2f}<extra>" + bank_names[ticker] + "</extra>"
    ))
for d in boc_dates:
    fig4.add_vline(x=d, line_width=1, line_dash="dash", line_color="#5c6370", opacity=0.35)

buttons = [dict(label="All Banks", method="update", args=[{"visible": [True] * len(tickers)}])]
for i, ticker in enumerate(tickers):
    visibility = [False] * len(tickers)
    visibility[i] = True
    buttons.append(dict(label=bank_names[ticker], method="update", args=[{"visible": visibility}]))

fig4.update_layout(
    **CHART_LAYOUT,
    title=dict(text="Bank Stock Price Over Time", font=dict(size=14, family="Inter, sans-serif", color="#0F1B2D")),
    yaxis_title="Closing Price (CAD)",
    xaxis_title="Date",
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(15,27,45,0.06)", zeroline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    updatemenus=[dict(
        buttons=buttons,
        direction="down",
        showactive=True,
        x=1.0,
        xanchor="right",
        y=1.18,
        yanchor="top",
        bgcolor="#F4F6F8",
        bordercolor="#D8DDE5",
        font=dict(family="Inter, sans-serif", size=12, color="#0F1B2D"),
    )],
)
fig4.update_layout(height=440)

# --- Raw data table ---
raw_data = returns.reset_index()
raw_data.columns = ["Date"] + [bank_names[t] for t in tickers] + ["Is Announcement Day"]
raw_data["Date"] = pd.to_datetime(raw_data["Date"]).dt.strftime("%Y-%m-%d")
raw_data = raw_data.round(3)

raw_table = dash_table.DataTable(
    data=raw_data.to_dict("records"),
    columns=[{"name": c, "id": c} for c in raw_data.columns],
    page_size=20,
    filter_action="native",
    sort_action="native",
    style_cell=TABLE_CELL,
    style_header=TABLE_HEADER,
    style_cell_conditional=[
        {
            "if": {"column_id": "Date"},
            "position": "sticky",
            "left": 0,
            "zIndex": 1,
            "minWidth": "108px",
            "width": "120px",
            "backgroundColor": "#FFFFFF",
        },
    ],
    style_header_conditional=[
        {
            "if": {"column_id": "Date"},
            "position": "sticky",
            "left": 0,
            "zIndex": 2,
            "backgroundColor": "#EEF1F5",
        },
    ],
    style_data_conditional=[
        {"if": {"row_index": "odd"}, "backgroundColor": "#F4F6F8"},
        {
            "if": {"column_id": "Date", "row_index": "odd"},
            "backgroundColor": "#F4F6F8",
        },
        {
            "if": {"filter_query": "{Is Announcement Day} = True"},
            "backgroundColor": "rgba(166, 101, 110, 0.10)",
            "fontWeight": "500",
        },
        {
            "if": {
                "filter_query": "{Is Announcement Day} = True",
                "column_id": "Date",
            },
            "backgroundColor": "rgba(166, 101, 110, 0.10)",
        },
    ],
    style_table={"overflowX": "auto", "minWidth": "100%", "borderRadius": "8px"},
    style_filter={"backgroundColor": "#F4F6F8", "border": "none", "padding": "6px"},
)

# --- Homepage metrics ---
top_bank_ticker = impact_diff_sorted.index[0]
top_bank_name = bank_names[top_bank_ticker]
top_bank_impact = impact_diff_sorted.iloc[0]
n_announcements = len(boc_dates)
n_trading_days = len(returns.dropna(how="all"))

# --- Page layouts ---
GRAPH_CONFIG = {"responsive": True, "displayModeBar": False}


def page_home():
    return html.Div(className="page page-home", children=[
        html.Section(className="hero", children=[
            html.Div(className="hero-copy", children=[
                html.P("Rate Days", className="brand"),
                html.H1("Bank of Canada rate announcements and Big Five equity reactions"),
                html.P(
                    "Event-day absolute moves versus normal trading days across thirteen scheduled BoC decisions, January 2025–August 2026.",
                    className="hero-lede",
                ),
                html.Div(className="hero-actions", children=[
                    dcc.Link("Open dashboard", href="/dashboard", className="btn btn-primary"),
                    dcc.Link("Methodology", href="/about", className="btn btn-ghost"),
                ]),
            ]),
            html.Div(className="hero-visual", children=[
                dcc.Graph(
                    figure=fig2,
                    config=GRAPH_CONFIG,
                    className="hero-chart",
                    style={"width": "100%", "height": "380px"},
                ),
            ]),
        ]),
        html.Section(className="stat-strip", children=[
            html.Div(className="stat", children=[
                html.Span(str(n_announcements), className="stat-value"),
                html.Span("Rate announcements", className="stat-label"),
            ]),
            html.Div(className="stat", children=[
                html.Span("5", className="stat-value"),
                html.Span("Canadian banks", className="stat-label"),
            ]),
            html.Div(className="stat", children=[
                html.Span(f"{top_bank_impact:+.2f}%", className="stat-value"),
                html.Span(f"Largest impact · {top_bank_name}", className="stat-label"),
            ]),
            html.Div(className="stat", children=[
                html.Span("Jan ’25 – Aug ’26", className="stat-value stat-value--sm"),
                html.Span(f"{n_trading_days} trading days", className="stat-label"),
            ]),
        ]),
    ])


def page_dashboard():
    return html.Div(className="page", children=[
        html.Header(className="page-header", children=[
            html.P("Analysis", className="page-eyebrow"),
            html.H1("Dashboard"),
            html.P("Event-day absolute moves versus normal trading days for RY, TD, BMO, BNS, and CM."),
        ]),
        html.Div(className="card", children=[
            html.Div(className="card-label", children="Volatility"),
            dcc.Graph(figure=fig1, config=GRAPH_CONFIG, className="chart", style={"width": "100%", "height": "420px"}),
        ]),
        html.Div(className="card", children=[
            html.Div(className="card-label", children="Relative impact"),
            dcc.Graph(figure=fig2, config=GRAPH_CONFIG, className="chart", style={"width": "100%", "height": "420px"}),
        ]),
        html.Div(className="card", children=[
            html.Div(className="card-header", children=[
                html.Div(className="card-label", children="Summary"),
                html.H2("Bank-level average moves"),
            ]),
            html.Div(className="table-scroll", children=[table_component]),
        ]),
        html.Div(className="card", children=[
            html.Div(className="card-label", children="Co-movement"),
            dcc.Graph(figure=fig3, config=GRAPH_CONFIG, className="chart", style={"width": "100%", "height": "420px"}),
        ]),
        html.Div(className="card", children=[
            html.Div(className="card-label", children="Price path"),
            dcc.Graph(figure=fig4, config=GRAPH_CONFIG, className="chart", style={"width": "100%", "height": "440px"}),
        ]),
    ])


def page_raw_data():
    return html.Div(className="page", children=[
        html.Header(className="page-header", children=[
            html.P("Dataset", className="page-eyebrow"),
            html.H1("Raw Data"),
            html.P("Daily percentage returns for each bank. Announcement days are highlighted."),
        ]),
        html.Div(className="card card--flush", children=[
            html.Div(className="card-header", children=[
                html.Div(className="card-label", children="Daily returns (%)"),
                html.P("Filter and sort any column. Announcement rows are tinted.", className="card-hint"),
            ]),
            html.Div(className="table-scroll", children=[raw_table]),
        ]),
    ])


def page_about():
    return html.Div(className="page", children=[
        html.Header(className="page-header", children=[
            html.P("Context", className="page-eyebrow"),
            html.H1("About"),
            html.P("Why this project exists and how the numbers were built."),
        ]),
        html.Div(className="about-grid", children=[
            html.Article(className="card about-card", children=[
                html.H2("The question"),
                html.P(
                    "This dashboard explores whether Bank of Canada interest rate announcements "
                    "cause noticeably larger price movements in Canada's Big Five bank stocks "
                    "compared to typical trading days."
                ),
            ]),
            html.Article(className="card about-card", children=[
                html.H2("Data sources"),
                html.P(
                    "Stock price data was pulled via the yfinance library (Yahoo Finance). "
                    "Bank of Canada rate announcement dates were sourced from the Bank of Canada's public schedule."
                ),
            ]),
            html.Article(className="card about-card", children=[
                html.H2("Methodology"),
                html.P(
                    '"Announcement day" refers to trading days on which the Bank of Canada made a scheduled rate decision. '
                    "Daily volatility is measured as the absolute percentage change in closing price. "
                    "Analysis covers January 2025 through August 2026, spanning 13 rate announcements."
                ),
            ]),
            html.Article(className="card about-card about-card--wide", children=[
                html.H2("Disclaimer"),
                html.P(
                    "This is a personal portfolio project built for educational and demonstrative purposes. "
                    "It is not financial advice.",
                    className="disclaimer",
                ),
                html.P(className="about-credit", children=[
                    "Built by Dhanush Chandar Sivakumar — ",
                    html.A(
                        "LinkedIn",
                        href="https://www.linkedin.com/in/dhanush-chandar-sivakumar/",
                        target="_blank",
                        rel="noopener noreferrer",
                    ),
                ]),
            ]),
        ]),
    ])


def page_not_found():
    return html.Div(className="page page-empty", children=[
        html.H1("Page not found"),
        html.P("That route doesn't exist."),
        dcc.Link("Back home", href="/", className="btn btn-primary"),
    ])


NAV_ITEMS = [
    ("/", "Home", "nav-home"),
    ("/dashboard", "Dashboard", "nav-dashboard"),
    ("/raw-data", "Raw Data", "nav-raw"),
    ("/about", "About", "nav-about"),
]


def is_active_path(href, pathname):
    path = pathname or "/"
    if href == "/":
        return path in ("/", "")
    return path == href or path.startswith(href)


def build_sidebar():
    links = [
        dcc.Link(
            label,
            href=href,
            id=link_id,
            className="nav-link",
        )
        for href, label, link_id in NAV_ITEMS
    ]
    return html.Aside(id="sidebar", className="sidebar", children=[
        html.Nav(className="sidebar-nav", children=links),
    ])


# --- Dash app ---
app = Dash(__name__, suppress_callback_exceptions=True, title="Rate Days · BoC Big Five")
server = app.server

app.layout = html.Div(className="app-shell", children=[
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="nav-open", data=False),
    html.Header(className="mobile-topbar", children=[
        html.Button(
            [
                html.Span(className="nav-toggle-bar"),
                html.Span(className="nav-toggle-bar"),
                html.Span(className="nav-toggle-bar"),
            ],
            id="nav-toggle",
            className="nav-toggle",
            n_clicks=0,
            type="button",
            **{"aria-label": "Toggle navigation"},
        ),
        html.Span("Rate Days", className="mobile-topbar-title"),
    ]),
    html.Div(id="nav-overlay", className="nav-overlay", n_clicks=0),
    build_sidebar(),
    html.Main(className="main", children=[
        html.Div(id="page-content", className="page-content"),
        html.Footer(className="footer", children=[
            html.P("Built by Dhanush Chandar Sivakumar"),
        ]),
    ]),
])


@app.callback(
    Output("page-content", "children"),
    Output("nav-home", "className"),
    Output("nav-dashboard", "className"),
    Output("nav-raw", "className"),
    Output("nav-about", "className"),
    Input("url", "pathname"),
)
def render_page(pathname):
    path = pathname or "/"
    if path in ("/", ""):
        content = page_home()
    elif path == "/dashboard":
        content = page_dashboard()
    elif path == "/raw-data":
        content = page_raw_data()
    elif path == "/about":
        content = page_about()
    else:
        content = page_not_found()

    classes = [
        "nav-link" + (" is-active" if is_active_path(href, path) else "")
        for href, _, _ in NAV_ITEMS
    ]
    return content, *classes


@app.callback(
    Output("sidebar", "className"),
    Output("nav-overlay", "className"),
    Output("nav-open", "data"),
    Input("nav-toggle", "n_clicks"),
    Input("nav-overlay", "n_clicks"),
    Input("url", "pathname"),
    State("nav-open", "data"),
)
def sync_mobile_nav(toggle_clicks, overlay_clicks, pathname, is_open):
    triggered = ctx.triggered_id
    open_state = bool(is_open)
    if triggered == "nav-toggle":
        open_state = not open_state
    else:
        open_state = False
    return (
        "sidebar is-open" if open_state else "sidebar",
        "nav-overlay is-visible" if open_state else "nav-overlay",
        open_state,
    )


if __name__ == "__main__":
    app.run(debug=False)
