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
from flask import request
from OpenSSL import crypto
from six.moves.urllib.parse import urljoin, parse_qs
from requests.exceptions import RequestException

from nmoscommon.mdnsbridge import IppmDNSBridge
from nmoscommon.nmoscommonconfig import config as _config
from nmoscommon.logger import Logger as defaultLogger
from authlib.jose import jwt
from authlib.oauth2.rfc6749.errors import MissingAuthorizationError, \
    UnsupportedTokenTypeError
from authlib.common.errors import AuthlibBaseError

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
CERT_ENDPOINT = 'certs'
CERT_URL_PATH = '/{}/{}/{}/{}'.format(APINAMESPACE, APINAME, APIVERSION, CERT_ENDPOINT)


class RequiresAuth(object):

    def __init__(self, condition=OAUTH_MODE, claimsOptions=IS_XX_CLAIMS,
                 certificate=None):
        self.condition = condition
        self.claimsOptions = claimsOptions
        self.certificate = certificate
        self.bridge = IppmDNSBridge()
        self.logger = defaultLogger("authresource")

    def getHrefFromService(self, serviceType):
        return self.bridge.getHref(serviceType)

    def getCertFromEndpoint(self):
        try:
            href = self.getHrefFromService(MDNS_SERVICE_TYPE)
            certHref = urljoin(href, CERT_URL_PATH)
            self.logger.writeInfo('cert href is: {}'.format(certHref))
            cert_resp = requests.get(certHref, timeout=0.5, proxies={'http': ''})
            cert_resp.raise_for_status()  # Raise error if status !=200
        except RequestException as e:
            self.logger.writeError("Error: {0!s}".format(e))
            self.logger.writeError("Cannot find certificate at {}. Is the Auth Server Running?".format(certHref))
            raise

        contentType = cert_resp.headers['content-type'].split(";")[0]
        if contentType == "application/json":
            cert = cert_resp.json()
            try:
                if len(cert) > 1:
                    self.logger.writeWarning("Multiple certificates at Endpoint. Returning First Instance.")
                cert = cert[0]
                return cert
            except Exception as e:
                self.logger.writeError("Error: {}. Endpoint contains: {}".format(str(e), cert))
                raise
        else:
            self.logger.writeError("Incorrect Content-Type. Expected 'application/json but got {}".format(contentType))
            raise ValueError

    def getCertFromFile(self, filename):
        try:
            if filename is not None:
                with open(filename, 'r') as myfile:
                    cert_data = myfile.read()
                    self.certificate = cert_data
                    return cert_data
        except OSError:
            self.logger.writeError("File does not exist or you do not have permission to open it")
            raise

    def extractPublicKey(self, certificate):
        crtObj = crypto.load_certificate(crypto.FILETYPE_PEM, certificate)
        pubKeyObject = crtObj.get_pubkey()
        pubKeyString = crypto.dump_publickey(crypto.FILETYPE_PEM, pubKeyObject)
        if pubKeyString is None:
            self.logger.writeError("Public Key could not be extracted from certificate")
            raise ValueError
        else:
            return pubKeyString.decode('utf-8')

    def getPublicKey(self):
        if self.certificate is None:
            self.logger.writeInfo("Fetching Certificate...")
            try:
                self.logger.writeInfo("Trying to fetch cert using mDNS...")
                cert = self.getCertFromEndpoint()
            except Exception as e:
                self.logger.writeError("Error: {0!s}. Trying to fetch Cert From File...".format(e))
                cert = self.getCertFromFile(CERT_FILE_PATH)
            self.certificate = cert
        pubKey = self.extractPublicKey(self.certificate)
        return pubKey

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
        else:
            self.logger.writeWarning("Websocket does not have auth header, looking in query string..")
            query_string = environment.get('QUERY_STRING', None)
            try:
                if query_string is not None:
                    try:
                        auth_string = parse_qs(query_string)['access_token'][0]
                    except KeyError:
                        self.logger.writeError("""
                            'access_token' URL param doesn't exist. Websocket authentication failed.
                        """)
                        raise MissingAuthorizationError()
                self.processAccessToken(auth_string)
            except AuthlibBaseError:
                err = {"type": "error", "data": "Socket Authentication Error"}
                ws.send(json.dumps(err))
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
