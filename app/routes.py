from flask import Blueprint, jsonify, g, current_app, request
import logging
import os
import stripe
from prometheus_flask_exporter import PrometheusMetrics
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from .utils import requires_auth
from . import models, database
from sqlalchemy.orm import Session

# --- Setup Prometheus Metrics ---

# --- Setup Logging ---
# Create a logger
log_directory = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(log_directory, '..', 'app.log') # Assumes this code is in the 'app' directory

# 2. Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# 3. Create a handler to write to a file
# Using RotatingFileHandler is a good practice
logHandler = RotatingFileHandler(log_file_path, maxBytes=1000000, backupCount=5)

# 4. Create a JSON formatter
formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')

consoleHandler = logging.StreamHandler() 
consoleHandler.setFormatter(formatter) # Use the same JSON formatter
logger.addHandler(consoleHandler)

# 5. Set the formatter and add the handler
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
# --- End Logging Setup ---

# 1. Create a Blueprint object
main = Blueprint('main', __name__)
metrics = PrometheusMetrics(main)
stripe.api_key = os.getenv('STRIPE_API_KEY')

@main.route('/')
def me():
    logging.info("Main page has been accessed.")
    return "Welcome!"

# 2. Define the route on the Blueprint, not on 'app'
@main.route('/health')
def health_check():
    print(f"Health check endpoint was called.")
    logging.info(" check endpoint was called.")
    return jsonify({"status": "healthy"}), 200

@main.route('/api/user/onboard', methods=['POST'])
@requires_auth # This decorator validates the JWT and attaches the payload
def sync_user():
    """
    Handles user onboarding after successful Auth0 login.
    - Checks if a user exists based on their Auth0 ID ('sub' claim).
    - If not, creates a new user, assigns a default role, and logs the action.
    - If the user exists, it does nothing.
    """
    # 1. Get user info from the validated Auth0 token payload
    logging.info(f"An error occurred during user onboarding:")
    payload = g.current_user
    print(f"payload:")
    auth0_user_id = payload.get('sub')
    email = payload.get('https://my-template-app.com/email') 

    if not auth0_user_id or not email:
        return jsonify({
            "code": "bad_request",
            "description": "Auth0 token payload is missing 'sub' or 'email'."
        }), 400

    db: Session = database.SessionLocal()
    try:
        # 2. Check if the user already exists in our database
        existing_user = db.query(models.User).filter(
            models.User.auth0_user_id == auth0_user_id
        ).first()

        if existing_user:
            return jsonify({
                "status": "success", 
                "message": "User already exists."
            }), 200

        # --- User does not exist, proceed with creation ---

        # 3. Find the default role to assign to the new user
        # This assumes you have a 'user' role seeded in your database.
        default_role = db.query(models.Role).filter(models.Role.name == 'user').first()
        if not default_role:
            # This is a server configuration error, so we should log it and fail.
            print("CRITICAL: Default role 'user' not found in the database.")
            return jsonify({
                "code": "server_error",
                "description": "Server configuration error: default role missing."
            }), 500

        # 4. Create the new user instance
        new_user = models.User(
            auth0_user_id=auth0_user_id,
            email=email
            # subscription_plan defaults to 'free' as per the model
        )
        
        # 5. Assign the default role
        new_user.roles.append(default_role)
        db.add(new_user)
        
        # We must flush the session to get the generated UUID for the new_user.id
        # This is necessary before creating the audit log entry that references it.
        db.flush()

        # 6. Create an audit log for the user creation event
        audit_log_entry = models.AuditLog(
            user_id=new_user.id,
            action='user.created',
            details={"source": "auth0_onboarding", "assigned_roles": ["user"]}
        )
        db.add(audit_log_entry)

        # 7. Commit all changes to the database
        db.commit()
        
        return jsonify({
            "status": "success",
            "message": "New user created and assigned default role."
        }), 201

    except Exception as e:
        db.rollback()
        print(f"An error occurred during user onboarding: {e}")
        return jsonify({
            "code": "server_error",
            "description": "An unexpected error occurred."
        }), 500
    finally:
        db.close()

@main.route('/api/create-checkout-session', methods=['POST'])
@requires_auth # Ensures only a logged-in user can start a checkout
def create_checkout_session():
    """
    Creates a Stripe Checkout session for the authenticated user.
    """
    db: Session = database.SessionLocal()
    try:
        auth0_user_id = g.current_user.get('sub')
        user = db.query(models.User).filter(models.User.auth0_user_id == auth0_user_id).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        price_id = os.getenv('STRIPE_PRICE_ID')
        frontend_url = os.getenv('NEXT_PUBLIC_APP_URL')

        # Create a new checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            # These are the URLs Stripe will redirect to after the checkout
            success_url=f'{frontend_url}/dashboard?success=true',
            cancel_url=f'{frontend_url}/dashboard?canceled=true',
            # CRITICAL: This securely links the Stripe session to your internal user ID
            client_reference_id=str(user.id)
        )
        
        # Return the session URL to the frontend
        return jsonify({'url': checkout_session.url})

    except Exception as e:
        current_app.logger.error(f"Stripe session creation failed: {e}")
        return jsonify(error=str(e)), 500
    finally:
        db.close()

@main.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """
    Handles incoming webhook events from Stripe to fulfill orders.
    This endpoint is public but secured by verifying the Stripe signature.
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    event = None

    # Verify the event came from Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return 'Invalid signature', 400

    try:
        # Handle the 'checkout.session.completed' event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Retrieve our internal user ID from the session metadata
            user_id = session.get('client_reference_id')
            stripe_customer_id = session.get('customer')

            if not user_id or not stripe_customer_id:
                return "Webhook Error: Missing required data in session.", 400

            db: Session = database.SessionLocal()
            # Find the user and update their subscription status in our database
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                user.subscription_plan = 'premium'
                user.stripe_customer_id = stripe_customer_id
                db.commit()
                current_app.logger.info(f"User {user.email} subscription updated to premium.")
        elif event['type'] == 'customer.subscription.deleted':
            # --- This handles CANCELLATIONS ---
            session = event['data']['object']
            
            # Retrieve our internal user ID from the session metadata
            stripe_customer_id = session.get('customer')
            if not stripe_customer_id:
                return "Webhook Error: Missing required data in session.", 400
            
            db: Session = database.SessionLocal()
            # Find the user and update their subscription status in our database
            user = db.query(models.User).filter(models.User.stripe_customer_id == stripe_customer_id).first()
            if user:
                user.subscription_plan = 'free'
                db.commit()
                current_app.logger.info(f"User {user.email} plan canceled, set to 'free'.")
        # Add handling for other event types as needed
    except Exception as e:
            db.rollback()
            current_app.logger.error(f"Webhook DB update failed: {e}")
            return "Server error during DB update", 500
    finally:
        db.close()

    return 'Success', 200

@main.route('/error')
def trigger_error():
    """
    This endpoint intentionally causes a division-by-zero error
    to test the application's error handling and logging.
    """
    try:
        # This line will always raise a ZeroDivisionError
        print(f"An error occurred during user onboarding:")
        result = 1 / 0
    except Exception as e:
        # Log the error with its type and message in a structured way
        logging.error(
            "An exception occurred on the /error endpoint",
            extra={
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        )
        
        # Return a user-friendly JSON response and a 500 status code
        response = jsonify(error="An internal server error occurred.")
        response.status_code = 500
        return response
    

@main.route('/api/user/status')
@requires_auth # Ensures only authenticated users can access this endpoint
def user_status():
    """
    Returns the subscription status of the authenticated user.
    """
    db: Session = database.SessionLocal()
    try:
        auth0_user_id = g.current_user.get('sub')
        user = db.query(models.User).filter(models.User.auth0_user_id == auth0_user_id).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "email": user.email,
            "subscription_plan": user.subscription_plan
        })

    except Exception as e:
        current_app.logger.error(f"Failed to fetch user status: {e}")
        return jsonify(error="Server error"), 500
    finally:
        db.close()

@main.route('/api/create-portal-session', methods=['POST'])
@requires_auth # Ensures only an authenticated user can access this
def create_portal_session():
    """
    Creates a Stripe Customer Portal session for the authenticated user,
    allowing them to manage their billing and subscription details.
    """
    db: Session = database.SessionLocal()
    try:
        # 1. Identify the user from the validated Auth0 JWT
        auth0_user_id = g.current_user.get('sub')
        user = db.query(models.User).filter(models.User.auth0_user_id == auth0_user_id).first()

        # 2. CRITICAL: Validate that the user is an existing Stripe customer.
        # A user who has never subscribed will not have a stripe_customer_id.
        if not user or not user.stripe_customer_id:
            return jsonify({"error": "User not found or is not a Stripe customer"}), 404

        # 3. Get the return URL from environment variables
        frontend_url = os.getenv('NEXT_PUBLIC_APP_URL')
        if not frontend_url:
             raise ValueError("NEXT_PUBLIC_APP_URL environment variable not set.")

        # 4. Create a Billing Portal Session on Stripe's servers
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f'{frontend_url}/dashboard',
        )

        # 5. Return the unique session URL to the frontend
        return jsonify({'url': portal_session.url})

    except Exception as e:
        current_app.logger.error(f"Stripe portal session creation failed: {e}")
        return jsonify(error=str(e)), 500
    finally:
        db.close()

# You can add all your other API routes to this file
# For example:
# @main.route('/api/users')
# def get_users():
#     ...
