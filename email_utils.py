import smtplib
from email.mime.text import MIMEText
from config import Config

def send_email(to_email, subject, body, is_html=False):
    """Send an email using SMTP"""
    try:
        msg_type = "html" if is_html else "plain"
        msg = MIMEText(body, msg_type)
        msg["Subject"] = subject
        msg["From"] = Config.EMAIL_SENDER
        msg["To"] = to_email

        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
            server.sendmail(Config.EMAIL_SENDER, to_email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_rsvp_confirmation(to_email, application_id):
    """Send RSVP confirmation email to participant"""
    subject = "RSVP Confirmation"
    body = f"Thanks for RSVPing to event #{application_id}! We will see you there!"
    return send_email(to_email, subject, body)

def send_organizer_notification(organizer_email, username, application_id):
    """Send notification to event organizer about new RSVP"""
    subject = "RSVP Confirmation"
    body = f"""
Hello,

User **{username}** has registered for **Event #{application_id}**.

You can review their information on the website. As the organizer, you may:
- Approve or deny their registration
- Provide them with additional details through the website or by email

Please log in to the website to manage this registration.

Thank you,
The Volunteer.org Team
"""
    return send_email(organizer_email, subject, body)

def send_event_cancellation(to_email_list, application_id):
    """Send event cancellation emails to all participants"""
    subject = f"Event #{application_id} Cancelled"
    body_template = """
Hello,

Event #{application_id} has been canceled.

On behalf of the organizer we apologize for any inconvenience this may cause. 
If you have any questions, please contact the event organizer.

Thank you,
The Volunteer.org Team
SAFETY IS OUR FIRST PRIORITY!
"""
    
    success_count = 0
    try:
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
            
            for recipient in to_email_list:
                try:
                    msg = MIMEText(body_template.format(application_id=application_id), "plain")
                    msg["Subject"] = subject
                    msg["From"] = Config.EMAIL_SENDER
                    msg["To"] = recipient
                    server.sendmail(Config.EMAIL_SENDER, recipient, msg.as_string())
                    success_count += 1
                except Exception as e:
                    print(f"Failed to send email to {recipient}: {e}")
    
    except Exception as e:
        print(f"SMTP connection error: {e}")
    
    return success_count
