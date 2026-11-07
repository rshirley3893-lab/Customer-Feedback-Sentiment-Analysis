"""
Plotly chart builders, kept separate from app.py so styling stays consistent
across pages and app.py stays focused on layout.
"""

import plotly.graph_objects as go

COLORS = {
    "Positive": "#22A559",
    "Neutral": "#2F6FED",
    "Negative": "#F97316",
    "Urgent Negative": "#DC2626",
    "line": "#2F6FED",
    "grid": "#EAEDF3",
    "text": "#5B6472",
}


def satisfaction_trend_figure(df):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["week"].astype(str),
            y=df["satisfaction"],
            mode="lines+markers",
            line=dict(color=COLORS["line"], width=3, shape="spline"),
            marker=dict(size=7, color=COLORS["line"]),
            fill="tozeroy",
            fillcolor="rgba(47,111,237,0.08)",
            hovertemplate="Week of %{x}<br>Satisfaction: %{y}%<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=280,
        yaxis=dict(range=[0, 100], ticksuffix="%", gridcolor=COLORS["grid"], zeroline=False),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=COLORS["text"], size=12),
    )
    return fig


def sentiment_donut_figure(dist_df):
    order = ["Positive", "Neutral", "Negative", "Urgent Negative"]
    dist_df = dist_df.set_index("sentiment").reindex(order).reset_index()
    fig = go.Figure(
        data=[
            go.Pie(
                labels=dist_df["sentiment"],
                values=dist_df["count"],
                hole=0.62,
                marker=dict(colors=[COLORS[s] for s in dist_df["sentiment"]]),
                textinfo="none",
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
                sort=False,
            )
        ]
    )
    total = int(dist_df["count"].sum())
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=230,
        showlegend=False,
        annotations=[dict(text=f"{total:,}<br><span style='font-size:11px'>Tickets</span>", x=0.5, y=0.5,
                           font=dict(size=20, color="#1A2033"), showarrow=False)],
        paper_bgcolor="white",
    )
    return fig


def negative_sparkline_figure(df):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["day"].astype(str),
            y=df["negative_pct"],
            mode="lines",
            line=dict(color="#DC2626", width=2, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(220,38,38,0.08)",
            hovertemplate="%{x}: %{y}%<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=70,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def top_issues_figure(issues_df):
    issues_df = issues_df.sort_values(issues_df.columns[1])
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=issues_df.iloc[:, 1],
            y=issues_df.iloc[:, 0],
            orientation="h",
            marker=dict(color=COLORS["line"]),
            text=issues_df.iloc[:, 1],
            textposition="outside",
            hovertemplate="%{y}: %{x} tickets<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=30, t=10, b=10),
        height=260,
        xaxis=dict(visible=False),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=COLORS["text"], size=12),
    )
    return fig


def topic_over_time_figure(df):
    """df expected to have columns: day, topic, count"""
    fig = go.Figure()
    palette = ["#2F6FED", "#22A559", "#F97316", "#A855F7", "#DC2626", "#0EA5E9", "#EAB308", "#64748B"]
    for i, topic in enumerate(sorted(df["topic"].unique())):
        sub = df[df["topic"] == topic]
        fig.add_trace(
            go.Scatter(
                x=sub["day"].astype(str),
                y=sub["count"],
                mode="lines",
                stackgroup="one",
                name=topic,
                line=dict(width=0.5, color=palette[i % len(palette)]),
            )
        )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
        font=dict(color=COLORS["text"], size=11),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor=COLORS["grid"]),
    )
    return fig
