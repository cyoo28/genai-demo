import logging
from datetime import datetime, timezone
import parsedatetime

logger = logging.getLogger(__name__)

# Initialize the parsedatetime calendar
cal = parsedatetime.Calendar()

# Function to get the time an event occurred
def get_eventtime(text):
    # Attempt to extract date/time from text
    timeStruct, status = cal.parse(text)
    if status == 1:
        # If successfuly, extract: year, month, day, hour, minute, second
        dt = datetime(*timeStruct[:6])
        # Make datetime UTC aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        # Return extracted time
        return dt.strftime("%Y-%m-%d")
    else:
        return None

# Bedrock AI client wrapper
class BedrockClient:
    def __init__(self, session, s3Client):
        # Set up S3 client
        self.s3 = s3Client
        # Model settings
        self.model = "amazon.nova-micro-v1:0"
        self.system_instructions = """
        You are a general-purpose AI assistant for demonstration purposes.
        - Respond helpfully and accurately to user input.
        - Explain your reasoning clearly when asked.
        - Keep responses concise unless detail is requested.
        - Ask clarifying questions if a request is unclear.
        - Avoid sensitive, private, or inappropriate content.
        """
        # Generation Parameters
        self.temperature = 0.2
        self.top_p = 0.8
        self.max_output_tokens = 400
        # Set up Bedrock AI client
        self.client = session.client("bedrock-runtime")
    # Define function to send messages to chatbot
    def send_message(self, username, msg):
        logger.info(f"send_message: received message from '{username}'")
        # Handle test messages (do not store in history)
        isTest = False
        if msg.startswith("test:"):
            logger.info(f"Test message detected for '{username}' - not adding to history")
            msg = msg[len("test:"):].strip()
            isTest = True
        # Initialize chat history
        history = []
        # Keys for storing history in S3
        key = f"chat-history/{username}.json"
        # Load existing history if they exist in S3
        if self.s3.obj_check(key):
            history, _ = self.s3.obj_read(key)
            logger.debug(f"Loaded history for user '{username}'")
        if isTest:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            prompt = history.copy()
            prompt.append({"role":"user", "content":[{"text":f"[Query-{timestamp}] {msg}"}]})
            response = self.client.converse(
                modelId=self.model,
                messages=prompt,
                system=[{'text': self.system_instructions}],
                inferenceConfig={"maxTokens": self.max_output_tokens, "temperature": self.temperature, "topP": self.top_p}
            )
            responseText = response["output"]["message"]["content"][0]["text"]
            logger.debug(f"Generated response for test message: {responseText}")
            return responseText
        # Parse event time from message (if present)
        eventtime = get_eventtime(msg) or None
        # Current timestamp in UTC
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Add user message to history
        history.append({"role":"user", "content":[{"text":f"[Query-{timestamp}] {msg}"}]})
        logger.debug(f"Appended user message to history for '{username}'")
        # Generate model response using the full chat history
        response = self.client.converse(
            modelId=self.model,
            messages=history,
            system=[{'text': self.system_instructions}],
            inferenceConfig={"maxTokens": self.max_output_tokens, "temperature": self.temperature, "topP": self.top_p}
        )
        responseText = response["output"]["message"]["content"][0]["text"]
        logger.info(f"Generated model response for '{username}'")
        # Update timestamp for model response
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Add model response to history
        history.append({"role":"assistant", "content":[{"text":responseText}]})
        logger.debug(f"Appended model message to history for '{username}'")         
        # Write updated history back to S3
        self.s3.obj_write(f"chat-history/{username}.json", history)
        logger.debug(f"Updated history written to S3 for '{username}'")
        return responseText