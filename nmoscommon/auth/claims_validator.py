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
from flask import request
from fnmatch import fnmatch
from authlib.jose import JWTClaims
from authlib.jose.errors import InvalidClaimError, MissingClaimError


class JWTClaimsValidator(JWTClaims):

    def __init__(self, payload, header, options=None, params=None):
        super(JWTClaimsValidator, self).__init__(payload, header, options, params)

    def validate_iss(self):  # placeholder
        super(JWTClaimsValidator, self).validate_iss()

    def validate_sub(self):  # placeholder
        super(JWTClaimsValidator, self).validate_sub()

    def validate_aud(self):  # placeholder
        super(JWTClaimsValidator, self).validate_aud()

    def validate_nmos(self):
        claim_name = "x-nmos-api"
        actual_claim_value = self.get(claim_name)  # actual claim value in JWT
        valid_claim_option = self.options.get(claim_name)  # from `claim_options.py`

        if not actual_claim_value:  # Missing x-nmos-api claim
            raise MissingClaimError(claim_name)
        if not valid_claim_option:  # No options given for validation
            return

        valid_api_value = valid_claim_option.get('value')
        if valid_api_value and valid_api_value not in actual_claim_value.keys():
            raise InvalidClaimError(claim_name)

        valid_api_values = valid_claim_option.get('values')
        if valid_api_values and not any(api_name in actual_claim_value.keys() for api_name in valid_api_values):
            raise InvalidClaimError(claim_name)

        if not valid_api_value and valid_api_values:
            # Multiple existing values should only occur in testing scenarios
            shared_keys = list(set(actual_claim_value.keys()) & set(valid_api_values))  # Find shared keys
            valid_api_value = shared_keys[0]  # Select first one to validate against

        access_permission_object = actual_claim_value.get(valid_api_value)
        if not access_permission_object:
            raise InvalidClaimError(claim_name)

        if request.method in ["GET", "OPTIONS", "HEAD"]:
            access_right = "read"
        else:
            access_right = "write"
        url_access_list = access_permission_object.get(access_right)
        if not url_access_list:
            raise InvalidClaimError(claim_name)

        pattern = compile(r'/x-nmos/[a-zA-Z]+/v[0-9]\.[0-9]/(.*)')  # Capture path after namespace
        trimmed_path = pattern.match(request.path).group(1)

        for wildcard_url in url_access_list:
            if fnmatch(trimmed_path, wildcard_url):
                return True

        raise InvalidClaimError(claim_name)

    def validate(self, now=None, leeway=0):
        super(JWTClaimsValidator, self).validate()
        self.validate_nmos()
