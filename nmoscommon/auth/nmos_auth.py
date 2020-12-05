# Copyright 2019 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import json

from os import path, sep
from time import time
from flask import abort, request
from functools import reduce, wraps
from six.moves.urllib.parse import urljoin, parse_qs
from requests.exceptions import RequestException
from authlib.jose import jwt, jwk
from authlib.common.errors import AuthlibBaseError
from authlib.oauth2.rfc6749.errors import MissingAuthorizationError, UnsupportedTokenTypeError
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from ..mdnsbridge import IppmDNSBridge
from ..nmoscommonconfig import config as _config
from .claims_validator import JWTClaimsValidator, generate_claims_options, logger

# DISCOVERY AND CONFIG
MDNS_SERVICE_TYPE = "nmos-auth"
OAUTH_MODE = _config.get('oauth_mode', False)

# CERTIFICATE FALLBACK PATH
NMOSAUTH_DIR = path.abspath(path.join(sep, 'var', 'nmosauth'))
CERT_FILE_PATH = path.join(NMOSAUTH_DIR, "certificate.pem")

SERVER_METADATA_ENDPOINTS = [
    '.well-known/oauth-authorization-server',
    '.well-known/openid-configuration'
]


def get_auth_server_url(serviceType=MDNS_SERVICE_TYPE):

    bridge = IppmDNSBridge()  # Only instantiated when making request for keys
    # Look for an auth_url override option in config for non DNS-SD setups
    if _config.get('auth_server_url', False):
        auth_href = _config.get('auth_server_url')
        return auth_href
    auth_href = bridge.getHref(serviceType)
    if auth_href:
        return auth_href
    else:
        return None


def get_auth_server_metadata(auth_href):
    for metadata_endpoint in SERVER_METADATA_ENDPOINTS:
        try:
            url = urljoin(auth_href, metadata_endpoint)
            resp = requests.get(url, timeout=0.5, proxies={'http': ''})
            resp.raise_for_status()  # Raise exception if not a 2XX status code
            return resp.json(), url
        except RequestException:
            pass
    return (None, None)


class RequiresAuth(object):

    refresh_key_interval = 3600  # Time in Seconds until Public_key is refreshed
    public_key = None  # Shared Class Variable to share public key between instances
    key_last_refreshed = 0  # UTC time the public key was last fetched

    def __init__(self, condition=OAUTH_MODE, api_name=""):
        logger.writeWarning("The @RequiresAuth decorator is now deprecated in favour of the AuthMiddleware Class")
        self.condition = condition
        self.api_name = api_name
        self.auth_href = None

    @classmethod
    def update_public_key(cls, public_key):
        cls.public_key = public_key
        cls.key_last_refreshed = time()

    def _get_jwk_url(self, service_type):
        auth_href = get_auth_server_url(service_type)
        if auth_href:
            self.auth_href = auth_href
        elif not auth_href and self.auth_href:
            logger.writeWarning(
                "Could not find service of type: '{}'. Using previously found metadata endpoint: {}.".format(
                    service_type, self.auth_href))
        else:
            logger.writeError(
                "No services of type '{}' could be found. Cannot validate Authorization token.".format(service_type))
            abort(500, "A valid authorization server could not be found via DNS-SD")
        metadata, metadata_url = get_auth_server_metadata(self.auth_href)
        if metadata is not None and "jwks_uri" in metadata:
            return metadata.get("jwks_uri")
        else:
            # Construct default URI
            logger.writeWarning("Could not locate metadata endpoint at {}".format(self.auth_href))
            abort(500, "A valid authorization server could not be found via DNS-SD")

    def get_jwks(self):
        try:
            jwk_href = self._get_jwk_url(MDNS_SERVICE_TYPE)
            logger.writeInfo('JWK endpoint is: {}'.format(jwk_href))
            jwk_resp = requests.get(jwk_href, timeout=0.5, proxies={'http': ''})
            jwk_resp.raise_for_status()  # Raise error if status !=200
        except RequestException as e:
            logger.writeError("Error: {}. Cannot find JSON Web Key Endpoint at {}.".format(e, jwk_href))
            abort(500, "Could not retrieve the JSON Web Key from: {}".format(jwk_href))

        if "application/json" in jwk_resp.headers['content-type']:
            try:
                jwks = jwk_resp.json()
                if "keys" in jwks:
                    jwks_keys = jwks["keys"]
                else:
                    jwks_keys = jwks
                return jwks_keys
            except Exception as e:
                logger.writeError("Error: {}. JWK endpoint contains: {}".format(str(e), jwk_resp.text))
                raise
        else:
            logger.writeError("Incorrect Content-Type. Expected 'application/json but got {}".format(
                jwk_resp.headers['content-type']))
            raise ValueError

    def getCertFromFile(self, file_path):
        try:
            if path.exists(file_path):
                with open(file_path, 'r') as myfile:
                    cert = myfile.read()
                    return cert
        except OSError:
            logger.writeError("File {} does not exist or you do not have permission to open it".format(
                file_path))
            raise

    def getPublicKeyString(self, key_class):
        # authlib v0.15 changes the return value of jwk.loads()
        if hasattr(key_class, "get_public_key"):
            key_class = key_class.get_public_key()

        serialised_key = key_class.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return serialised_key.decode('utf-8')

    def findMostRecentJWK(self, jwks):
        """Finds the JWK with the most recent timestamp inside the 'kid' property"""
        try:
            newest_key = reduce(
                lambda a, b: a if int(a["kid"].lstrip("x-nmos-")) > int(b["kid"].lstrip("x-nmos-")) else b, jwks)
            return newest_key
        except KeyError as e:
            logger.writeError("JSON Web Key 'kid' parameter is missing or malformed. {}".format(e))
            raise

    def extractPublicKey(self, key_containing_object):
        """Extracts a key from the given parameter. A list or a dict object will be treated as a JWK or JWKS structure.
        A string will be treated like a X509 certificate"""
        try:
            if isinstance(key_containing_object, dict):
                pub_key = jwk.loads(key_containing_object)
            elif isinstance(key_containing_object, list):
                newest_key = self.findMostRecentJWK(key_containing_object)
                pub_key = jwk.loads(newest_key)
            elif isinstance(key_containing_object, str):
                key_containing_object = key_containing_object.encode()
                crt_obj = x509.load_pem_x509_certificate(key_containing_object, default_backend())
                pub_key = crt_obj.public_key()
            pubkey_string = self.getPublicKeyString(pub_key)
            if pubkey_string is None:
                logger.writeError("Public Key could not be extracted from certificate")
            else:
                return pubkey_string
        except Exception as e:
            logger.writeError("Public Key(s) could not be extracted from JSON Web Keys. {}".format(e))
            raise

    def getPublicKey(self):
        if self.public_key is None or self.key_last_refreshed + self.refresh_key_interval < time():
            try:
                logger.writeInfo("Fetching JSON Web Keys using DNS Service Discovery")
                jwks = self.get_jwks()
                public_key = self.extractPublicKey(jwks)
            except RequestException as e:
                logger.writeError("Error: {0!s}. Trying to fetch certificate from file".format(e))
                cert = self.getCertFromFile(CERT_FILE_PATH)
                public_key = self.extractPublicKey(cert)
            self.update_public_key(public_key)
        return self.public_key

    def processAccessToken(self, auth_string):
        # Auth string is of type 'Bearer xAgy65..'
        if auth_string.find(' ') > -1:
            token_type, token_string = auth_string.split(None, 1)
            if token_type.lower() != "bearer":
                raise UnsupportedTokenTypeError()
        # Otherwise string is access token 'xAgy65..'
        else:
            token_string = auth_string
        if token_string == "null" or token_string == "":
            raise MissingAuthorizationError()
        pubKey = self.getPublicKey()
        claims_options = generate_claims_options(self.api_name)
        claims = jwt.decode(s=token_string, key=pubKey,
                            claims_cls=JWTClaimsValidator,
                            claims_options=claims_options,
                            claims_params=None)
        claims.validate(req=None)  # Request=None as Flask request proxy object used instead

    def handleHttpAuth(self):
        """Handle bearer token string ("Bearer xAgy65...") in "Authorzation" Request Header"""
        auth_string = request.headers.get('Authorization', None)
        if auth_string is None:
            raise MissingAuthorizationError()
        self.processAccessToken(auth_string)

    def handleSocketAuth(self, *args, **kwargs):
        """Handle bearer token string ("access_token=xAgy65...") in Websocket URL Query Param"""
        ws = args[0]
        environment = ws.environ
        auth_header = environment.get('HTTP_AUTHORIZATION', None)
        if auth_header is not None:
            logger.writeInfo("auth header string is {}".format(auth_header))
            auth_string = auth_header
            self.processAccessToken(auth_string)
        else:
            logger.writeWarning("Websocket does not have auth header, looking in query string..")
            query_string = environment.get('QUERY_STRING', None)
            try:
                if query_string is not None:
                    auth_string = parse_qs(query_string)['access_token'][0]
                    self.processAccessToken(auth_string)
                else:
                    raise MissingAuthorizationError
            except (AuthlibBaseError, KeyError):
                err = {"type": "error", "data": "Socket Authentication Error"}
                ws.send(json.dumps(err))
                logger.writeError("""
                    'access_token' URL param doesn't exist. Websocket authentication failed.
                """)
                raise

    def JWTRequired(self):
        def JWTDecorator(func):
            @wraps(func)
            def processAccessToken(*args, **kwargs):
                # Check to see if request is a Websocket upgrade, else treat request as a standard HTTP request
                headers = request.headers
                if ('Upgrade' in headers.keys() and headers['Upgrade'].lower() == 'websocket'):
                    logger.writeInfo("Using Socket handler")
                    self.handleSocketAuth(*args, **kwargs)
                else:
                    logger.writeInfo("Using HTTP handler")
                    self.handleHttpAuth()
                return func(*args, **kwargs)
            return processAccessToken
        return JWTDecorator

    def __call__(self, func):
        if not self.condition:
            # Return the function unchanged, not decorated.
            return func

        # Return decorated function
        decorator = self.JWTRequired()
        return decorator(func)
