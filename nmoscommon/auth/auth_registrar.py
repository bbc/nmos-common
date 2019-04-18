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

import os
import json
import time
import jwt
import requests
from requests.exceptions import HTTPError
from six.moves.urllib.parse import urljoin

from ..mdnsbridge import IppmDNSBridge
from ..logger import Logger

NMOSOAUTH_DIR = '/var/nmosoauth'
CREDENTIALS_FILE = 'oauth_credentials.json'
CREDENTIALS_PATH = os.path.join(NMOSOAUTH_DIR, CREDENTIALS_FILE)

MDNS_SERVICE_TYPE = "nmos-auth"

API_NAMESPACE = 'x-nmos/auth/v1.0/'
REGISTRATION_ENDPOINT = API_NAMESPACE + 'register_client'
TOKEN_ENDPOINT = API_NAMESPACE + 'token'


def get_credentials_from_file(file):
    with open(CREDENTIALS_PATH, 'r') as f:
        credentials = json.load(f)
    client_id = credentials['client_id']
    client_secret = credentials['client_secret']
    return client_id, client_secret


class AuthRegistrar(object):
    def __init__(self, client_name, redirect_uri, client_uri=None,
                 allowed_scope=None, allowed_grant="authorization_code",
                 allowed_response="code", auth_method="client_secret_basic",
                 certificate=None, logger=None):
        self.client_name = client_name
        self.redirect_uri = redirect_uri
        self.client_uri = client_uri
        self.allowed_scope = allowed_scope
        self.allowed_grant = allowed_grant
        self.allowed_response = allowed_response
        self.auth_method = auth_method
        self.certificate = certificate  # Could be deployed centrally for an alternative trust mechanism

        self.client_id = None
        self.client_secret = None
        self.logger = Logger("auth_registrar", logger)
        self.bridge = IppmDNSBridge()
        self.initialised = self.initialise()

    def initialise(self):
        try:
            # Check if credentials file already exists i.e. device is already registered
            if os.path.isfile(CREDENTIALS_PATH):
                self.logger.writeWarning("Credentials file already exists. Using existing credentials.")
                self.client_id, self.client_secret = get_credentials_from_file(CREDENTIALS_PATH)
            else:
                self.logger.writeInfo("Registering with Authorization Server...")
                reg_resp_json = self.send_oauth_registration_request()
                self.write_credentials_to_file(reg_resp_json, CREDENTIALS_PATH)
            return True
        except Exception as e:
            self.logger.writeError("Unable to initialise OAuth Client with client credentials. {}".format(e))
            return False

    def write_credentials_to_file(self, data, file_path):
        self.client_id = data.get('client_id')
        self.client_secret = data.get('client_secret')
        credentials = {"client_id": self.client_id, "client_secret": self.client_secret}
        with open(file_path, 'w') as f:
            json.dump(credentials, f)
        os.chmod(file_path, 0o600)
        return True

    def send_oauth_registration_request(self):
        try:
            href = self.bridge.getHref(MDNS_SERVICE_TYPE)
            registration_href = urljoin(href, REGISTRATION_ENDPOINT)
            self.logger.writeDebug('Registration endpoint href is: {}'.format(registration_href))

            data = {
                    "client_name": self.client_name,
                    "client_uri": self.client_uri,
                    "scope": self.allowed_scope,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": self.allowed_grant,
                    "response_type": self.allowed_response,
                    "token_endpoint_auth_method": self.auth_method
                    }

            # Decide how Basic Auth details are retrieved - user input? Retrieved from file?
            reg_resp = requests.post(
                registration_href,
                data=data,
                auth=('dannym', 'password'),
                timeout=0.5,
                proxies={'http': ''}
            )
            reg_resp.raise_for_status()  # Raise error if status !=201
            return reg_resp.json()
        except HTTPError as e:
            self.logger.writeError("Unable to Register Client with Auth Server. {}".format(e))
            raise


class AuthRequestor(object):

    def __init__(self, auth_registrar=None, logger=None):
        self.auth_reg = auth_registrar
        self.bridge = IppmDNSBridge()
        self.logger = Logger("auth_requestor", logger)

    def token_request_password(self, username, password, scope):
        """Request Token using Password Grant"""
        return self.token_request(grant_type="password", username=username, password=password, scope=scope)

    def token_request_code(self, code, scope):
        """Request Token using Authorization Code Grant"""
        return self.token_request(grant_type="authorization_code", auth_code=code, scope=scope)

    def token_request(self, grant_type, username=None, password=None, auth_code=None, scope=None):
        """Determine data object to be sent in Token Request"""

        request_data = None

        if grant_type == "password" and username is not None and password is not None:
            request_data = {
                "grant_type": grant_type,
                "username": username,
                "password": password
            }
        elif grant_type == "authorization_code" and auth_code is not None:
            if self.auth_reg is not None:
                request_data = {
                    "grant_type": grant_type,
                    "code": auth_code,
                    "redirect_uri": self.auth_reg.redirect_uri,
                    "client_id": self.auth_reg.client_id
                }
            else:
                client_id, client_secret = get_credentials_from_file(CREDENTIALS_PATH)
                request_data = {
                    "grant_type": grant_type,
                    "code": auth_code,
                    "redirect_uri": None,
                    "client_id": client_id
                }
        if request_data is None:
            raise Exception("Invalid Credentials for the supplied Grant Type")

        if scope is not None:
            request_data.update({'scope': scope})

        return self._auth_request(request_data)

    def validate_token_expiry(self, bearer_token):
        """Validate if access token has expired and, if so, remove"""
        if bearer_token is None:
            return False
        else:
            try:
                access_token = bearer_token.get('access_token')
                claims_dict = jwt.decode(access_token, verify=False)
                expiry_time = claims_dict['exp']
                current_time = int(time.time())
                if expiry_time > current_time:
                    return True
                else:
                    self.bearer_token = None
                    return False
            except Exception as e:
                self.logger.writeError("Exception reading Token Expiry: {}. Removing Token.".format(e))
                return False

    def _auth_request(self, data):
        """Function for Requesting Bearer Token form Auth Server"""
        try:
            href = self.bridge.getHref(MDNS_SERVICE_TYPE)
            if href == '':
                raise ValueError("No Services Found of type {}".format(MDNS_SERVICE_TYPE))
            token_href = urljoin(href, TOKEN_ENDPOINT)
            client_id, client_secret = get_credentials_from_file(CREDENTIALS_PATH)

            # self.logger.writeDebug('Data is: {}. HREF is: {}. ID is: {}. Secret is: {}'.format(
            #     data, token_href, client_id, client_secret
            # ))  # Only for Testing

            bearer_token_req = requests.post(
                token_href,
                data=data,
                auth=(client_id, client_secret),
                timeout=0.5,
                proxies={'http': ''}
            )
            bearer_token_req.raise_for_status()
            self.logger.writeInfo("Bearer Token Request Successful")
            return bearer_token_req.json()
        except Exception as e:
            self.logger.writeError("Bearer Token Request Failed. {}".format(e))
            return False


if __name__ == "__main__":  # pragma: no cover
    auth_reg = AuthRegistrar(
        client_name="test_oauth_client",
        client_uri="www.example.com",
        allowed_scope="is04",
        redirect_uri="www.app.example.com",
        allowed_grant="password\nauthorization_code",  # Authlib only accepts grants seperated with newline chars
        allowed_response="code",
        auth_method="client_secret_basic",
        certificate=None
    )
    if auth_reg.initialised is True:
        auth_req = AuthRequestor(auth_reg)
        token = auth_req.token_request_password(username='dannym', password='password', scope='is04')
        print('Access Token is: {}'.format(token['access_token']))
