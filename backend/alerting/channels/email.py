"""Email notification channel."""

from typing import Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from backend.common.logging import get_logger

logger = get_logger(__name__)


class EmailChannel:
    """Email notification channel."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize email channel."""
        self.config = config or {}
        self.enabled = config.get("enabled", False) if config else False
        self.smtp_host = config.get("smtp_host", "localhost") if config else "localhost"
        self.smtp_port = config.get("smtp_port", 587) if config else 587
        self.smtp_user = config.get("smtp_user", "") if config else ""
        self.smtp_password = config.get("smtp_password", "") if config else ""
        self.from_email = config.get("from_email", "noreply@prokvant.local") if config else "noreply@prokvant.local"
        self.use_tls = config.get("use_tls", True) if config else True
    
    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send email notification.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug("Email channel disabled")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to
            msg["Subject"] = subject
            
            # Add plain text part
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, "html")
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Email sent to {to}: {subject}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending email to {to}: {e}", exc_info=True)
            return False
    
    async def send_alert(
        self,
        to: str,
        alert: Dict[str, Any]
    ) -> bool:
        """Send alert as email."""
        subject = f"[PROKVANT] {alert.get('severity', 'ALERT').upper()}: {alert.get('title', 'Alert')}"
        
        body = f"""
PROKVANT Security Alert

Title: {alert.get('title')}
Severity: {alert.get('severity')}
Source: {alert.get('source')}
Time: {alert.get('created_at')}

Message:
{alert.get('message')}
"""
        
        html_body = f"""
<html>
<body>
<h2>PROKVANT Security Alert</h2>
<p><strong>Title:</strong> {alert.get('title')}</p>
<p><strong>Severity:</strong> <span style="color: {'red' if alert.get('severity') in ['high', 'critical'] else 'orange'}">{alert.get('severity')}</span></p>
<p><strong>Source:</strong> {alert.get('source')}</p>
<p><strong>Time:</strong> {alert.get('created_at')}</p>
<hr>
<p>{alert.get('message')}</p>
</body>
</html>
"""
        
        return await self.send(to, subject, body, html_body)
