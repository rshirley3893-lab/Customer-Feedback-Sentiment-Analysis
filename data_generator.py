"""
Synthetic ticket data generator for the AI Customer Support Analytics Platform.

Generates realistic-looking support tickets (customer info, subject, description,
sentiment, topic, assigned team member, resolution status, timestamps) and writes
them into the SQLite database used by the dashboard.

This stands in for the real pipeline described in the PRD:
  Customer submits ticket -> stored in DB -> ML model predicts sentiment/topic -> dashboard reads DB
Here, steps 1-3 are simulated so the dashboard (step 4) has real data to render.
"""

import random
import sqlite3
import datetime as dt
from pathlib import Path

from faker import Faker

DB_PATH = Path(__file__).parent / "data" / "tickets.db"

fake = Faker()
Faker.seed(42)
random.seed(42)

# ---- Reference data -------------------------------------------------------

TEAM_MEMBERS = ["Ravi Kumar", "Priya Sharma", "Arun Nair", "Sneha Iyer", "Karthik Raja"]

TOPICS = [
    "Login / Authentication Issues",
    "Software Bug / Error",
    "Billing / Payment Issues",
    "Feature Request",
    "Account Access",
    "Performance / Slowness",
    "Integration Issue",
    "Data Export Problem",
]

# Relative weight per topic (roughly mirrors the PRD mockup ordering)
TOPIC_WEIGHTS = [22, 18, 14, 11, 9, 10, 9, 7]

SENTIMENTS = ["Positive", "Neutral", "Negative", "Urgent Negative"]
SENTIMENT_WEIGHTS = [51.4, 25.0, 17.1, 6.4]

STATUS_BY_SENTIMENT = {
    "Positive": ["Resolved", "Resolved", "Resolved", "Open"],
    "Neutral": ["Resolved", "Resolved", "Open", "In Progress"],
    "Negative": ["Resolved", "In Progress", "Open", "Open"],
    "Urgent Negative": ["In Progress", "Open", "Open", "Escalated"],
}

SUBJECT_TEMPLATES = {
    "Login / Authentication Issues": [
        "Can't log into my account",
        "Password reset link not working",
        "Two-factor authentication failing",
        "Session keeps expiring immediately",
    ],
    "Software Bug / Error": [
        "Getting an error when saving changes",
        "App crashes on the reports page",
        "Dashboard not loading correctly",
        "Data showing incorrect values",
    ],
    "Billing / Payment Issues": [
        "Charged twice for this month's plan",
        "Invoice missing from billing history",
        "Payment failed but card was charged",
        "Need help understanding my invoice",
    ],
    "Feature Request": [
        "Would love a dark mode option",
        "Please add CSV export for reports",
        "Request: bulk edit for tickets",
        "Suggestion for a better filter UI",
    ],
    "Account Access": [
        "Locked out of my team's workspace",
        "Need to transfer account ownership",
        "Can't add new team members",
        "Permissions not updating for my role",
    ],
    "Performance / Slowness": [
        "Dashboard is extremely slow to load",
        "Search takes forever to return results",
        "App freezes when uploading files",
        "Noticeable lag across the whole platform",
    ],
    "Integration Issue": [
        "Slack integration stopped sending alerts",
        "Zapier webhook not firing",
        "API returning 500 errors intermittently",
        "SSO integration broke after update",
    ],
    "Data Export Problem": [
        "Exported report is missing columns",
        "PDF export fails every time",
        "CSV export has encoding issues",
        "Can't export more than 100 rows",
    ],
}

DESCRIPTION_SNIPPETS = {
    "Positive": [
        "Just wanted to flag this, but overall the platform has been working really well for our team.",
        "Not a big deal, support has been great so far and we appreciate the quick turnaround.",
        "Small thing to fix, but otherwise really happy with how smooth everything has been.",
    ],
    "Neutral": [
        "Wanted to check on the status of this and understand what steps are next.",
        "Following up on this issue, could you let me know the expected timeline?",
        "Not urgent, just documenting this so it's on your radar for the next release.",
    ],
    "Negative": [
        "This has been frustrating to deal with and it's affecting our daily workflow.",
        "I've tried the usual troubleshooting steps and nothing seems to resolve it.",
        "This is the second time this has happened this month and it's disruptive.",
    ],
    "Urgent Negative": [
        "This is blocking our entire team from working, we need this fixed immediately.",
        "Production is down because of this and customers are already complaining.",
        "We are losing revenue every hour this remains unresolved, please escalate.",
    ],
}


def _weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def _random_datetime_within(days_back: int) -> dt.datetime:
    now = dt.datetime.now()
    start = now - dt.timedelta(days=days_back)
    delta = now - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + dt.timedelta(seconds=random_seconds)


def _confidence_for(sentiment: str) -> float:
    # Urgent/negative tends to be easier for the model to be confident about
    base = {"Positive": 0.80, "Neutral": 0.68, "Negative": 0.82, "Urgent Negative": 0.88}[sentiment]
    return round(min(0.99, max(0.55, random.gauss(base, 0.07))), 2)


def generate_tickets(n: int = 1248, days_back: int = 60) -> list[dict]:
    tickets = []
    for i in range(1, n + 1):
        sentiment = _weighted_choice(SENTIMENTS, SENTIMENT_WEIGHTS)
        topic = _weighted_choice(TOPICS, TOPIC_WEIGHTS)
        subject = random.choice(SUBJECT_TEMPLATES[topic])
        description = f"{subject}. {random.choice(DESCRIPTION_SNIPPETS[sentiment])}"
        created_at = _random_datetime_within(days_back)
        status = random.choice(STATUS_BY_SENTIMENT[sentiment])
        resolved_at = None
        if status == "Resolved":
            resolved_at = created_at + dt.timedelta(hours=random.randint(1, 96))

        tickets.append(
            {
                "id": i,
                "customer_name": fake.name(),
                "customer_email": fake.email(),
                "subject": subject,
                "description": description,
                "sentiment": sentiment,
                "confidence": _confidence_for(sentiment),
                "topic": topic,
                "assigned_to": random.choice(TEAM_MEMBERS),
                "status": status,
                "created_at": created_at.isoformat(timespec="seconds"),
                "resolved_at": resolved_at.isoformat(timespec="seconds") if resolved_at else None,
            }
        )
    return tickets


def build_database(force: bool = False) -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists() and not force:
        return DB_PATH

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            confidence REAL NOT NULL,
            topic TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            resolved_at TEXT
        )
        """
    )

    tickets = generate_tickets()
    cur.executemany(
        """
        INSERT INTO tickets
            (id, customer_name, customer_email, subject, description, sentiment,
             confidence, topic, assigned_to, status, created_at, resolved_at)
        VALUES (:id, :customer_name, :customer_email, :subject, :description,
                :sentiment, :confidence, :topic, :assigned_to, :status,
                :created_at, :resolved_at)
        """,
        tickets,
    )
    conn.commit()
    conn.close()
    return DB_PATH


if __name__ == "__main__":
    path = build_database(force=True)
    print(f"Database built at {path}")
