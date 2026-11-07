"""
Database access layer for the AI Customer Support Analytics Platform.

All dashboard pages read through the functions in this module rather than
writing raw SQL inline, so the query logic (date filtering, aggregation) is
defined once and stays consistent across pages.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

import pandas as pd

from data_generator import build_database

DB_PATH = Path(__file__).parent / "data" / "tickets.db"


@contextmanager
def get_connection():
    build_database(force=False)  # ensure DB exists
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def _date_filter_sql(start_date, end_date) -> str:
    return f"WHERE date(created_at) BETWEEN '{start_date}' AND '{end_date}'"


def get_date_bounds() -> tuple[str, str]:
    with get_connection() as conn:
        row = conn.execute("SELECT MIN(date(created_at)), MAX(date(created_at)) FROM tickets").fetchone()
    return row[0], row[1]


def get_tickets_df(start_date, end_date) -> pd.DataFrame:
    query = f"SELECT * FROM tickets {_date_filter_sql(start_date, end_date)} ORDER BY created_at DESC"
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, parse_dates=["created_at", "resolved_at"])
    return df


def get_kpis(start_date, end_date, prev_start_date, prev_end_date) -> dict:
    df = get_tickets_df(start_date, end_date)
    prev_df = get_tickets_df(prev_start_date, prev_end_date)

    total = len(df)
    prev_total = len(prev_df)
    total_change = ((total - prev_total) / prev_total * 100) if prev_total else 0.0

    counts = df["sentiment"].value_counts()
    pct = (counts / total * 100) if total else counts

    def safe(sentiment):
        return int(counts.get(sentiment, 0)), float(round(pct.get(sentiment, 0.0), 1))

    positive_n, positive_pct = safe("Positive")
    neutral_n, neutral_pct = safe("Neutral")
    negative_n, negative_pct = safe("Negative")
    urgent_n, urgent_pct = safe("Urgent Negative")

    neg_rate = (negative_n + urgent_n) / total * 100 if total else 0.0
    prev_counts = prev_df["sentiment"].value_counts()
    prev_total_neg = int(prev_counts.get("Negative", 0)) + int(prev_counts.get("Urgent Negative", 0))
    prev_neg_rate = (prev_total_neg / prev_total * 100) if prev_total else 0.0
    neg_rate_change = neg_rate - prev_neg_rate

    return {
        "total": total,
        "total_change_pct": round(total_change, 1),
        "positive": positive_n,
        "positive_pct": positive_pct,
        "neutral": neutral_n,
        "neutral_pct": neutral_pct,
        "negative": negative_n,
        "negative_pct": negative_pct,
        "urgent": urgent_n,
        "urgent_pct": urgent_pct,
        "negative_rate_pct": round(neg_rate, 1),
        "negative_rate_change": round(neg_rate_change, 1),
    }


def get_satisfaction_trend(start_date, end_date) -> pd.DataFrame:
    """
    Weekly 'satisfaction score' = share of (Positive + Neutral) tickets vs total,
    used as a stand-in for a CSAT-style trend line.
    """
    df = get_tickets_df(start_date, end_date)
    if df.empty:
        return pd.DataFrame(columns=["week", "satisfaction"])

    df["week"] = df["created_at"].dt.to_period("W").apply(lambda p: p.start_time.date())
    grouped = df.groupby("week")["sentiment"].apply(
        lambda s: round((s.isin(["Positive", "Neutral"]).sum() / len(s)) * 100, 1)
    )
    return grouped.reset_index(name="satisfaction")


def get_negative_trend(start_date, end_date) -> pd.DataFrame:
    df = get_tickets_df(start_date, end_date)
    if df.empty:
        return pd.DataFrame(columns=["day", "negative_pct"])

    df["day"] = df["created_at"].dt.date
    grouped = df.groupby("day")["sentiment"].apply(
        lambda s: round((s.isin(["Negative", "Urgent Negative"]).sum() / len(s)) * 100, 1)
    )
    return grouped.reset_index(name="negative_pct")


def get_sentiment_distribution(start_date, end_date) -> pd.DataFrame:
    df = get_tickets_df(start_date, end_date)
    counts = df["sentiment"].value_counts().reindex(
        ["Positive", "Neutral", "Negative", "Urgent Negative"], fill_value=0
    )
    return counts.rename_axis("sentiment").reset_index(name="count")


def get_top_issues(start_date, end_date, limit: int = 5) -> pd.DataFrame:
    df = get_tickets_df(start_date, end_date)
    counts = df["topic"].value_counts().head(limit)
    return counts.reset_index()


def get_team_performance(start_date, end_date) -> pd.DataFrame:
    df = get_tickets_df(start_date, end_date)
    if df.empty:
        return pd.DataFrame(
            columns=["assigned_to", "total_tickets", "resolved_tickets", "positive_pct", "negative_pct", "urgent_pct"]
        )

    rows = []
    for member, group in df.groupby("assigned_to"):
        total = len(group)
        resolved = int((group["status"] == "Resolved").sum())
        pos_pct = round((group["sentiment"] == "Positive").sum() / total * 100)
        neg_pct = round((group["sentiment"] == "Negative").sum() / total * 100)
        urgent_pct = round((group["sentiment"] == "Urgent Negative").sum() / total * 100)
        rows.append(
            {
                "assigned_to": member,
                "total_tickets": total,
                "resolved_tickets": resolved,
                "positive_pct": pos_pct,
                "negative_pct": neg_pct,
                "urgent_pct": urgent_pct,
            }
        )
    result = pd.DataFrame(rows).sort_values("total_tickets", ascending=False).reset_index(drop=True)
    return result
