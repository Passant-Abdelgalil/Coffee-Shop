import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-p0xs7y2g.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee-shop'


# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header


def get_token_auth_header():
    '''
    attempt to get the header from the request
        raise an AuthError if no header is present
    attempt to split bearer and the token
        raise an AuthError if the header is malformed

    return the token part of the header
    '''

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

    elif len(parts) != 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    token = parts[1]
    return token


def check_permissions(permission, payload):
    '''
    INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    raise an AuthError if permissions are not included in the payload
    raise an AuthError if the requested permission string is
                            not in the payload permissions array

    return true otherwise
    '''

    if 'permissions' not in payload:
        print("no permissions")
        raise AuthError({
            "code": "invalid_payload",
            "description": "permissions are not included in the payload"
        }, 401)

    if permission in payload['permissions']:
        print("permited")
        return True
    raise AuthError({
        "code": "invalid_permission",
        "description": "the requested permission is not in the payload"
    }, 401)


def verify_decode_jwt(token):
    '''
    INPUTS
        token: a json web token (string)
    the token should be an Auth0 token with key id (kid)
    verify the token using Auth0 /.well-known/jwks.json
    decode the payload from the token
    validate the claims

    return the decoded payload
    '''
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
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
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
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
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 401)
    raise AuthError({
        'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
    }, 401)


def requires_auth(permission=''):
    '''
    INPUTS
        permission: string permission (i.e. 'post:drink')

    uses the get_token_auth_header method to get the token
    uses the verify_decode_jwt method to decode the jwt
    uses the check_permissions method validate claims
                and check the requested permission

    return the decorator that passes the decoded payload to the decorated method
    '''
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(*args, **kwargs)

        return wrapper
    return requires_auth_decorator
