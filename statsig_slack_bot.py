from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import schedule
import time
import threading

# Initialize Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Statsig API configuration
STATSIG_API_KEY = "console-CLzsS36tIwaj9pxj7dw44ArHQ8LCBBWm197KHh52FSk"
STATSIG_API_BASE_URL = "https://statsigapi.net/console/v1/metrics"

# Daily metrics to track
DAILY_METRICS = [
    "sheet_created", "row_added", "column_added",
    "sign_up", "sign_in", "logout", "sheet_deleted",
    "column_renamed", "column_update_type", "sheet_exported",
    "template_opened", "sheet_renamed", "sheet_duplicated"
]

# Weekly metrics to track
WEEKLY_METRICS = ["sheet_created", "sign_up"]

def get_statsig_metric(metric_id, date):
    """Fetch a single metric count from Statsig API for a specific date"""
    headers = {
        "STATSIG-API-KEY": STATSIG_API_KEY
    }
    params = {
        "id": f"{metric_id}::event_count",
        "date": date
    }

    response = requests.get(STATSIG_API_BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json().get("data", [])
        if data:
            return data[0].get("value", 0)
        else:
            print(f"No data for {metric_id} on {date}")
    else:
        print(f"Error fetching {metric_id} for {date}: {response.status_code}")
    return 0

def get_weekly_metrics():
    """Fetch and aggregate metrics for the past 7 days"""
    today = datetime.now()
    weekly_metrics = {}
    
    for metric in WEEKLY_METRICS:
        total = 0
        for i in range(7):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            value = get_statsig_metric(metric, date)
            total += value
        weekly_metrics[metric] = total
    
    return weekly_metrics

def format_metrics_message(daily_metrics, date):
    """Format the metrics into a Slack message"""
    # Convert date string to datetime object
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%B %d")  # e.g., "June 13"
    
    message = "*📊 Daily Metrics Report*\n\n"
    message += f"*Date: {formatted_date}*\n\n"
    message += "*Daily Metrics:*\n"
    
    # Create table header
    message += "```\nMetric                | Count\n"
    message += "---------------------|-------\n"
    
    # Add each metric as a table row
    for metric, value in daily_metrics.items():
        # Format metric name: capitalize and replace underscores with spaces
        metric_name = metric.replace('_', ' ').title()
        # Pad the metric name to align the table
        message += f"{metric_name:<20} | {value:>5}\n"
    
    message += "```"
    return message

def format_weekly_metrics_message(weekly_metrics):
    """Format the weekly metrics into a Slack message"""
    today = datetime.now()
    end_date = (today - timedelta(days=1)).strftime("%B %d")  # yesterday
    start_date = (today - timedelta(days=7)).strftime("%B %d")  # 7 days ago
    
    message = "*📈 Weekly Metrics Report*\n\n"
    message += f"*Period: {start_date} - {end_date}*\n\n"
    message += "*Weekly Summary:*\n"
    
    # Create table
    message += "```\nMetric          | Count\n"
    message += "---------------|-------\n"
    message += f"Sheets Created | {weekly_metrics['sheet_created']:>5}\n"
    message += f"New Users      | {weekly_metrics['sign_up']:>5}\n"
    message += "```"
    return message

def send_daily_report():
    """Send the daily metrics report"""
    today = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Fetch daily metrics
    daily_metrics = {}
    for metric in DAILY_METRICS:
        value = get_statsig_metric(metric, today)
        daily_metrics[metric] = value

    # Format and send the message
    message = format_metrics_message(daily_metrics, today)
    app.client.chat_postMessage(
        channel="dailystats",
        text=message
    )

def send_weekly_report():
    """Send the weekly metrics report"""
    weekly_metrics = get_weekly_metrics()
    message = format_weekly_metrics_message(weekly_metrics)
    app.client.chat_postMessage(
        channel="dailystats",
        text=message
    )

def run_schedule():
    """Run the scheduler in a separate thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.command("/usage-report")
def handle_usage_report(ack, body, client):
    """Handle the /usage-report Slack command"""
    ack()
    
    # Get the text parameter from the command
    text = body.get('text', '').strip().lower()
    
    if text == 'weekly':
        send_weekly_report()
    else:
        send_daily_report()

if __name__ == "__main__":
    # Schedule the daily report at whatever time you want
    schedule.every().day.at("12:45").do(send_daily_report)
    
    # Schedule the weekly report for Fridays at 9:25 AM
    schedule.every().friday.at("12:45").do(send_weekly_report)
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Start the Slack bot
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()
