import logging
from datetime import datetime, timezone
from google.genai.types import GenerateContentConfig
import vertexai
from google import genai

logger = logging.getLogger(__name__)

# Vertex AI client wrapper
class VertexClient:
    def __init__(self, region, session, gcsClient):
        # Set up GCS client
        self.gcs = gcsClient
        # Model settings
        self.model = "gemini-2.0-flash-001"
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
        self.top_k = 20
        self.max_output_tokens = 400
        self.presence_penalty = 0.0
        self.frequency_penalty = 0.0
        # Set up VertexAI client
        self.client = genai.Client(
            vertexai=True,
            project=session["project"],
            location=region,
            credentials=session["credentials"],
        )
        # Set up RAG/corpus
        vertexai.init(
            credentials=session["credentials"],
            project=session["project"],
            location=region
        )
        logger.info(f"VertexClient initialized for region '{region}'")

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
        # Keys for storing history in GCS
        key = f"chat-history/{username}.json"
        # Load existing history if they exist in GCS
        if self.gcs.obj_check(key):
            history, _ = self.gcs.obj_read(key)
            logger.debug(f"Loaded history for user '{username}'")
        # Configure model generation parameters
        config = GenerateContentConfig(
                system_instruction=self.system_instructions,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                max_output_tokens=self.max_output_tokens,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty
            )
        if isTest:
            logger.info(f"Test message detected for '{username}' - not adding to history")
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            prompt = history.copy()
            prompt.append({"role":"user", "parts":[{"text":f"[Query-{timestamp}] {msg}"}]})
            response = self.client.models.generate_content(model=self.model, config=config, contents=prompt)
            logger.debug(f"Generated response for test message: {response.text}")
            return response
        # Current timestamp in UTC
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Add user message to both history
        history.append({"role":"user", "parts":[{"text":f"[Query-{timestamp}] {msg}"}]})
        logger.debug(f"Appended user message to history for '{username}'")
        # Generate model response using the full chat history
        response = self.client.models.generate_content(model=self.model, config=config, contents=history)
        logger.info(f"Generated model response for '{username}'")
        # Add model response to both history
        history.append({"role":"model", "parts":[{"text":response.text}]})
        logger.debug(f"Appended model message to history for '{username}'")         
        # Write updated history back to GCS
        self.gcs.obj_write(f"chat-history/{username}.json", history)
        logger.debug(f"Updated history written to GCS for '{username}'")
        return response