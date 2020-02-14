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

from re import compile
from six import string_types
from flask import request, abort
from socket import getfqdn
from fnmatch import fnmatch
from authlib.jose import JWTClaims
from authlib.jose.errors import InvalidClaimError, MissingClaimError

from ..logger import Logger as defaultLogger

logger = defaultLogger("authresource")


def generate_claims_options(nmos_api):
    claims_options = {
        "iss": {"essential": True},
        "sub": {"essential": True},
        "aud": {"essential": True},
        "exp": {"essential": True},
        "iat": {"essential": False},
        "nbf": {"essential": False},
        "client_id": {"essential": True},
        "scope": {"essential": False},
        "x-nmos-api": {
            "essential": True,
        }
    }
    if nmos_api and isinstance(nmos_api, str):
        claims_options["x-nmos-api"]["value"] = nmos_api
    elif nmos_api and isinstance(nmos_api, list):
        claims_options["x-nmos-api"]["values"] = nmos_api
    return claims_options


class JWTClaimsValidator(JWTClaims):

    def __init__(self, payload, header, options=None, params=None):
        super(JWTClaimsValidator, self).__init__(payload, header, options, params)

    def validate_iss(self):  # placeholder
        super(JWTClaimsValidator, self).validate_iss()

    def validate_sub(self):  # placeholder
        super(JWTClaimsValidator, self).validate_sub()

    def validate_aud(self):  # placeholder
        super(JWTClaimsValidator, self).validate_aud()
        claim_name = "aud"
        fqdn = getfqdn()  # Fully qualified domain name of Resource Server
        actual_claim_value = self.get(claim_name)  # actual claim value in JWT
        if isinstance(actual_claim_value, string_types):
            actual_claim_value = [actual_claim_value]

        for aud in actual_claim_value:
            if fnmatch(fqdn, aud):
                return True
        raise InvalidClaimError(
            "Hostname '{}' does not match aud claim value of '{}'.".format(fqdn, actual_claim_value))

    def validate_nmos(self):
        claim_name = "x-nmos-api"
        actual_claim_value = self.get(claim_name)  # actual claim value in JWT
        valid_claim_option = self.options.get(claim_name)  # from `claim_options.py`

        if not actual_claim_value:  # Missing x-nmos-api claim
            raise MissingClaimError(claim_name)
        if not valid_claim_option:  # No options given for validation
            return

        def _validate_permissions_object(valid_api_value):
            access_permission_object = actual_claim_value.get(valid_api_value)
            if not access_permission_object:
                raise InvalidClaimError("{}. No entry in claim for '{}'.".format(claim_name, valid_api_value))

            if request.method in ["GET", "OPTIONS", "HEAD"]:
                access_right = "read"
            elif request.method in ["PUT", "POST", "PATCH", "DELETE"]:
                access_right = "write"
            else:
                abort(405)
            url_access_list = access_permission_object.get(access_right)
            if not url_access_list:
                raise InvalidClaimError(
                    "{}. No entry in permissions object for '{}'.".format(claim_name, access_right))

            pattern = compile(r'/x-nmos/[a-z]+/v[0-9]+\.[0-9]+/(.*)')  # Capture path after namespace
            trimmed_path = pattern.match(request.path).group(1)
            for wildcard_url in url_access_list:
                if fnmatch(trimmed_path, wildcard_url):
                    return True

            raise InvalidClaimError("{}. No matching paths in access list for '{}'.".format(claim_name, trimmed_path))

        # Single x-nmos-api value present in claims options (e.g. query)
        valid_api_value = valid_claim_option.get('value')
        if valid_api_value:
            if valid_api_value not in actual_claim_value.keys():
                raise InvalidClaimError("{}. No entry in claim for '{}'.".format(claim_name, valid_api_value))
            _validate_permissions_object(valid_api_value)

        # Multiple x-nmos-api values present in claims options (e.g. [query, registration])
        valid_api_values = valid_claim_option.get('values')
        if valid_api_values:
            if not any(api_name in actual_claim_value.keys() for api_name in valid_api_values):
                raise InvalidClaimError("{}. No entry in claim for one of '{}'.".format(claim_name, valid_api_value))
            shared_keys = list(set(actual_claim_value.keys()) & set(valid_api_values))  # Find shared keys
            for valid_api_value in shared_keys:
                _validate_permissions_object(valid_api_value)

        if not valid_api_value and not valid_api_values:
            logger.writeWarning("No x-nmos-api claim value in claims options")

    def validate(self, now=None, leeway=0):
        super(JWTClaimsValidator, self).validate()
        self.validate_nmos()
