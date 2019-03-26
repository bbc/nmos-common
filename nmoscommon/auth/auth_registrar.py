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
import requests
from requests.exceptions import HTTPError
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

from ..mdnsbridge import IppmDNSBridge

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
                 certificate=None):
        self.client_name = client_name
        self.redirect_uri = redirect_uri
        self.client_uri = client_uri
        self.allowed_scope = allowed_scope
        self.allowed_grant = allowed_grant
        self.allowed_response = allowed_response
        self.auth_method = auth_method
        self.certificate = certificate  # Could be deployed centrally for an alternative trust mechanism

        self.bridge = IppmDNSBridge()
        self.initialised = self.initialise()
        self.client_id = None
        self.client_secret = None

    def write_credentials_to_file(self, data, file_path):
        self.client_id = data.get('client_id')
        self.client_secret = data.get('client_secret')
        credentials = {"client_id": self.client_id, "client_secret": self.client_secret}
        with open(file_path, 'w') as f:
            json.dump(credentials, f)
        return True

    def send_registration_request(self):
        try:
            href = self.bridge.getHref(MDNS_SERVICE_TYPE)
            registration_href = urljoin(href, REGISTRATION_ENDPOINT)
            print('Registration endpoint href is: {}'.format(registration_href))

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
            reg_resp = requests.post(registration_href,
                                     data=data,
                                     auth=('dannym', 'password'),
                                     timeout=0.5,
                                     proxies={'http': ''}
                                     )
            reg_resp.raise_for_status()  # Raise error if status !=201
            return reg_resp.json()
        except HTTPError as e:
            print("Unable to Register Client with Auth Server. {}".format(e))

    def initialise(self):
        try:
            # Check if credentials file already exists i.e. device is already registered
            if os.path.isfile(CREDENTIALS_PATH):
                print("Credentials file already exists. Using existing credentials.")
                self.client_id, self.client_secret = get_credentials_from_file(CREDENTIALS_PATH)
            else:
                print("Registering with Authorization Server...")
                reg_resp_json = self.send_registration_request()
                self.write_credentials_to_file(reg_resp_json, CREDENTIALS_PATH)
            return True
        except Exception as e:
            print("Unable to initialise OAuth Client with client credentials. {}".format(e))
            return False


class AuthRequestor(object):

    def __init__(self, auth_registrar=None):
        self.auth_reg = auth_registrar
        self.bridge = IppmDNSBridge()

    def _auth_request(self, data):
        try:
            href = self.bridge.getHref(MDNS_SERVICE_TYPE)
            if href == '':
                raise ValueError("No Services Found of type {}".format(MDNS_SERVICE_TYPE))
            token_href = urljoin(href, TOKEN_ENDPOINT)
            client_id, client_secret = get_credentials_from_file(CREDENTIALS_PATH)

            # print('Data is: {}. HREF is: {}. ID is: {}. Secret is: {}'.format(
            #     data, token_href, client_id, client_secret
            # ))  # Only for Testing

            token_req = requests.post(token_href,
                                      data=data,
                                      auth=(client_id, client_secret),
                                      timeout=0.5,
                                      proxies={'http': ''})
            token_req.raise_for_status()
            print("Token Request Successful")
            return token_req.json()
        except Exception as e:
            print("Bearer Token Request Failed. {}".format(e))
            return False

    def token_request_password(self, username, password, scope):
        return self.token_request(grant_type="password", username=username, password=password, scope=scope)

    def token_request_code(self, code, scope):
        return self.token_request(grant_type="authorization_code", auth_code=code, scope=scope)

    def token_request(self, grant_type, username=None, password=None, auth_code=None, scope=None):
        data = None

        if grant_type == "password" and username is not None and password is not None:
            data = {
                    "grant_type": grant_type,
                    "username": username,
                    "password": password
            }
        elif grant_type == "authorization_code" and auth_code is not None:
            if self.auth_reg is not None:
                data = {
                    "grant_type": grant_type,
                    "code": auth_code,
                    "redirect_uri": self.auth_reg.redirect_uri,
                    "client_id": self.auth_reg.client_id
                }
            else:
                client_id, client_secret = get_credentials_from_file(CREDENTIALS_PATH)
                data = {
                    "grant_type": grant_type,
                    "code": auth_code,
                    "redirect_uri": None,
                    "client_id": client_id
                }
        if data is None:
            raise Exception("Invalid Credentials for the supplied Grant Type")

        if scope is not None:
            data.update({'scope': scope})

        return self._auth_request(data)


if __name__ == "__main__":  # pragma: no cover
    auth_reg = AuthRegistrar(
        client_name="test_oauth_client",
        client_uri="www.example.com",
        allowed_scope="is04",
        redirect_uri="www.app.example.com",
        allowed_grant="password\nauthorization_code",  # Authlib only seems to accept grants seperated with newline chars
        allowed_response="code",
        auth_method="client_secret_basic",
        certificate=None
    )
    if auth_reg.initialised is True:
        auth_req = AuthRequestor(auth_reg)
        token = auth_req.token_request_password(username='dannym', password='password', scope='is04')
        print('Access Token is: {}'.format(token['access_token']))
