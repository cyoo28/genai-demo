#!/usr/bin/env python3

import os
import sys
import logging
import secrets
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

# Add parent folder to sys.path so we can import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "aws")))
from aws_config import AWSConfig

# Configure Logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)-11s [%(levelname)s] %(message)s (%(name)s:%(lineno)d)"
)
logger = logging.getLogger(__name__)
# Initialize AWS config
aws_config = AWSConfig()
try:
    config_store = aws_config.create()
except Exception as e:
    logger.error(f"Failed to initialize AWS config: {e}", exc_info=True)
    sys.exit(1)

# Flask app setup
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config["Config"] = config_store
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30) # Time out session after 30 minutes
app.secret_key = os.urandom(32)

# Check if session is available
def check_session():
    # Check if the user has a valid session
    sessionToken = request.cookies.get("sessionToken")
    userMan = app.config["Config"]["userMan"]
    if sessionToken:
        return userMan.check_session_token(sessionToken)
    return None

# Update session expiration
def update_session(username):
    userMan = app.config["Config"]["userMan"]
    newExpire = datetime.now() + timedelta(minutes=30)
    userMan.update_session(username, newExpire)

# Set route for unspecified page
@app.route("/")
def index():
    # If the user is already signed in redirect to /chat, otherwise redirect to /home
    username = check_session()
    return redirect(url_for("chat") if username else url_for("home"))

# Set route for /home page
@app.route("/home")
def home():
    # If the user is already signed in redirect to /chat, otherwise render home.html
    username = check_session()
    return redirect(url_for("chat")) if username else render_template("home.html")

# Set route for /login page
@app.route("/login", methods=["GET", "POST"])
def login():
    errorMessage = None
    userMan = app.config["Config"]["userMan"]
    # Allow users to input username and password
    if request.method == "POST":
        # Get username and password entered
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        # Check that the username/password is a valid login
        user = userMan.find_user(username)
        # Error if username or password is incorrect
        if not userMan.check_password(user, password):
            errorMessage = "Invalid username or password"
        # Error if user email has not been confirmed
        elif not userMan.check_confirm(user):
            errorMessage = "User email has not been confirmed"
        if errorMessage:
            # If there is an error, rerender login.html and display error
            logger.warning(f"Failed login attempt for user: {username}")
            return render_template("login.html", error=errorMessage)
        # Otherwise, redirect to /chat
        else:
            # Generate session token
            sessionToken = secrets.token_urlsafe(32)
            expire = datetime.now(timezone.utc) + timedelta(minutes=30)
            # Add session
            userMan.add_session(username, sessionToken, expire)
            # Set session cookie
            response = redirect(url_for("chat"))
            response.set_cookie(
                "sessionToken",
                sessionToken,
                httponly=True,
                secure=False,
                samesite="Lax",
            )
            # Redirect to the chat
            logger.info(f"User {username} logged in with session {sessionToken}")
            return response
    # Handle error query parameters
    error_map = {
        "session_expired": "Your session has expired due to inactivity. Please log in again.",
        "confirm_expired": "Email confirmation has expired. Try signing up again.",
        "reset_expired": "Password reset has expired. Try requesting again."
    }
    errorMessage = error_map.get(request.args.get("error"), None)
    # Render login.html
    return render_template("login.html", error=errorMessage)

# Set route for /logout page
@app.route("/logout")
def logout():
    userMan = app.config["Config"]["userMan"]
    # Remove session from sessions table
    username = check_session()
    if username:
        userMan.delete_token(username, userMan.sessionTable)
        logger.info(f"User {username} logged out and session removed.")
    else:
        logger.info("Invalid or expired session during logout.")
    # Remove cookie
    response = render_template("logout.html")
    response = app.make_response(response)
    response.delete_cookie("sessionToken")
    # Render logout.html
    return response

# Set route for /signup page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    userMan = app.config["Config"]["userMan"]
    # Allow users to input username, password, and email
    if request.method == "POST":
        newUsername = request.form.get("username", "").strip()
        newPassword = request.form.get("password", "")
        newEmail = request.form.get("email", "").strip()
        confirmEmail = request.form.get("confirmEmail", "").strip()
        # Check for errors
        errorMessage = None
        # Error if one of the fields is not filled out
        if not newUsername or not newEmail or not newPassword:
            errorMessage = "Please enter a username, email, and password"
        # Error if the email confirmation does not match
        elif newEmail != confirmEmail:
            errorMessage = "Emails do not match"
        else:
            # Error if the username or email is already in use
            (user_exists, email_exists) = userMan.user_exists(newUsername, newEmail)
            if user_exists:
                errorMessage = "Username already exists"
            elif email_exists:
                errorMessage = "Email already in use"
        # If there's an error
        if errorMessage:
            logger.warning(f"Failed signup attempt for user: {newUsername}")
            # Rerender signup.html and display error
            return render_template("signup.html", error=errorMessage)
        # If no error,
        else:
            # Add new user
            userMan.add_user(newUsername, newEmail, newPassword)
            # Generate confirmation token
            token = secrets.token_urlsafe(32)
            expire = datetime.now()+timedelta(days=1)
            userMan.add_confirm(newUsername, token, expire)
            # Create confirmation link
            with app.app_context():
                confirmationUrl = url_for('confirm_email', token=token, _external=True)
            # Make datetime more readable
            emailExpire = expire.strftime("%A, %B %d, %Y at %I:%M %p")
            # Send email through SES
            subject = "Chatbot Helper Signup Confirmation"
            body = f"""Hello {newUsername},

                Thank you for signing up! Please confirm your email address by clicking the link below:

                {confirmationUrl}

                This link will expire in 24 hours (at {emailExpire}).

                If you did not sign up for this account, please ignore this email.

                Best regards,  
                Chatbot Helper Security Team
            """
            app.config["Config"]["emailClient"].send_email([newEmail], subject, body)
            logger.info(f"User {newUsername} signed up.")
            # Render signup_success.html
            return render_template("signup_success.html")
    # Render signup.html
    return render_template("signup.html")

# Set route for /confirm_email page
@app.route("/confirm_email")
def confirm_email():
    # Check that confirmation token is valid
    token = request.args.get("token")
    userMan = app.config["Config"]["userMan"]
    username = userMan.check_confirm_token(token)
    # If token is invalid
    if not username:
        logger.warning(f"Failed email confirmation attempt for user: {username}")
        # Redirect to login page and display error
        return redirect(url_for("login", error="confirm_expired"))
    # Otherwise, confirm the user
    userMan.update_confirm(username, token)
    logger.info(f"User {username} confirmed email")
    # Render confirm_email_success.html
    return render_template("confirm_email_success.html")

# Set route for /forgot_password page
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    userMan = app.config["Config"]["userMan"]
    # Allow users to input email
    if request.method == "POST":
        email = request.form["email"]
        matchedUser = userMan.find_user_by_email(email)
        # If the email exists in the userbase
        if matchedUser:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            expire = datetime.now()+timedelta(minutes=10)
            userMan.add_reset(matchedUser["username"], token, expire)
            # Send an email
            with app.app_context():
                resetUrl = url_for('reset_password', token=token, _external=True)
            # Make datetime more readable
            emailExpire = expire.strftime("%A, %B %d, %Y at %I:%M %p")
            # Send email through SES
            subject = "Chatbot Helper Reset Request"
            body = f"""Hello {matchedUser["username"]},

                Please reset your account password by clicking the link below:

                {resetUrl}

                This link will expire in 10 minutes (at {emailExpire}).

                If you did not request to reset your password, please ignore this email.

                Best regards,  
                Chatbot Helper Team
            """
            app.config["Config"]["emailClient"].send_email([email], subject, body)
            # Render forgot_password_success.html
            logger.info(f"User {matchedUser['username']} requested password reset.")
            return render_template("forgot_password_success.html", email=email)
        else:
            # Rerender forgot_password_success.html and display error
            logger.warning(f"Failed password reset request for user: {email}")
            return render_template("forgot_password.html", error="Email not found")
    # Render forgot_password.html
    return render_template("forgot_password.html")

# Set route for /reset_password page
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    # Check that reset token is valid
    token = request.args.get("token")
    userMan = app.config["Config"]["userMan"]
    username = userMan.check_reset_token(token)
    # If token is invalid
    if not username:
        logger.warning(f"Failed password reset attempt for user: {username}")
        # Redirect to login page and display error
        return redirect(url_for("login", error="reset_expired"))
    # Otherwise, allow password reset
    if request.method == "POST":
        # Allow users to input new password
        newPassword = request.form["password"]
        confirmPassword = request.form["confirmPassword"]
        # Check for errors
        errorMessage = None
        if not newPassword or not confirmPassword:
            errorMessage = "Please enter email and confirmation"
        elif newPassword!=confirmPassword:
            errorMessage = "Passwords do not match"
        if errorMessage:
            # Rerender reset_password.html and display error
            return render_template("reset_password.html", error=errorMessage)
        # If no errors, reset the password
        userMan.update_reset(username, newPassword)
        logger.info(f"User {username} reset password.")
        # Render reset_password_success.html
        return render_template("reset_password_success.html")
    # Render reset_password.html
    return render_template("reset_password.html")

# Set route for /change_password page
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    # Check that user is logged in
    username = check_session()
    if username:
        # Update session expiration
        update_session(username)
    else:
        # If not redirect to login page and display error
        return redirect(url_for("login", error="session_expired"))
    userMan = app.config["Config"]["userMan"]
    # Allow user to input old password, new password, and password confirmation
    if request.method == "POST":
        user = userMan.find_user(username)
        oldPassword = request.form["oldPassword"]
        newPassword = request.form["newPassword"]
        confirmPassword = request.form["confirmPassword"]
        # Check for errors
        errorMessage = None
        # Error if the current password is incorrect
        if not userMan.check_password(user, oldPassword):
            errorMessage = "Incorrect current password."
        # Error if the email confirmation does not match
        if newPassword != confirmPassword:
            errorMessage = "Passwords do not match"
        if errorMessage:
            # Rerender change_password.html and display error
            logger.warning(f"Failed password change attempt for user: {username}")
            return render_template('change_password.html', error=errorMessage)
        # If no errors, change the password
        userMan.change_password(username, newPassword)
        logger.info(f"User {username} changed password.")
        # Redirect to /chat
        return redirect(url_for("chat"))
    # Render change_password.html
    return render_template("change_password.html")

# Set route for /chat page
@app.route("/chat")
def chat():
    # Check that user is logged in
    username = check_session()
    if username:
        # Update session expiration
        update_session(username)
    else:
        # If not redirect to login page and display error
        return redirect(url_for("login", error="session_expired"))
    # Render chat.html
    return render_template("chat.html", username=username)

# Set backend for /send
@app.route("/send", methods=["POST"])
def send_message():
    # Check that user is logged in
    username = check_session()
    if username:
        # Update session expiration
        update_session(username)
    else:
        # If not redirect to login page and display error
        return redirect(url_for("login", error="session_expired"))
    # Extract json for incoming request
    data = request.get_json()
    # Extract message
    userInput = data.get("message", "").strip()
    logger.debug(f"User {username} sent message: {userInput}")
    # Reject empty messages
    if not userInput:
        return jsonify({"error": "Empty message"}), 400
    # Enforce max message length
    maxLength = 2000
    if len(userInput) > maxLength:
        return jsonify({"error": f"Message too long. Limit is {maxLength} characters."}), 400
    try:
        # If there is a message, try to send the message to chatbot
        response = app.config["Config"]["genaiClient"].send_message(username, userInput)
        logger.debug(f"Model response for {username}: {response}")
        # Return the response
        return jsonify({"response": response})
    except Exception as e:
        # If there is an error while handling the message,
        logger.error(f"Error processing message for {username}: {e}", exc_info=True)
        # Return the error
        return jsonify({"error": str(e)}), 500

# Set route /favicon.ico for browsers
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'chatbot.ico',
        mimetype='image/x-icon'
    )

# Set route /ping to respond to health checks
@app.route("/ping")
def ping():
    return "pong"

# Create a global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error("Unhandled exception occurred", exc_info=True)
    return jsonify({"error": "An internal server error occurred"}), 500

if __name__ == "__main__":
    # Start webapp
    logger.info("Starting Flask app on http://0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080)
