import logging
import bcrypt
from datetime import datetime

logger = logging.getLogger(__name__)

# Class for managing users with SQL client
class UserManager:
    def __init__(self, sqlClient):
        # sqlClient for managing SQL tables
        self.sqlClient = sqlClient
        # Table for webapp users
        self.userTable = "users"
        # Table for users that require confirmation
        self.confirmTable = "confirmation"
        # Table for users that request a password reset
        self.resetTable = "password_reset"
        # Table for user sessions
        self.sessionTable = "sessions"
        logger.info("UserManager initialized")

    # Helper function to load sql table
    def _load_table(self, table):
        logger.debug(f"Loading table '{table}'")
        return self.sqlClient.read_table(table)

    # Find a user based on their username
    def find_user(self, username):
        # Load users
        users = self._load_table(self.userTable)
        # Check if there is a user that matches the username
        user = next((u for u in users if u["username"]==username), None)
        if user:
            logger.debug(f"Found user '{username}'")
        else:
            logger.debug(f"User '{username}' not found")
        return user

    # Find a user based on their email
    def find_user_by_email(self, email):
        # Load users
        users = self._load_table(self.userTable)
        # Check if there is a user that matches the email
        user = next((u for u in users if u["email"]==email), None)
        if user:
            logger.debug(f"Found user with email '{email}'")
        else:
            logger.debug(f"No user found with email '{email}'")
        return user
    
    # Check that the password is correct
    def check_password(self, user, password):
        # Check whether or not the entered password matches the database password
        result = user and bcrypt.checkpw(password.encode(), user["password"].encode())
        logger.debug(f"Password check for user '{user['username'] if user else 'None'}': {result}")
        return result
    
    # Check that the user is confirmed
    def check_confirm(self, user):
        # Check user confirmation status
        status = user["confirmed"]
        logger.debug(f"Confirmation status for user '{user['username']}': {status}")
        return status

    # Change password for user
    def change_password(self, username, password):
        # Hash the password
        salt = bcrypt.gensalt()
        hashedPassword = bcrypt.hashpw(password.encode(), salt)
        # Update password for user
        userUpdateValue  = {"password": hashedPassword}
        userUpdateFilter = {"username": username}
        self.sqlClient.update_entry(userUpdateValue, userUpdateFilter, self.userTable)
        logger.info(f"Password changed for user '{username}'")

    # Check if the username or email is already in use
    def user_exists(self, username, email):
        # Load users
        users = self._load_table(self.userTable)
        # Check if username or email match any existing users
        usernameMatch = any(username==user["username"] for user in users)
        emailMatch = any(email==user["email"] for user in users)
        logger.debug(f"user_exists('{username}', '{email}') => (username: {usernameMatch}, email: {emailMatch})")
        # Return results
        return (usernameMatch, emailMatch)
    
    # Add new user to users table
    def add_user(self, username, email, password):
        # Hash the password
        salt = bcrypt.gensalt()
        hashedPassword = bcrypt.hashpw(password.encode(), salt)
        # Add new user info to user table
        userEntry = {"username": username, "password": hashedPassword, "email": email, "confirmed": False}
        self.sqlClient.create_entry(userEntry, self.userTable)
        logger.info(f"Added new user '{username}' with email '{email}'")
    
    # Add token to table
    def add_token(self, username, token, expire, table):
        # Set expiration limit for confirmation
        sqlExpire = expire.strftime('%Y-%m-%d %H:%M:%S')
        # Add new token to table
        entry = {"username": username, "token": token, "expiration": sqlExpire}
        self.sqlClient.create_entry(entry, table)
        logger.info(f"Added token for user '{username}' in table '{table}' (expires {sqlExpire})")
    
    def delete_token(self, username, table):
        # Delete old token if it exists
        deleteFilter = {"username": username}
        self.sqlClient.delete_entry(deleteFilter, table)

    # Add new user token to confirmation table 
    def add_confirm(self, username, token, expire):
        self.delete_token(username, self.confirmTable)
        self.add_token(username, token, expire, self.confirmTable)
    
    # Add user token to reset table 
    def add_reset(self, username, token, expire):
        self.delete_token(username, self.resetTable)
        self.add_token(username, token, expire, self.resetTable)

    # Add session token to session table
    def add_session(self, username, token, expire):
        self.delete_token(username, self.sessionTable)
        self.add_token(username, token, expire, self.sessionTable)

    # Check that the token has not expired
    def _check_token(self, token, table):
        # Check that token is present
        if not token:
            # Return nothing if there is no token
            return None
        # Load users that need token
        tokens = self._load_table(table)
        # Find entry if there is one that matches the token 
        tokenEntry = next((row for row in tokens if row["token"]==token), None)
        # Check that the token hasn't expired
        if tokenEntry and datetime.now() <= tokenEntry["expiration"]:
            # Return confirmed username if token is valid
            logger.debug(f"Valid token for user '{tokenEntry['username']}' in table '{table}'")
            return tokenEntry["username"]
        # Return nothing if it has expired
        logger.warning(f"Token invalid or expired in table '{table}'")
        return None

    # Check that confirmation has not expired
    def check_confirm_token(self, token):
        return self._check_token(token, self.confirmTable)
    
    # Check that reset has not expired
    def check_reset_token(self, token):
        return self._check_token(token, self.resetTable)
    
    # Check that session has not expired
    def check_session_token(self, token):
        return self._check_token(token, self.sessionTable)

    # Update confirmation status for user
    def update_confirm(self, username, token):
        # Update confirmation status for user
        userUpdateValue = {"confirmed": True}
        userUpdateFilter = {"username": username}
        self.sqlClient.update_entry(userUpdateValue, userUpdateFilter, self.userTable)
        # Delete the user's entry in the confirmation table
        confirmDeleteFilter = {"token": token}
        self.sqlClient.delete_entry(confirmDeleteFilter, self.confirmTable)
        logger.info(f"User '{username}' confirmed and token '{token}' deleted")

    # Update password for user
    def update_reset(self, username, password):
        # Update password for user
        self.change_password(username, password)
        # Delete the user's entry in the reset table
        resetDeleteFilter = {"username": username}
        self.sqlClient.delete_entry(resetDeleteFilter, self.resetTable)
        logger.info(f"Password reset for user '{username}' and reset token cleared")

    # Update session for user
    def update_session(self, username, expire):
        sqlExpire = expire.strftime('%Y-%m-%d %H:%M:%S')
        # Update confirmation status for user
        sessionUpdateValue = {"expiration": sqlExpire}
        sessionUpdateFilter = {"username": username}
        self.sqlClient.update_entry(sessionUpdateValue, sessionUpdateFilter, self.sessionTable)