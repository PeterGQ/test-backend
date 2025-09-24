import os
from functools import wraps
import json
from urllib.request import urlopen
from flask import request, g, jsonify
from jose import jwt
# from auth0.management import Auth0

# --- CONFIGURE YOUR AUTH0 VARIABLES ---
# You can find these in your Auth0 Dashboard
AUTH0_DOMAIN = os.environ['AUTH0_DOMAIN'] # e.g., 'dev-12345.us.auth0.com'
API_AUDIENCE = os.environ['AUTH0_AUDIENCE'] # The identifier of your API in Auth0
ALGORITHMS = ['RS256']
# ------------------------------------


# def get_auth0_management_client():
#     """
#     Initializes and returns an Auth0 Management API client.
#     Requires Auth0 domain and M2M application credentials as environment variables.
#     """
#     domain = os.getenv('AUTH0_DOMAIN')
#     # You need to create a Machine-to-Machine application in Auth0 to get these
#     client_id = os.getenv('AUTH0_MGMT_CLIENT_ID') 
#     client_secret = os.getenv('AUTH0_MGMT_CLIENT_SECRET')

#     if not all([domain, client_id, client_secret]):
#         print("Error: Auth0 Management API credentials are not fully configured.")
#         return None

#     auth0 = Auth0(domain, client_id, client_secret)
#     return auth0.users

# def update_auth0_metadata(auth0_user_id, metadata):
#     """
#     Updates the app_metadata for a given user in Auth0.
    
#     :param auth0_user_id: The ID of the user to update (e.g., 'auth0|...').
#     :param metadata: A dictionary containing the metadata to set.
#     """
#     try:
#         mgmt_client = get_auth0_management_client()
#         if mgmt_client:
#             mgmt_client.update(auth0_user_id, {'app_metadata': metadata})
#             print(f"Successfully updated app_metadata for {auth0_user_id}")
#     except Exception as e:
#         print(f"Failed to update Auth0 metadata: {e}")


# Custom AuthError Exception
class AuthError(Exception):
    """
    A standardized way to communicate auth failure modes
    """
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()

    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)
    elif len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)
    elif len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    token = parts[1]
    return token


def verify_decode_jwt(token):
    """
    Verifies and decodes the JWT.
    Checks the signature using the public key from Auth0 (JWKS).
    Checks the claims (audience, issuer).
    """
    # GET THE PUBLIC KEY FROM AUTH0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    
    # GET THE DATA IN THE HEADER
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Error decoding token headers.'
        }, 401)

    # CHOOSE THE CORRECT KEY
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    
    # Finally, verify the key
    if rsa_key:
        try:
            # USE THE KEY TO VALIDATE THE JWT
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/'
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please check the audience and issuer.'
            }, 401)
            
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
            
    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)


# The Decorator function
def requires_auth(f):
    """Determines if the Access Token is valid and attaches the payload"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            
            # Make the payload available to the decorated function
            # g is a context-local object in Flask for temporary storage during a request
            g.current_user = payload
            
        except AuthError as e:
            # Return a JSON response if an AuthError is raised
            return jsonify(e.error), e.status_code
            
        return f(*args, **kwargs)

    return decorated