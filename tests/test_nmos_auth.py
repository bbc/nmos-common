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

from __future__ import print_function
from __future__ import absolute_import
import unittest
import mock
import json
import requests

from requests.exceptions import HTTPError
from authlib.specs.rfc6749.errors import UnsupportedTokenTypeError, MissingAuthorizationError
from authlib.specs.rfc7519.errors import InvalidClaimError
from nmoscommon.auth.nmos_auth import RequiresAuth
from nmoscommon.auth.claims_options import IS_04_REG_CLAIMS, IS_05_CLAIMS
from nmos_auth_data import BEARER_TOKEN, TEST_JWK, TEST_JWKS, PUB_KEY


class TestRequiresAuth(unittest.TestCase):

    def setUp(self):
        self.security = RequiresAuth(condition=True)

    def dummy(self):
        return "SUCCESS"

    @mock.patch.object(RequiresAuth, "JWTRequired")
    def testCondition(self, mockJWTRequired):
        self.security = RequiresAuth(condition=False)
        self.security(self.dummy)
        mockJWTRequired.assert_not_called()

        self.security = RequiresAuth(condition=True)
        self.security(self.dummy)
        mockJWTRequired.assert_called_once_with()

    @mock.patch("nmoscommon.auth.nmos_auth.request")
    def testJWTRequiredWithBadRequest(self, mockRequest):
        mockRequest.headers.get.return_value = None
        self.assertRaises(MissingAuthorizationError, self.security(self.dummy))

        mockRequest.headers.get.return_value = "barer " + BEARER_TOKEN["access_token"]
        self.assertRaises(UnsupportedTokenTypeError, self.security(self.dummy))

        mockRequest.headers.get.return_value = "Bearer null"
        self.assertRaises(MissingAuthorizationError, self.security(self.dummy))

    def mockGetResponse(self, code, content, headers, mockObject, method):
        resp = requests.Response()
        resp.status_code = code
        resp._content = json.dumps(content).encode('utf-8')
        resp.headers = headers
        mockObject.get.return_value = resp
        res = eval("self.security.{}()".format(method))
        return res

    @mock.patch.object(RequiresAuth, "getHrefFromService")
    @mock.patch("nmoscommon.auth.nmos_auth.requests")
    def testgetJwksFromEndpointWithJWK(self, mockRequests, mockGetHref):

        mockGetHref.return_value = "http://172.29.80.117:4999"

        jwk_resp = self.mockGetResponse(
            code=200,
            content=TEST_JWK,
            headers={'content-type': 'application/json'},
            mockObject=mockRequests,
            method="getJwksFromEndpoint"
        )

        self.assertTrue(isinstance(jwk_resp, dict))
        self.assertEqual(jwk_resp, TEST_JWK)
        self.assertRaises(HTTPError, self.mockGetResponse,
                          code=400,
                          content=TEST_JWK,
                          headers={'content-type': 'application/json'},
                          mockObject=mockRequests,
                          method="getJwksFromEndpoint"
                          )
        self.assertRaises(ValueError, self.mockGetResponse,
                          code=200,
                          content=TEST_JWK,
                          headers={'content-type': 'application/text'},
                          mockObject=mockRequests,
                          method="getJwksFromEndpoint"
                          )

    @mock.patch.object(RequiresAuth, "getHrefFromService")
    @mock.patch("nmoscommon.auth.nmos_auth.requests")
    def testgetJwksFromEndpointWithJWKS(self, mockRequests, mockGetHref):

        mockGetHref.return_value = "http://172.29.80.117:4999"
        jwks_resp = self.mockGetResponse(
            code=200,
            content=TEST_JWKS,
            headers={'content-type': 'application/json'},
            mockObject=mockRequests,
            method="getJwksFromEndpoint"
        )
        self.assertTrue(isinstance(jwks_resp, list))
        self.assertEqual(jwks_resp, TEST_JWKS['keys'])

    def testExtractPublicKeyWithJWK(self):
        self.assertRaises(Exception, self.security.extractPublicKey, "")
        self.assertEqual(self.security.extractPublicKey(TEST_JWK), PUB_KEY)

    def testExtractPublicKeyWithJWKS(self):
        self.assertRaises(Exception, self.security.extractPublicKey, "")
        self.assertEqual(self.security.extractPublicKey(TEST_JWKS["keys"][0]), PUB_KEY)

    @mock.patch.object(RequiresAuth, "getJwksFromEndpoint")
    @mock.patch("nmoscommon.auth.nmos_auth.request")
    def testJWTClaimsValidator(self, mockRequest, mockGetJwk):
        mockRequest.headers.get.return_value = "Bearer " + BEARER_TOKEN["access_token"]
        mockGetJwk.return_value = TEST_JWK

        self.security = RequiresAuth(condition=True, claimsOptions=IS_05_CLAIMS)
        self.assertRaises(InvalidClaimError, self.security(self.dummy))

        self.security = RequiresAuth(condition=True, claimsOptions=IS_04_REG_CLAIMS)
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")

        # NOTE: Assumes Only Write Access is permitted
        IS_04_REG_CLAIMS["x-nmos-api"]["value"]["access"] = "read"
        self.security = RequiresAuth(condition=True, claimsOptions=IS_04_REG_CLAIMS)
        self.assertRaises(InvalidClaimError, self.security(self.dummy))


if __name__ == '__main__':
    unittest.main()
