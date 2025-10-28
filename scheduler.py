# scheduler.py
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import resend
import storage

# ========== Configuration ==========
# Load API key from .env file
from dotenv import load_dotenv
load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

if not RESEND_API_KEY:
    print("WARNING: RESEND_API_KEY not found in .env file!")
    print("Please create a .env file with: RESEND_API_KEY=your_key_here")

resend.api_key = RESEND_API_KEY

# Global state
_email_recipients = []
_scheduler_thread = None
_scheduler_running = False
_scheduler_info = {}


# ========== Email Recipients Management ==========
def get_email_recipients() -> list:
    """Get the list of configured email recipients."""
    return _email_recipients.copy()


def set_email_recipients(emails: list) -> None:
    """Set the list of email recipients."""
    global _email_recipients
    _email_recipients = [e.strip() for e in emails if e.strip()]


# ========== Scheduler Control ==========
def start_scheduler(start_date, start_time: str, frequency: str) -> None:
    """
    Start the scheduler with given parameters.
    
    Args:
        start_date: datetime.date object from DateEntry
        start_time: String in format "HH:MM" (24-hour)
        frequency: One of the frequency options
    """
    global _scheduler_thread, _scheduler_running, _scheduler_info
    
    if _scheduler_running:
        stop_scheduler()
    
    _scheduler_info = {
        "start_date": start_date,
        "start_time": start_time,
        "frequency": frequency,
        "next_run": None
    }
    
    _scheduler_running = True
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()


def stop_scheduler() -> None:
    """Stop the scheduler."""
    global _scheduler_running
    _scheduler_running = False


def is_scheduler_running() -> bool:
    """Check if scheduler is currently running."""
    return _scheduler_running


def get_scheduler_info() -> dict:
    """Get current scheduler configuration and status."""
    return _scheduler_info.copy()


# ========== Email Sending ==========
def send_test_email(recipients: list) -> None:
    """Send a test email to verify configuration."""
    if not recipients:
        raise ValueError("No recipients specified")
    
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #2563eb;">FilePulse Test Email</h2>
        <p>This is a test email from FilePulse.</p>
        <p>If you received this, your email configuration is working correctly!</p>
        <hr style="margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">Sent at: {}</p>
    </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    for recipient in recipients:
        try:
            resend.Emails.send({
                "from": "onboarding@resend.dev",
                "to": recipient,
                "subject": "FilePulse - Test Email",
                "html": html_content
            })
        except Exception as e:
            raise Exception(f"Failed to send to {recipient}: {e}")


def send_report_email(recipients: list, report_path: str, report_title: str) -> None:
    """Send the latest report via email."""
    if not recipients:
        raise ValueError("No recipients specified")
    
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Report not found: {report_path}")
    
    # Read PDF as base64 for attachment
    import base64
    with open(report_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode()
    
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #2563eb;">FilePulse - Scheduled Report</h2>
        <p>Please find attached the latest FilePulse report.</p>
        <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Report:</strong> {}</p>
            <p style="margin: 5px 0;"><strong>Generated:</strong> {}</p>
        </div>
        <p>This report contains folder activity analysis based on your configured thresholds.</p>
        <hr style="margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">Automated email from FilePulse</p>
    </body>
    </html>
    """.format(report_title, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    filename = os.path.basename(report_path)
    
    for recipient in recipients:
        try:
            resend.Emails.send({
                "from": "onboarding@resend.dev",
                "to": recipient,
                "subject": f"FilePulse Report - {report_title}",
                "html": html_content,
                "attachments": [{
                    "filename": filename,
                    "content": pdf_data
                }]
            })
        except Exception as e:
            print(f"Failed to send email to {recipient}: {e}")


# ========== Scheduler Loop ==========
def _scheduler_loop() -> None:
    """Background thread that runs the scheduler."""
    global _scheduler_info
    
    # Calculate first run time
    start_date = _scheduler_info["start_date"]
    start_time = _scheduler_info["start_time"]
    frequency = _scheduler_info["frequency"]
    
    # Parse start time
    hour, minute = map(int, start_time.split(":"))
    
    # Combine date and time
    next_run = datetime.combine(start_date, datetime.min.time())
    next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If the start time is in the past, calculate next run based on frequency
    now = datetime.now()
    if next_run < now:
        next_run = _calculate_next_run(now, frequency, hour, minute)
    
    _scheduler_info["next_run"] = next_run.strftime("%Y-%m-%d %H:%M:%S")
    
    while _scheduler_running:
        now = datetime.now()
        
        if now >= next_run:
            # Time to send email
            try:
                _send_scheduled_email()
            except Exception as e:
                print(f"Scheduled email failed: {e}")
            
            # Calculate next run
            next_run = _calculate_next_run(now, frequency, hour, minute)
            _scheduler_info["next_run"] = next_run.strftime("%Y-%m-%d %H:%M:%S")
        
        # Sleep for 30 seconds before checking again
        time.sleep(30)


def _calculate_next_run(current_time: datetime, frequency: str, hour: int, minute: int) -> datetime:
    """Calculate the next run time based on frequency."""
    next_run = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    if frequency == "Hourly":
        next_run = current_time + timedelta(hours=1)
        next_run = next_run.replace(minute=minute, second=0, microsecond=0)
    elif frequency == "Daily":
        next_run = current_time + timedelta(days=1)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif frequency == "Every 2 days":
        next_run = current_time + timedelta(days=2)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif frequency == "Every 3 days":
        next_run = current_time + timedelta(days=3)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif frequency == "Weekly":
        next_run = current_time + timedelta(weeks=1)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif frequency == "Fortnightly":
        next_run = current_time + timedelta(weeks=2)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif frequency == "Monthly":
        # Add one month
        if current_time.month == 12:
            next_run = current_time.replace(year=current_time.year + 1, month=1, hour=hour, minute=minute, second=0, microsecond=0)
        else:
            next_run = current_time.replace(month=current_time.month + 1, hour=hour, minute=minute, second=0, microsecond=0)
    elif frequency == "Every 6 months":
        # Add 6 months
        new_month = current_time.month + 6
        new_year = current_time.year
        if new_month > 12:
            new_month -= 12
            new_year += 1
        next_run = current_time.replace(year=new_year, month=new_month, hour=hour, minute=minute, second=0, microsecond=0)
    elif frequency == "Yearly":
        next_run = current_time.replace(year=current_time.year + 1, hour=hour, minute=minute, second=0, microsecond=0)
    
    return next_run


def _send_scheduled_email() -> None:
    """Send email with the latest report."""
    if not _email_recipients:
        print("No email recipients configured")
        return
    
    # Get latest report from storage
    reports = storage.list_reports()
    if not reports:
        print("No reports available to send")
        return
    
    latest_report = reports[0]  # Already sorted newest-first
    report_path = latest_report.get("path")
    report_title = latest_report.get("title", "Report")
    
    if not report_path or not os.path.exists(report_path):
        print(f"Report file not found: {report_path}")
        return
    
    send_report_email(_email_recipients, report_path, report_title)
    print(f"Scheduled email sent to {len(_email_recipients)} recipient(s)")