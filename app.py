import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, dash_table

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

data = pd.read_csv("stock_data.csv", header=[0,1], index_col=0, parse_dates=True)

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
    title="Average Daily Price Move: Normal Days vs. BoC Announcement Days",
    yaxis_title="Average Absolute % Move",
    barmode="group",
    template="plotly_white",
    legend_title="Day Type",
    hoverlabel=dict(font_size=13, font_family="Arial"),
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False),
    bargap=0.3,
    bargroupgap=0.1
)

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
    textposition="outside"
))
fig2.update_layout(
    title="Which Bank Reacts Most to BoC Announcements?",
    yaxis_title="Change in Avg. Absolute Move (%)",
    template="plotly_white",
    showlegend=False,
    margin=dict(l=100, t=80),
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False)
)
fig2.add_hline(y=0, line_width=1, line_color="black")

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
fig3.update_layout(template="plotly_white")

# --- Summary Table ---
summary_table = pd.DataFrame({
    "Bank": [bank_names[t] for t in tickers],
    "Normal Day Avg Move (%)": comparison.loc["Normal Day"].round(3).values,
    "Announcement Day Avg Move (%)": comparison.loc["Announcement Day"].round(3).values,
    "Difference (%)": (comparison.loc["Announcement Day"] - comparison.loc["Normal Day"]).round(3).values
})
summary_table = summary_table.sort_values("Difference (%)", ascending=False)

table_component = dash_table.DataTable(
    data=summary_table.to_dict("records"),
    columns=[{"name": c, "id": c} for c in summary_table.columns],
    style_cell={"textAlign": "center", "fontFamily": "Arial", "padding": "10px", "fontSize": "14px"},
    style_header={"backgroundColor": "#F5F5F5", "fontWeight": "bold"},
    style_table={"marginTop": "20px"}
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
    fig4.add_vline(x=d, line_width=1, line_dash="dash", line_color="gray", opacity=0.4)

buttons = [dict(label="All Banks", method="update", args=[{"visible": [True] * len(tickers)}])]
for i, ticker in enumerate(tickers):
    visibility = [False] * len(tickers)
    visibility[i] = True
    buttons.append(dict(label=bank_names[ticker], method="update", args=[{"visible": visibility}]))

fig4.update_layout(
    title="Bank Stock Price Over Time",
    yaxis_title="Closing Price (CAD)",
    xaxis_title="Date",
    template="plotly_white",
    hoverlabel=dict(font_size=13, font_family="Arial"),
    updatemenus=[dict(buttons=buttons, direction="down", showactive=True, x=1.0, xanchor="right", y=1.15, yanchor="top")]
)

# --- About section ---
about_section = html.Div(style={
    "marginTop": "50px",
    "padding": "30px",
    "backgroundColor": "#F9F9F9",
    "borderRadius": "8px"
}, children=[
    html.H2("About This Project", style={"color": "#1A1A1A", "marginBottom": "15px"}),
    html.P([
        "This dashboard explores whether Bank of Canada interest rate announcements ",
        "cause noticeably larger price movements in Canada's Big Five bank stocks compared to typical trading days."
    ], style={"color": "#333333", "lineHeight": "1.6"}),
    html.H4("Data Sources", style={"color": "#1A1A1A", "marginTop": "20px"}),
    html.P([
        "Stock price data was pulled via the yfinance library (Yahoo Finance). ",
        "Bank of Canada rate announcement dates were sourced from the Bank of Canada's public schedule."
    ], style={"color": "#333333", "lineHeight": "1.6"}),
    html.H4("Methodology", style={"color": "#1A1A1A", "marginTop": "20px"}),
    html.P([
        "\"Announcement day\" refers to trading days on which the Bank of Canada made a scheduled rate decision. ",
        "Daily volatility is measured as the absolute percentage change in closing price. ",
        "Analysis covers January 2025 through August 2026, spanning 13 rate announcements."
    ], style={"color": "#333333", "lineHeight": "1.6"}),
    html.H4("Disclaimer", style={"color": "#1A1A1A", "marginTop": "20px"}),
    html.P([
        "This is a personal portfolio project built for educational and demonstrative purposes. ",
        "It is not financial advice."
    ], style={"color": "#666666", "fontStyle": "italic", "lineHeight": "1.6"}),
    html.P([
        "Built by Dhanush Chandar Sivakumar — ",
        html.A("LinkedIn", href="https://www.linkedin.com/in/dhanush-chandar-sivakumar/", target="_blank")
    ], style={"marginTop": "20px", "color": "#333333"})
])

# --- Raw data table ---
raw_data = returns.reset_index()
raw_data.columns = ["Date"] + [bank_names[t] for t in tickers] + ["Is Announcement Day"]
raw_data = raw_data.round(3)

raw_table = dash_table.DataTable(
    data=raw_data.to_dict("records"),
    columns=[{"name": c, "id": c} for c in raw_data.columns],
    page_size=15,
    style_cell={"textAlign": "center", "fontFamily": "Arial", "padding": "8px", "fontSize": "13px"},
    style_header={"backgroundColor": "#F5F5F5", "fontWeight": "bold"},
    style_table={"marginTop": "20px", "overflowX": "auto"}
)

# --- Dash app ---
app = Dash(__name__)
server = app.server  # needed for Render deployment

app.layout = html.Div(children=[

    html.Div(className="header", children=[
        html.P("BANK OF CANADA RATE ANALYSIS", className="eyebrow"),
        html.H1("Rate Days: How the Big Five React to BoC Announcements"),
        html.P("An analysis of Canadian bank stock behaviour around Bank of Canada rate announcements"),
    ]),

    html.Div(className="body-container", children=[

        html.Div(className="grid-2col", children=[
            html.Div(className="card", children=[dcc.Graph(figure=fig1, config={"responsive": True})]),
            html.Div(className="card", children=[dcc.Graph(figure=fig2, config={"responsive": True})]),
        ]),

        html.Div(className="card", children=[
            html.H3("Summary Table"),
            table_component,
        ]),

        html.Div(className="card", children=[dcc.Graph(figure=fig3, config={"responsive": True})]),
        html.Div(className="card", children=[dcc.Graph(figure=fig4, config={"responsive": True})]),

        html.Div(className="card", children=[
            html.H3("Raw Data"),
            raw_table
        ]),

        html.Div(className="card", children=about_section.children),
    ]),

    html.Div(className="footer", children=[
        html.P("Built by Dhanush Chandar Sivakumar")
    ])
])

if __name__ == "__main__":
    app.run(debug=False)