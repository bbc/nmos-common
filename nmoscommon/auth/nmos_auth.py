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
from functools import wraps
from time import time
from flask import request
from functools import reduce
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
from ..logger import Logger as defaultLogger
from .claims_options import IS_XX_CLAIMS
from .claims_validator import JWTClaimsValidator

MDNS_SERVICE_TYPE = "nmos-auth"
OAUTH_MODE = _config.get('oauth_mode', True)

NMOSAUTH_DIR = path.abspath(path.join(sep, 'var', 'nmosauth'))
CERT_FILE = 'certificate.pem'
CERT_FILE_PATH = path.join(NMOSAUTH_DIR, CERT_FILE)

APINAMESPACE = "x-nmos"
APINAME = "auth"
APIVERSION = "v1.0"
JWK_ENDPOINT = 'jwks'
JWK_URL_PATH = '/{}/{}/{}/{}'.format(APINAMESPACE, APINAME, APIVERSION, JWK_ENDPOINT)

REFRESH_KEY_INTERVAL = 3600


class RequiresAuth(object):

    def __init__(self, condition=OAUTH_MODE, claimsOptions=IS_XX_CLAIMS):
        self.logger = defaultLogger("authresource")
        self.bridge = IppmDNSBridge()
        self.condition = condition
        self.claimsOptions = claimsOptions
        self.publicKey = None
        self.key_last_accessed_time = 0

    def getHrefFromService(self, serviceType):
        return self.bridge.getHref(serviceType)

    def getJwksFromEndpoint(self):
        try:
            href = self.getHrefFromService(MDNS_SERVICE_TYPE)
            jwk_href = urljoin(href, JWK_URL_PATH)
            self.logger.writeInfo('JWK endpoint is: {}'.format(jwk_href))
            jwk_resp = requests.get(jwk_href, timeout=0.5, proxies={'http': ''})
            jwk_resp.raise_for_status()  # Raise error if status !=200
        except RequestException as e:
            self.logger.writeError("Error: {0!s}".format(e))
            self.logger.writeError("Cannot find certificate at {}. Is the Auth Server Running?".format(jwk_href))
            raise

        if "application/json" in jwk_resp.headers['content-type']:
            try:
                jwks = jwk_resp.json()
                if "keys" in jwks:
                    jwks_keys = jwks["keys"]
                    self.logger.writeInfo("JSON Web Key Set located at /jwks endpoint.")
                else:
                    jwks_keys = jwks
                return jwks_keys
            except Exception as e:
                self.logger.writeError("Error: {}. JWK endpoint contains: {}".format(str(e), jwk_resp.text))
                raise
        else:
            self.logger.writeError("Incorrect Content-Type. Expected 'application/json but got {}".format(
                jwk_resp.headers['content-type']))
            raise ValueError

    def getCertFromFile(self, file_path):
        try:
            if path.exists(file_path):
                with open(file_path, 'r') as myfile:
                    cert = myfile.read()
                    return cert
        except OSError:
            self.logger.writeError("File {} does not exist or you do not have permission to open it".format(
                file_path))
            raise

    def getPublicKeyString(self, key_class):
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
            self.logger.writeError("Format of JSON Web Key 'kid' parameter is incorrect. {}".format(e))
            raise

    def extractPublicKey(self, key_containing_object):
        """Extracts a key from the given parameter. A list or a dict object will be treated as a JWK or JWKS structure.
        A string will be treated like a X509 certificate"""
        try:
            if isinstance(key_containing_object, dict):
                key_class = jwk.loads(key_containing_object)
            elif isinstance(key_containing_object, list):
                newest_key = self.findMostRecentJWK(key_containing_object)
                key_class = jwk.loads(newest_key)
            elif isinstance(key_containing_object, str):
                key_containing_object = key_containing_object.encode()
                crt_obj = x509.load_pem_x509_certificate(key_containing_object, default_backend())
                key_class = crt_obj.public_key()
            pubkey_string = self.getPublicKeyString(key_class)
            if pubkey_string is None:
                self.logger.writeError("Public Key could not be extracted from certificate")
            else:
                return pubkey_string
        except Exception as e:
            self.logger.writeError("Public Key(s) could not be extracted from JSON Web Keys. {}".format(e))
            raise

    def getPublicKey(self):
        if self.publicKey is None or self.key_last_accessed_time + REFRESH_KEY_INTERVAL < time():
            try:
                self.logger.writeInfo("Fetching JSON Web Keys using DNS Service Discovery")
                jwks = self.getJwksFromEndpoint()
                public_key = self.extractPublicKey(jwks)
            except Exception as e:
                self.logger.writeError("Error: {0!s}. Trying to fetch certificate from file".format(e))
                cert = self.getCertFromFile(CERT_FILE_PATH)
                public_key = self.extractPublicKey(cert)
            self.publicKey = public_key
            self.key_last_accessed_time = time()
        return self.publicKey

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
        claims = jwt.decode(s=token_string, key=pubKey,
                            claims_cls=JWTClaimsValidator,
                            claims_options=self.claimsOptions,
                            claims_params=None)
        claims.validate()

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
            self.logger.writeInfo("auth header string is {}".format(auth_header))
            auth_string = auth_header
            self.processAccessToken(auth_string)
        else:
            self.logger.writeWarning("Websocket does not have auth header, looking in query string..")
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
                self.logger.writeError("""
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
                    self.logger.writeInfo("Using Socket handler")
                    self.handleSocketAuth(*args, **kwargs)
                else:
                    self.logger.writeInfo("Using HTTP handler")
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
