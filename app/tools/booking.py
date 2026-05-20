import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.booking import BookingRepository

def send_booking_email(to_email: str, subject: str, body: str) -> bool:
    """Dispatches a confirmation email using smtplib, falling back to mock logs if credentials are absent."""
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        # High quality console log acting as mock SMTP fallback
        print("\n" + "="*50)
        print("[MOCK SMTP EMAIL CONFIRMATION TRIGGERED]")
        print(f"To:      {to_email}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("="*50 + "\n")
        return True

    try:
        # Standard email construction
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_SENDER or settings.SMTP_USERNAME
        msg["To"] = to_email
        msg["Subject"] = subject
        
        msg.attach(MIMEText(body, "plain"))
        
        # Establish SMTP connection with standard security enhancements
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()  # Upgrade to TLS connection
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"[SMTP] Dispatched confirmation email successfully to {to_email}")
        return True
    except Exception as e:
        # Log error to stderr but prevent transaction crash to maintain resilience
        print(f"[SMTP EXCEPTION] Failed to dispatch real email: {str(e)}")
        return False

@tool
def book_interview(full_name: str, email: str, date: str, time: str) -> str:
    """Registers and schedules a new interview or meeting in our database and sends a confirmation email.
    
    Use this tool whenever the user explicitly requests to book, schedule, or set up a meeting/interview.
    
    Args:
        full_name: The full name of the interviewee.
        email: Contact email address.
        date: Target date for scheduling (e.g. "2026-06-10").
        time: Target time slot (e.g. "11:00 AM").
        
    Returns:
        A status string detailing the schedule outcomes.
    """
    try:
        # 1. Commit booking entry to Postgres via Repository
        db: Session = SessionLocal()
        try:
            repo = BookingRepository(db)
            booking = repo.create_booking(
                full_name=full_name,
                email=email,
                date=date,
                time=time
            )
        finally:
            db.close()

        # 2. Build template email body
        subject = f"Interview Scheduled: {full_name} - PalmMind AI"
        body = (
            f"Hello {full_name},\n\n"
            f"Your interview booking at PalmMind AI is officially confirmed!\n\n"
            f"Details of your slot:\n"
            f"  Date: {date}\n"
            f"  Time: {time}\n"
            f"  Reference ID: {booking.id}\n\n"
            f"Please prepare your environment with local docker capabilities.\n"
            f"We look forward to our discussion!\n\n"
            f"Warm Regards,\n"
            f"PalmMind Engineering"
        )

        # 3. Dispatched confirmation
        sent = send_booking_email(email, subject, body)

        status = f"Successfully scheduled interview for {full_name} on {date} at {time}."
        if not sent:
            status += " (Warning: Confirmation email could not be sent, check logs for details)."
        return status
        
    except Exception as e:
        return f"Error executing booking registrations: {str(e)}"
