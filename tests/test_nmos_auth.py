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
from werkzeug.exceptions import HTTPException
from authlib.oauth2.rfc6749.errors import UnsupportedTokenTypeError, MissingAuthorizationError
from authlib.jose.errors import InvalidClaimError, MissingClaimError
from nmoscommon.auth.nmos_auth import RequiresAuth, get_auth_server_url, get_auth_server_metadata

from nmos_auth_data import BEARER_TOKEN, TEST_JWK, TEST_JWKS, PUB_KEY, CERT


class TestRequiresAuth(unittest.TestCase):

    def setUp(self):
        self.security = RequiresAuth(condition=True)  # API Instance

    def dummy(self):
        return "SUCCESS"

    @mock.patch("nmoscommon.auth.nmos_auth._config")
    @mock.patch("nmoscommon.auth.nmos_auth.IppmDNSBridge")
    def test_get_auth_server_url(self, mock_bridge, mock_config):

        mock_config.get.return_value = {}
        mock_bridge.return_value.getHref.return_value = None
        self.assertEqual(get_auth_server_url(), None)

        mock_bridge.return_value.getHref.return_value = "http://example_service.com"
        url = get_auth_server_url()
        self.assertEqual(url, "http://example_service.com")

        mock_config.get.return_value = "http://another_service.com"
        url = get_auth_server_url()
        self.assertEqual(url, "http://another_service.com")

    @mock.patch("nmoscommon.auth.nmos_auth.requests")
    def test_get_auth_server_metadata(self, mock_requests):
        resp = requests.Response()
        resp.status_code = 400
        mock_requests.get.return_value = resp
        
        url = "http://auth_server.com"
        get_auth_server_metadata(url)

        mock_calls = [
             mock.call("{}/.well-known/oauth-authorization-server".format(url), proxies={'http': ''}, timeout=0.5),
             mock.call("{}/.well-known/openid-configuration".format(url), proxies={'http': ''}, timeout=0.5)
        ]
 
        mock_requests.get.assert_has_calls(mock_calls)

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

    @mock.patch.object(RequiresAuth, "_get_jwk_url")
    @mock.patch("nmoscommon.auth.nmos_auth.requests")
    def testgetJwksWithJWK(self, mockRequests, mockGetJWKUrl):

        mockGetJWKUrl.return_value = "http://172.29.80.117:4999"

        jwk_resp = self.mockGetResponse(
            code=200,
            content=TEST_JWK,
            headers={'content-type': 'application/json'},
            mockObject=mockRequests,
            method="get_jwks"
        )
        
        self.assertTrue(isinstance(jwk_resp, dict))
        self.assertEqual(jwk_resp, TEST_JWK)

        self.assertRaises(HTTPException, self.mockGetResponse,
                          code=500,
                          content=TEST_JWK,
                          headers={'content-type': 'application/json'},
                          mockObject=mockRequests,
                          method="get_jwks"
                          )

        self.assertRaises(ValueError, self.mockGetResponse,
                          code=200,
                          content=TEST_JWK,
                          headers={'content-type': 'application/text'},
                          mockObject=mockRequests,
                          method="get_jwks"
                          )

    @mock.patch.object(RequiresAuth, "_get_jwk_url")
    @mock.patch("nmoscommon.auth.nmos_auth.requests")
    def testgetJwksWithJWKS(self, mockRequests, mockGetJWKUrl):

        mockGetJWKUrl.return_value = "http://172.29.80.117:4999"
        jwks_resp = self.mockGetResponse(
            code=200,
            content=TEST_JWKS,
            headers={'content-type': 'application/json'},
            mockObject=mockRequests,
            method="get_jwks"
        )
        self.assertTrue(isinstance(jwks_resp, list))
        self.assertEqual(jwks_resp, TEST_JWKS['keys'])

    def testfindMostRecentJWK(self):
        self.assertEqual(self.security.findMostRecentJWK(TEST_JWKS["keys"]), TEST_JWKS["keys"][0])
        self.assertNotEqual(self.security.findMostRecentJWK(TEST_JWKS["keys"]), TEST_JWKS["keys"][1])

    def testExtractPublicKeyWithJWK(self):
        self.assertRaises(Exception, self.security.extractPublicKey, "")
        self.assertEqual(self.security.extractPublicKey(TEST_JWK), PUB_KEY)

    def testExtractPublicKeyWithJWKS(self):
        self.assertRaises(Exception, self.security.extractPublicKey, "")
        self.assertEqual(self.security.extractPublicKey(TEST_JWKS["keys"][0]), PUB_KEY)

    def testExtractPublicKeyWithCert(self):
        self.assertEqual(self.security.extractPublicKey(CERT), PUB_KEY)

    @mock.patch("nmoscommon.auth.claims_validator.flask_request")
    @mock.patch.object(RequiresAuth, "get_jwks")
    @mock.patch("nmoscommon.auth.nmos_auth.request")
    def testJWTClaimsValidator_x_nmos(self, mockRequest, mockGetJwk, mockValidatorRequest):
        mockRequest.headers.get.return_value = "Bearer " + BEARER_TOKEN["access_token"]
        mockGetJwk.return_value = TEST_JWK

        # Example Token:
        # {
        # "iss": "ap-z420-5.rd.bbc.co.uk",
        # "sub": "demo",
        # "nbf": 1581420052,
        # "exp": 2581420052,
        # "aud": "*.rd.bbc.co.uk",
        # "client_id": "my_client",
        # "x-nmos-connection": {
        #     "read": ["*"]
        # },
        # "x-nmos-registration": {
        #     "read": ["*"],
        #     "write": ["*"]
        # },
        # "scope": "connection registration",
        # "iat": 1581420052
        # }

        ############### READ REQUESTS ###################
        mockValidatorRequest.method = "GET"

        # Any api_name should be permitted for base resources, even when not included in token
        self.security = RequiresAuth(condition=True, api_name="query")
        mockValidatorRequest.path = "/"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos"

        # "query" should not pass as READ is not in token
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos/query/"
        self.assertRaises(MissingClaimError, self.security(self.dummy))
        mockValidatorRequest.path = "/x-nmos/query/v1.1/"
        self.assertRaises(MissingClaimError, self.security(self.dummy))
        mockValidatorRequest.path = "/x-nmos/query/v1.1/senders"
        self.assertRaises(MissingClaimError, self.security(self.dummy))

        # "registration" should pass as it allows READ in token
        self.security = RequiresAuth(condition=True, api_name="registration")
        mockValidatorRequest.path = "/x-nmos/registration/"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos/registration/v1.1/"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos/registration/v1.1/health"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")

        # "connection" should pass as it allows READ in token
        self.security = RequiresAuth(condition=True, api_name="connection")
        mockValidatorRequest.path = "/x-nmos/connection/"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos/connection/v1.1/"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos/connection/v1.1/senders"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")


        ############### WRITE REQUESTS ###################
        mockValidatorRequest.method = "POST"

        # "query" should fail as not included in token
        self.security = RequiresAuth(condition=True, api_name="query")
        mockValidatorRequest.path = "/x-nmos/query/"
        self.assertRaises(MissingClaimError, self.security(self.dummy))
        mockValidatorRequest.path = "/x-nmos/query/v1.1/"
        self.assertRaises(MissingClaimError, self.security(self.dummy))
        mockValidatorRequest.path = "/x-nmos/query/v1.1/senders"
        self.assertRaises(MissingClaimError, self.security(self.dummy))

        # "connection" doesn't allow WRITE in token
        self.security = RequiresAuth(condition=True, api_name="connection")
        mockValidatorRequest.path = "/x-nmos/connection/"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos/connection/v1.1/"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos/connection/v1.1/senders"
        self.assertRaises(InvalidClaimError, self.security(self.dummy))

        # "registration" allows WRITE in token
        self.security = RequiresAuth(condition=True, api_name="registration")
        mockValidatorRequest.path = "/x-nmos/registration/"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos/registration/v1.1/"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        mockValidatorRequest.path = "/x-nmos/registration/v1.1/health"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")

    @mock.patch("nmoscommon.auth.claims_validator.getfqdn")
    @mock.patch("nmoscommon.auth.claims_validator.flask_request")
    @mock.patch.object(RequiresAuth, "get_jwks")
    @mock.patch("nmoscommon.auth.nmos_auth.request")
    def testJWTClaimsValidator_aud(self, mockRequest, mockGetJwk, mockValidatorRequest, mockGetFQDN):
        mockRequest.headers.get.return_value = "Bearer " + BEARER_TOKEN["access_token"]
        mockGetJwk.return_value = TEST_JWK
        mockValidatorRequest.path = "/x-nmos/registration/v1.2/health/nodes"
        mockValidatorRequest.method = "GET"
        self.security = RequiresAuth(condition=True, api_name="registration")

        # Same hostname as auth server succeeds
        mockGetFQDN.return_value = "ap-z420-5.rd.bbc.co.uk"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        # Different hostname succeeds
        mockGetFQDN.return_value = "tony_has_massive_halls.rd.bbc.co.uk"
        self.assertEqual(self.security(self.dummy)(), "SUCCESS")
        # Missing sub-domain fails
        mockGetFQDN.return_value = "something.bbc.co.uk"
        self.assertRaises(InvalidClaimError, self.security(self.dummy))
        # Missing domain fails
        mockGetFQDN.return_value = "malicious-site.co.uk"
        self.assertRaises(InvalidClaimError, self.security(self.dummy))


if __name__ == '__main__':
    unittest.main()
