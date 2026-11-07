import datetime as dt

import streamlit as st
from streamlit_option_menu import option_menu

import database as db
import charts

st.set_page_config(
    page_title="Jórim Tech | Support Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global styling — matches the Jórim Technology Solutions navy/blue PRD mock
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1300px;}
        body, .stApp {background-color: #F4F6FB;}

        section[data-testid="stSidebar"] {
            background-color: #0B1C42;
            padding-top: 0;
        }
        section[data-testid="stSidebar"] > div {padding-top: 1rem;}
        .sidebar-brand {
            color: white; font-size: 1.15rem; font-weight: 700;
            padding: 0.4rem 0.5rem 1.2rem 0.9rem; letter-spacing: 0.2px;
        }
        .sidebar-brand span {color: #6FA8FF;}

        nav[aria-label] ul {background-color: transparent !important;}

        .card {
            background: white; border-radius: 14px; padding: 1.1rem 1.3rem;
            box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
            border: 1px solid #EEF1F6;
            height: 100%;
        }
        .kpi-label {color: #6B7280; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem;}
        .kpi-value {color: #111827; font-size: 1.7rem; font-weight: 700; line-height: 1.1;}
        .kpi-sub {font-size: 0.78rem; margin-top: 0.4rem; font-weight: 600;}
        .kpi-sub.up {color: #16A34A;}
        .kpi-sub.down {color: #DC2626;}
        .kpi-sub.flat {color: #6B7280;}

        .section-title {font-size: 1.02rem; font-weight: 700; color: #111827; margin-bottom: 0.7rem;}
        .page-title {font-size: 1.55rem; font-weight: 800; color: #0B1C42; margin-bottom: 0.1rem;}
        .page-sub {color: #6B7280; font-size: 0.9rem; margin-bottom: 1.1rem;}

        .legend-row {display: flex; align-items: center; gap: 0.5rem; font-size: 0.83rem; color: #374151; margin-bottom: 0.45rem;}
        .legend-dot {width: 10px; height: 10px; border-radius: 50%; display: inline-block;}

        .issue-row {display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #F1F3F8; font-size: 0.88rem;}
        .issue-row:last-child {border-bottom: none;}
        .issue-name {color: #1F2937;}
        .issue-count {color: #6B7280; font-weight: 600;}

        div[data-testid="stDataFrame"] {border-radius: 10px; overflow: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div class='sidebar-brand'>&lt;/&gt; Jórim <span>Tech</span></div>", unsafe_allow_html=True)
    page = option_menu(
        menu_title=None,
        options=["Overview", "Tickets", "Analytics", "Team Performance", "Reports", "Settings"],
        icons=["grid-1x2", "ticket-perforated", "bar-chart-line", "people", "file-earmark-text", "gear"],
        default_index=0,
        styles={
            "container": {"padding": "0.4rem 0.6rem", "background-color": "transparent"},
            "icon": {"color": "#9FB3D9", "font-size": "15px"},
            "nav-link": {
                "color": "#C6D2EA",
                "font-size": "14px",
                "text-align": "left",
                "margin": "2px 0",
                "padding": "10px 12px",
                "border-radius": "8px",
            },
            "nav-link-selected": {"background-color": "#1D3E8F", "color": "white", "font-weight": "600"},
        },
    )

# ---------------------------------------------------------------------------
# Shared date range control (used by Overview, Analytics, Reports)
# ---------------------------------------------------------------------------
min_date, max_date = db.get_date_bounds()
min_date = dt.date.fromisoformat(min_date)
max_date = dt.date.fromisoformat(max_date)
default_start = max(min_date, max_date - dt.timedelta(days=29))


def render_page_header(title, subtitle, show_date_picker=True):
    left, right = st.columns([3, 2])
    with left:
        st.markdown(f"<div class='page-title'>{title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='page-sub'>{subtitle}</div>", unsafe_allow_html=True)
    date_range = (default_start, max_date)
    if show_date_picker:
        with right:
            date_range = st.date_input(
                "Date range",
                value=(default_start, max_date),
                min_value=min_date,
                max_value=max_date,
                label_visibility="collapsed",
            )
            if isinstance(date_range, tuple) and len(date_range) == 1:
                date_range = (date_range[0], date_range[0])
    return date_range


def kpi_card(label, value, sub_text, direction="flat"):
    st.markdown(
        f"""
        <div class="card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub {direction}">{sub_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# OVERVIEW
# ---------------------------------------------------------------------------
if page == "Overview":
    start_date, end_date = render_page_header(
        "Dashboard Overview", "Real-time sentiment and performance insights from support tickets"
    )
    period_len = (end_date - start_date).days + 1
    prev_end = start_date - dt.timedelta(days=1)
    prev_start = prev_end - dt.timedelta(days=period_len - 1)

    kpis = db.get_kpis(start_date, end_date, prev_start, prev_end)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        arrow = "↑" if kpis["total_change_pct"] >= 0 else "↓"
        kpi_card(
            "Total Tickets", f"{kpis['total']:,}",
            f"{arrow} {abs(kpis['total_change_pct'])}% vs previous period",
            "up" if kpis["total_change_pct"] >= 0 else "down",
        )
    with c2:
        kpi_card("Positive Tickets", f"{kpis['positive']:,}", f"{kpis['positive_pct']}%", "up")
    with c3:
        kpi_card("Neutral Tickets", f"{kpis['neutral']:,}", f"{kpis['neutral_pct']}%", "flat")
    with c4:
        kpi_card("Negative Tickets", f"{kpis['negative']:,}", f"{kpis['negative_pct']}%", "down")
    with c5:
        kpi_card("Urgent Negative", f"{kpis['urgent']:,}", f"{kpis['urgent_pct']}%", "down")

    st.write("")
    left, right = st.columns([1.6, 1])
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Customer Satisfaction Trend</div>", unsafe_allow_html=True)
        trend_df = db.get_satisfaction_trend(start_date, end_date)
        if trend_df.empty:
            st.info("No tickets in this date range.")
        else:
            st.plotly_chart(charts.satisfaction_trend_figure(trend_df), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Sentiment Distribution</div>", unsafe_allow_html=True)
        dist_df = db.get_sentiment_distribution(start_date, end_date)
        if dist_df.empty or dist_df["count"].sum() == 0:
            st.info("No tickets in this date range.")
        else:
            st.plotly_chart(charts.sentiment_donut_figure(dist_df), use_container_width=True, config={"displayModeBar": False})
            for sentiment in ["Positive", "Neutral", "Negative", "Urgent Negative"]:
                row = dist_df[dist_df["sentiment"] == sentiment]
                count = int(row["count"].iloc[0]) if not row.empty else 0
                total = int(dist_df["count"].sum())
                pct = round(count / total * 100, 1) if total else 0
                st.markdown(
                    f"""<div class="legend-row">
                        <span class="legend-dot" style="background:{charts.COLORS[sentiment]}"></span>
                        {sentiment} ({pct}%)
                    </div>""",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.6, 1])
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Top Issues</div>", unsafe_allow_html=True)
        issues_df = db.get_top_issues(start_date, end_date, limit=5)
        if issues_df.empty:
            st.info("No tickets in this date range.")
        else:
            for _, row in issues_df.iterrows():
                st.markdown(
                    f"""<div class="issue-row">
                        <span class="issue-name">{row['topic']}</span>
                        <span class="issue-count">{row['count']}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Negative Ticket %</div>", unsafe_allow_html=True)
        arrow = "↓" if kpis["negative_rate_change"] <= 0 else "↑"
        direction = "up" if kpis["negative_rate_change"] <= 0 else "down"
        st.markdown(f"<div class='kpi-value'>{kpis['negative_rate_pct']}%</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='kpi-sub {direction}'>{arrow} {abs(kpis['negative_rate_change'])} pts vs previous period</div>",
            unsafe_allow_html=True,
        )
        neg_trend_df = db.get_negative_trend(start_date, end_date)
        if not neg_trend_df.empty:
            st.plotly_chart(
                charts.negative_sparkline_figure(neg_trend_df), use_container_width=True,
                config={"displayModeBar": False},
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Team Performance</div>", unsafe_allow_html=True)
    team_df = db.get_team_performance(start_date, end_date)
    if team_df.empty:
        st.info("No tickets in this date range.")
    else:
        display_df = team_df.rename(
            columns={
                "assigned_to": "Team Member",
                "total_tickets": "Total Tickets",
                "resolved_tickets": "Resolved Tickets",
                "positive_pct": "Positive %",
                "negative_pct": "Negative %",
                "urgent_pct": "Urgent Negative %",
            }
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TICKETS
# ---------------------------------------------------------------------------
elif page == "Tickets":
    start_date, end_date = render_page_header("Tickets", "View, search, and filter all support tickets", show_date_picker=True)
    df = db.get_tickets_df(start_date, end_date)

    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    with f1:
        search = st.text_input("Search", placeholder="Search by customer, subject, or email…", label_visibility="collapsed")
    with f2:
        sentiment_filter = st.selectbox("Sentiment", ["All"] + sorted(df["sentiment"].unique().tolist()) if not df.empty else ["All"])
    with f3:
        topic_filter = st.selectbox("Topic", ["All"] + sorted(df["topic"].unique().tolist()) if not df.empty else ["All"])
    with f4:
        status_filter = st.selectbox("Status", ["All"] + sorted(df["status"].unique().tolist()) if not df.empty else ["All"])

    filtered = df.copy()
    if search:
        s = search.lower()
        filtered = filtered[
            filtered["customer_name"].str.lower().str.contains(s)
            | filtered["subject"].str.lower().str.contains(s)
            | filtered["customer_email"].str.lower().str.contains(s)
        ]
    if sentiment_filter != "All":
        filtered = filtered[filtered["sentiment"] == sentiment_filter]
    if topic_filter != "All":
        filtered = filtered[filtered["topic"] == topic_filter]
    if status_filter != "All":
        filtered = filtered[filtered["status"] == status_filter]

    st.markdown(f"<div class='page-sub'>{len(filtered):,} ticket(s)</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    show_cols = ["id", "customer_name", "subject", "sentiment", "confidence", "topic", "assigned_to", "status", "created_at"]
    rename = {
        "id": "ID", "customer_name": "Customer", "subject": "Subject", "sentiment": "Sentiment",
        "confidence": "Confidence", "topic": "Topic", "assigned_to": "Assigned To", "status": "Status",
        "created_at": "Created At",
    }
    st.dataframe(
        filtered[show_cols].rename(columns=rename) if not filtered.empty else filtered,
        use_container_width=True, hide_index=True, height=520,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ANALYTICS
# ---------------------------------------------------------------------------
elif page == "Analytics":
    start_date, end_date = render_page_header("Analytics", "Deeper trends across sentiment, topics, and volume")
    df = db.get_tickets_df(start_date, end_date)

    left, right = st.columns(2)
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Ticket Volume by Topic (over time)</div>", unsafe_allow_html=True)
        if df.empty:
            st.info("No tickets in this date range.")
        else:
            volume_df = df.copy()
            volume_df["day"] = volume_df["created_at"].dt.date
            grouped = volume_df.groupby(["day", "topic"]).size().reset_index(name="count")
            st.plotly_chart(charts.topic_over_time_figure(grouped), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Average Model Confidence by Sentiment</div>", unsafe_allow_html=True)
        if df.empty:
            st.info("No tickets in this date range.")
        else:
            conf = df.groupby("sentiment")["confidence"].mean().reindex(
                ["Positive", "Neutral", "Negative", "Urgent Negative"]
            ).fillna(0)
            st.bar_chart(conf, color="#2F6FED", height=320)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Resolution Status Breakdown</div>", unsafe_allow_html=True)
    if df.empty:
        st.info("No tickets in this date range.")
    else:
        status_counts = df["status"].value_counts()
        st.bar_chart(status_counts, color="#22A559", height=280)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TEAM PERFORMANCE
# ---------------------------------------------------------------------------
elif page == "Team Performance":
    start_date, end_date = render_page_header("Team Performance", "Ticket load, resolution, and sentiment outcomes by agent")
    team_df = db.get_team_performance(start_date, end_date)

    if team_df.empty:
        st.info("No tickets in this date range.")
    else:
        cols = st.columns(len(team_df))
        for col, (_, row) in zip(cols, team_df.iterrows()):
            with col:
                resolution_rate = round(row["resolved_tickets"] / row["total_tickets"] * 100) if row["total_tickets"] else 0
                st.markdown(
                    f"""
                    <div class="card">
                        <div class="kpi-label">{row['assigned_to']}</div>
                        <div class="kpi-value">{row['total_tickets']}</div>
                        <div class="kpi-sub flat">tickets · {resolution_rate}% resolved</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.write("")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Detailed Breakdown</div>", unsafe_allow_html=True)
        display_df = team_df.rename(
            columns={
                "assigned_to": "Team Member", "total_tickets": "Total Tickets", "resolved_tickets": "Resolved Tickets",
                "positive_pct": "Positive %", "negative_pct": "Negative %", "urgent_pct": "Urgent Negative %",
            }
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# REPORTS
# ---------------------------------------------------------------------------
elif page == "Reports":
    start_date, end_date = render_page_header("Reports", "Export ticket data for the selected period")
    df = db.get_tickets_df(start_date, end_date)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Export Tickets (CSV)</div>", unsafe_allow_html=True)
    st.write(f"{len(df):,} tickets between **{start_date}** and **{end_date}**.")
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        data=csv_bytes,
        file_name=f"tickets_{start_date}_{end_date}.csv",
        mime="text/csv",
    )
    st.caption("PDF export is on the roadmap — wiring it up is a backend task for the next phase.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
elif page == "Settings":
    render_page_header("Settings", "Workspace and notification preferences", show_date_picker=False)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Workspace</div>", unsafe_allow_html=True)
    st.text_input("Company name", value="Jórim Technology Solutions Pvt Ltd")
    st.selectbox("Default date range", ["Last 7 days", "Last 30 days", "Last 90 days"], index=1)
    st.toggle("Email me a daily digest of urgent-negative tickets", value=True)
    st.toggle("Auto-assign new tickets by topic", value=False)
    st.caption("This page is UI scaffolding — settings aren't persisted yet in this prototype.")
    st.markdown("</div>", unsafe_allow_html=True)
