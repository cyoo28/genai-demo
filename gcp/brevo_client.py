import logging
import brevo_python
from brevo_python.rest import ApiException

logger = logging.getLogger(__name__)

# Brevo client wrapper
class BrevoClient:
    def __init__(self, apiKey, sender):
        self.sender = sender
        # Configure API key authorization
        configuration = brevo_python.Configuration()
        configuration.api_key['api-key'] = apiKey
        # Create Brevo client
        self.apiClient = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(configuration))
        logger.debug(f"BrevoClient initialized")
    
    # Define function to send email
    def send_email(self, recipients, subject, body):
        try:
            logger.debug(f"Sending notification to: {recipients}")
            # Build request payload            
            payload = brevo_python.SendSmtpEmail(to=[{"email": r} for r in recipients],
                                                 text_content=body,
                                                 sender={"email": self.sender},
                                                 subject=subject)
            # Send email
            res = self.apiClient.send_transac_email(payload)
            # Verify that the email is successfully sent
            messageId = getattr(res, "message_id", "unknown")
            logger.info(f"Notification sent successfully: {messageId}")
            return messageId
        except ApiException as e:
            # Log and raise other error
            logger.error(f"Error sending email to {recipients}: {e}", exc_info=True)
            raise