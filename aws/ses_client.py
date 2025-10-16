import logging
logger = logging.getLogger(__name__)

# SES client wrapper
class SesClient:
    def __init__(self, session, sender):
        # Create SES client
        self.sender = sender
        self.ses = session.client("ses")
        logger.debug(f"SesClient initialized")

    # Define function to send email
    def send_email(self, recipients, subject, body):
        try:
            logger.debug(f"Sending notification to: {recipients}")
            # Build request payload
            payload = {
                "Source": self.sender,
                "Destination": {"ToAddresses": recipients},
                "Message": {
                    "Subject": {"Charset": "UTF-8", "Data": subject},
                    "Body": {
                        "Text": {"Charset": "UTF-8", "Data": body}
                    },
                },
            }
            # Send email
            res = self.ses.send_email(**payload)
            # Verify that the email is successfully sent
            messageId = res.get("MessageId")
            if messageId:
                logger.info(f"Notification sent successfully: {messageId}")
            else:
                # Log if email might not have sent
                logger.warning(f"Notification may not have been sent: {res}")
        except Exception as e:
            # Log and raise other error
            logger.error(f"Error sending email to {recipients}: {e}")
            raise