import logging

logger = logging.getLogger(__name__)

def send_onboarding_email(email: str, name: str):
    '''
    Sends a welcome sequence to activate new signups.
    Uses tools like Resend or SendGrid in production.
    '''
    logger.info(f"Sending Onboarding Email to {email}")
    # mock_resend.emails.send(...)

def send_alert_email(email: str, alert_type: str, details: str):
    '''
    Transactional email for anomalies or stock-outs.
    '''
    logger.info(f"Alert [{alert_type}] sent to {email}")
