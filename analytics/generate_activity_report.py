
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import text
from datetime import datetime, timedelta
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# --- Setup Paths and Environment ---
# Based on the pattern in create_workout_main.py, we modify the Python path
# and load the .env file from the 'backend' directory.

# 1. Set up path to allow imports from the 'app' module
BACKEND_DIR = Path(__file__).resolve().parent.parent  # Resolves to the 'backend' directory
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

# 2. Load environment variables
# create_workout_main.py uses '.env.development'. Since this script uses the
# production DB, we will look for a '.env' file.
dotenv_path = BACKEND_DIR / ".env.production"
if dotenv_path.exists():
    print(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"Warning: '.env' file not found at '{dotenv_path}'. The script will likely fail if environment variables are not set.")

# 3. Now that the path is set, we can import from 'app'
from app.llm.utils.db_utils import create_db_session

# --- Configuration ---
LAST_N_DAYS_USER_ACTIVITY = 30
LAST_N_DAYS_HOURLY_ACTIVITY = 7
OUTPUT_HTML_FILE = "backend/analytics/activity_report.html"

async def fetch_data(query: str) -> pd.DataFrame:
    """
    Fetches data from the production database using a given SQL query.
    """
    print(f"Executing query:\n{query}\n")
    async for session in create_db_session(use_production=True):
        try:
            result = await session.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        finally:
            # The context manager in create_db_session handles closing
            pass

async def generate_daily_activity_per_user(days: int) -> go.Figure:
    """
    Generates a bar chart of daily activities per user hash for the last N days.
    """
    print("Generating daily activity per user chart...")
    query = f"""
    SELECT
        DATE(timestamp) as activity_date,
        user_id_hash,
        COUNT(*) as action_count
    FROM
        user_activity_logs
    WHERE
        timestamp >= NOW() - INTERVAL '{days} days'
        AND user_id_hash != 'anonymous'
    GROUP BY
        activity_date,
        user_id_hash
    ORDER BY
        activity_date,
        action_count DESC;
    """
    df = await fetch_data(query)

    if df.empty:
        print("No data found for daily activity.")
        return go.Figure().update_layout(title_text=f"Keine Benutzeraktivität in den letzten {days} Tagen gefunden")

    fig = px.bar(
        df,
        x="activity_date",
        y="action_count",
        color="user_id_hash",
        title=f"Tägliche Aktionen pro Benutzer (letzte {days} Tage)",
        labels={"activity_date": "Datum", "action_count": "Anzahl Aktionen", "user_id_hash": "Benutzer (Hash)"},
        text="action_count"
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_title="Datum",
        yaxis_title="Anzahl der Aktionen",
        legend_title="Benutzer (anonymisierter Hash)",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    print("Daily activity chart generated.")
    return fig

async def generate_hourly_activity_total(days: int) -> go.Figure:
    """
    Generates a line chart of total hourly activities for the last N days.
    """
    print("Generating hourly activity chart...")
    query = f"""
    SELECT
        DATE_TRUNC('hour', timestamp) as hour,
        COUNT(*) as action_count
    FROM
        user_activity_logs
    WHERE
        timestamp >= NOW() - INTERVAL '{days} days'
    GROUP BY
        hour
    ORDER BY
        hour;
    """
    df = await fetch_data(query)

    if df.empty:
        print("No data found for hourly activity.")
        return go.Figure().update_layout(title_text=f"Keine stündliche Aktivität in den letzten {days} Tagen gefunden")

    fig = px.line(
        df,
        x="hour",
        y="action_count",
        title=f"Gesamte stündliche Aktivität (letzte {days} Tage)",
        labels={"hour": "Stunde", "action_count": "Anzahl Aktionen"},
        markers=True
    )
    fig.update_layout(
        xaxis_title="Datum und Stunde",
        yaxis_title="Anzahl der Aktionen",
    )
    print("Hourly activity chart generated.")
    return fig

async def generate_llm_activity_table(days: int) -> go.Figure:
    """
    Generates a table of recent LLM activities (workout creation/revision)
    with user emails.
    """
    print("Generating LLM activity table...")
    query = f"""
    SELECT
        l.timestamp as "Zeitstempel",
        u.email as "Benutzer-E-Mail",
        l.llm_operation_type as "Aktion"
    FROM
        llm_call_logs AS l
    JOIN
        auth.users AS u ON l.user_id::uuid = u.id
    WHERE
        l.llm_operation_type IN ('workout_creation', 'workout_revision')
        AND l.timestamp >= NOW() - INTERVAL '{days} days'
    ORDER BY
        l.timestamp DESC;
    """
    df = await fetch_data(query)

    if df.empty:
        print("No data found for LLM activity.")
        return go.Figure().update_layout(title_text=f"Keine LLM-Aktivitäten in den letzten {days} Tagen gefunden")

    # Format timestamp for better readability
    df['Zeitstempel'] = pd.to_datetime(df['Zeitstempel']).dt.strftime('%Y-%m-%d %H:%M:%S')

    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[df[col] for col in df.columns],
                   fill_color='lavender',
                   align='left'))
    ])
    fig.update_layout(
        title_text=f"LLM-Aktivitäten (Workout Erstellung/Überarbeitung) der letzten {days} Tage"
    )
    print("LLM activity table generated.")
    return fig

async def generate_llm_activity_chart(days: int) -> go.Figure:
    """
    Generates a bar chart of daily LLM activities per user.
    """
    print("Generating LLM activity chart...")
    query = f"""
    SELECT
        DATE(l.timestamp) as activity_date,
        u.email as user_email,
        l.llm_operation_type as action_type,
        COUNT(*) as action_count
    FROM
        llm_call_logs AS l
    JOIN
        auth.users AS u ON l.user_id::uuid = u.id
    WHERE
        l.llm_operation_type IN ('workout_creation', 'workout_revision')
        AND l.timestamp >= NOW() - INTERVAL '{days} days'
    GROUP BY
        activity_date,
        user_email,
        action_type
    ORDER BY
        activity_date,
        user_email;
    """
    df = await fetch_data(query)

    if df.empty:
        print("No data found for LLM activity chart.")
        return go.Figure().update_layout(title_text=f"Keine LLM-Aktivitäten für Diagramm in den letzten {days} Tagen gefunden")

    df['activity_date'] = pd.to_datetime(df['activity_date']).dt.strftime('%Y-%m-%d')

    fig = px.bar(
        df,
        x="activity_date",
        y="action_count",
        color="user_email",
        barmode="stack",
        text="action_count",
        hover_data=["action_type"],
        title=f"Tägliche LLM-Aktionen pro Benutzer (letzte {days} Tage)",
        labels={"activity_date": "Datum", "action_count": "Anzahl Aktionen", "user_email": "Benutzer-E-Mail"}
    )
    fig.update_traces(textposition='inside')
    fig.update_layout(
        xaxis_title="Datum",
        yaxis_title="Anzahl der Aktionen",
        legend_title="Benutzer",
    )
    print("LLM activity chart generated.")
    return fig


async def main():
    """
    Main function to generate and save the analytics report.
    """
    print("Starting analytics report generation...")

    # Generate figures
    fig1 = await generate_daily_activity_per_user(LAST_N_DAYS_USER_ACTIVITY)
    fig2 = await generate_hourly_activity_total(LAST_N_DAYS_HOURLY_ACTIVITY)
    llm_table_fig = await generate_llm_activity_table(LAST_N_DAYS_USER_ACTIVITY)
    llm_chart_fig = await generate_llm_activity_chart(LAST_N_DAYS_USER_ACTIVITY)

    # Create a subplot figure
    # This part is complex because plotly subplots from figures directly is not straightforward.
    # We will save them to a single HTML file instead.
    print(f"Writing report to {OUTPUT_HTML_FILE}...")
    with open(OUTPUT_HTML_FILE, 'w') as f:
        f.write("<html><head><title>User Activity Report</title></head><body>")
        f.write(f"<h1>User Activity Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>")

        f.write("<h2>Hinweis zur Anonymisierung</h2>")
        f.write("""
        <p>
            Die Benutzerkennung ('user_id_hash') ist ein <b>wöchentlich rotierender, anonymisierter Hash</b>.
            Dies bedeutet:
            <ul>
                <li>Ein direkter Rückschluss auf die E-Mail-Adresse eines Benutzers ist <b>absichtlich nicht möglich</b>, um die Privatsphäre zu schützen.</li>
                <li>Ein Benutzer wird jede Woche unter einer neuen Kennung geführt. Dies verhindert permanentes Tracking über lange Zeiträume.</li>
            </ul>
            Diese Analyse zeigt also das Verhalten von anonymisierten Nutzern innerhalb einer Woche.
        </p>
        """)

        f.write(f"<h2>Tägliche Aktionen pro Benutzer (Letzte {LAST_N_DAYS_USER_ACTIVITY} Tage)</h2>")
        f.write(fig1.to_html(full_html=False, include_plotlyjs='cdn'))
        
        f.write(f"<h2>Gesamte stündliche Aktivität (Letzte {LAST_N_DAYS_HOURLY_ACTIVITY} Tage)</h2>")
        f.write(fig2.to_html(full_html=False, include_plotlyjs='cdn'))

        f.write(f"<h2>LLM-Aktivitäten (Letzte {LAST_N_DAYS_USER_ACTIVITY} Tage)</h2>")
        f.write(llm_chart_fig.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(llm_table_fig.to_html(full_html=False, include_plotlyjs='cdn'))
        
        f.write("</body></html>")

    print("Analytics report generated successfully!")
    print(f"File saved at: {os.path.abspath(OUTPUT_HTML_FILE)}")
    
    print("\\n--- How to run ---")
    print("1. Make sure you are in the 'mysports' root directory.")
    print("2. Install required packages: pip install pandas plotly sqlalchemy asyncpg python-dotenv")
    print("3. Run the script: python backend/analytics/generate_activity_report.py")


if __name__ == "__main__":
    # To allow running this script directly
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main()) 