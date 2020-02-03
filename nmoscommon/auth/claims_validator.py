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
        valid_claim_option = self.options.get(claim_name)
        valid_api_value = valid_claim_option.get('value')

        actual_claim_value = self.get(claim_name)
        if not actual_claim_value:
            raise MissingClaimError(claim_name)
        if not valid_api_value:
            return

        if valid_api_value not in actual_claim_value.keys():
            raise InvalidClaimError(claim_name)

        access_permission_object = actual_claim_value[valid_api_value]
        if not access_permission_object:
            raise InvalidClaimError(claim_name)

        if request.method in ["GET", "OPTIONS", "HEAD"]:
            access_right = "read"
        else:
            access_right = "write"
        url_access_list = access_permission_object.get(access_right)
        if not url_access_list:
            raise InvalidClaimError(claim_name)

        request_path = request.path

        # Replace with regex - re.sub()
        path_dot_notation = request_path.replace('/', '.').lstrip('x-nmos.').lstrip(valid_api_value).lstrip('v.0123')

        for wilcard_url in url_access_list:
            if fnmatch(path_dot_notation, wilcard_url):
                return True

        raise InvalidClaimError

    def validate(self, now=None, leeway=0):
        super(JWTClaimsValidator, self).validate()
        self.validate_nmos()
