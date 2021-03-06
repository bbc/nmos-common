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

from flask import Flask
from requests.exceptions import HTTPError
from werkzeug.exceptions import HTTPException
from authlib.oauth2.rfc6749.errors import UnsupportedTokenTypeError, MissingAuthorizationError
from authlib.jose.errors import InvalidClaimError, MissingClaimError
from nmoscommon.auth.auth_middleware import AuthMiddleware, get_auth_server_url, get_auth_server_metadata

from nmos_auth_data import BEARER_TOKEN, TEST_JWK, TEST_JWKS, PUB_KEY, CERT


class TestAuthMiddleware(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)  # create test Flask instance
        self.base_wsgi_app = self.app.wsgi_app  # cached to re-apply middleware with different params
        # apply middleware to app and give alias
        self.app.wsgi_app = self.middleware = AuthMiddleware(self.app.wsgi_app, auth_mode=True)
        self.client = self.app.test_client()
        self.create_dummy_routes()  # add test routes to dummy Flask instance

    def tearDown(self):
        AuthMiddleware.public_key = None

    def create_dummy_routes(self):
        self.app.route('/')(self.dummy)
        self.app.route('/x-nmos/')(self.dummy)
        self.app.route('/x-nmos/registration/')(self.dummy)
        self.app.route('/x-nmos/registration/v1.1/')(self.dummy)
        self.app.route('/x-nmos/registration/v1.1/health/')(self.dummy)
        self.app.route('/x-nmos/query/')(self.dummy)
        self.app.route('/x-nmos/query/v1.1/')(self.dummy)
        self.app.route('/x-nmos/query/v1.1/senders')(self.dummy)
        self.app.route('/x-nmos/connection/')(self.dummy)
        self.app.route('/x-nmos/connection/v1.1/')(self.dummy)
        self.app.route('/x-nmos/connection/v1.1/senders')(self.dummy)

    def dummy(self):
        return "SUCCESS"

    @mock.patch("nmoscommon.auth.auth_middleware._config")
    @mock.patch("nmoscommon.auth.auth_middleware.IppmDNSBridge")
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

    @mock.patch("nmoscommon.auth.auth_middleware.requests")
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

    def test_base_resources(self):

        # SHOULD ALWAYS RETURN 200
        res = self.client.get('/')
        self.assertEqual(res.data.decode(), "SUCCESS")
        # SHOULD ALWAYS RETURN 200
        res = self.client.get('/x-nmos/')
        self.assertEqual(res.data.decode(), "SUCCESS")
        # SHOULD ALWAYS RETURN 401 DUE TO MISSING AUTH
        res = self.client.get('/x-nmos/query/')
        self.assertEqual(401, res.status_code)

    def test_mode(self):

        # SHOULD PASS WHEN AUTH IS SWITCHED OFF
        self.app.wsgi_app = AuthMiddleware(self.base_wsgi_app, auth_mode=False)
        res = self.client.get('/x-nmos/query/')
        self.assertEqual(200, res.status_code)
        res = self.client.get('/x-nmos/query/v1.1/')
        self.assertEqual(200, res.status_code)
        res = self.client.get('/x-nmos/query/v1.1/senders')
        self.assertEqual(200, res.status_code)
        # SHOULD RETURN 401 WHEN AUTH TURNED BACK ON
        self.app.wsgi_app = AuthMiddleware(self.base_wsgi_app, auth_mode=True)
        res = self.client.get('/x-nmos/query/')
        self.assertEqual(401, res.status_code)
        res = self.client.get('/x-nmos/query/v1.1/')
        self.assertEqual(401, res.status_code)
        res = self.client.get('/x-nmos/query/v1.1/senders')
        self.assertEqual(401, res.status_code)

    def test_api_calls(self):
        mock_headers = {"Authorization": "Bearer " + BEARER_TOKEN["access_token"]}

        with mock.patch.object(AuthMiddleware, "get_jwks") as mock_get_jwks:
            mock_get_jwks.return_value = TEST_JWK

            # Check that a base request with no api_name succeeds
            res = self.client.get('/x-nmos/', headers=mock_headers)
            self.assertEqual(200, res.status_code)

            # Check that a base request with missing x-nmos claim fails
            self.app.wsgi_app = AuthMiddleware(self.base_wsgi_app, auth_mode=True, api_name="query")
            res = self.client.get('/x-nmos/query/', headers=mock_headers)
            self.assertEqual(400, res.status_code)
            self.assertIn("missing_claim", res.json["error"])

            # Check that a request to an endpoint not specified in constructor parameters fails
            self.app.wsgi_app = AuthMiddleware(self.base_wsgi_app, auth_mode=True, api_name="query")
            res = self.client.get('/x-nmos/registration/', headers=mock_headers)
            self.assertEqual(400, res.status_code)
            self.assertIn("missing_claim", res.json["error"])

            # Check that a base request with api_name in token succeeds
            self.app.wsgi_app = AuthMiddleware(self.base_wsgi_app, auth_mode=True, api_name="registration")
            res = self.client.get('/x-nmos/registration/', headers=mock_headers)
            self.assertEqual(200, res.status_code)

    def test_api_calls_with_incorrect_service(self):
        mock_headers = {"Authorization": "Bearer " + BEARER_TOKEN["access_token"]}

        with mock.patch("nmoscommon.auth.auth_middleware.MDNS_SERVICE_TYPE") as mock_service:
            mock_service = "this_is_definitely_not a service"
            res = self.client.get('/x-nmos/registration/', headers=mock_headers)
            self.assertEqual(500, res.status_code)
            self.assertIn("authorization server could not be found", res.json["error"].lower())

    def test_api_calls_with_bad_jwk_url(self):
        mock_headers = {"Authorization": "Bearer " + BEARER_TOKEN["access_token"]}

        with mock.patch.object(AuthMiddleware, "_get_jwk_url") as mock_jwk_url:
            mock_jwk_url.return_value = "http://something_that_should_fail.test"

            res = self.client.get('/x-nmos/registration/', headers=mock_headers)
            self.assertEqual(500, res.status_code)
            self.assertIn("could not retrieve the json web key", res.json["error"].lower())

    def test_extract_public_key(self):
        mock_headers = {"Authorization": "Bearer " + BEARER_TOKEN["access_token"]}

        with mock.patch.object(AuthMiddleware, "get_jwks") as mock_get_jwks:
            mock_get_jwks.return_value = "I am not a valid JSON Web Key"

            res = self.client.get('/x-nmos/registration/', headers=mock_headers)
            self.assertEqual(500, res.status_code)
            self.assertIn("public key could not be extracted from json web key", res.json["error"].lower())

    def test_handle_auth(self):
        mock_req = mock.MagicMock()

        mock_req.headers.get.return_value = None
        self.assertRaises(MissingAuthorizationError, self.middleware.handleAuth, req=mock_req, environ=None)

        mock_req.headers.get.return_value = "barer " + BEARER_TOKEN["access_token"]
        self.assertRaises(UnsupportedTokenTypeError, self.middleware.handleAuth, req=mock_req, environ=None)

        mock_req.headers.get.return_value = "Bearer null"
        self.assertRaises(MissingAuthorizationError, self.middleware.handleAuth, req=mock_req, environ=None)

    def mockGetResponse(self, code, content, headers, mockObject, method):
        resp = requests.Response()
        resp.status_code = code
        resp._content = json.dumps(content).encode('utf-8')
        resp.headers = headers
        mockObject.get.return_value = resp
        res = eval("self.middleware.{}()".format(method))
        return res

    @mock.patch.object(AuthMiddleware, "_get_jwk_url")
    @mock.patch("nmoscommon.auth.auth_middleware.requests")
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

    @mock.patch.object(AuthMiddleware, "_get_jwk_url")
    @mock.patch("nmoscommon.auth.auth_middleware.requests")
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

    def testfindJWKByAlg(self):
        self.assertEqual(self.middleware.findJWKByAlg(TEST_JWKS["keys"], "RS512"), TEST_JWKS["keys"][0])
        self.assertRaises(ValueError, self.middleware.findJWKByAlg, TEST_JWKS["keys"], "RS256")

    def testExtractPublicKeyWithJWK(self):
        self.assertRaises(Exception, self.middleware.extractPublicKey, "")
        self.assertEqual(self.middleware.extractPublicKey(TEST_JWK), PUB_KEY)

    def testExtractPublicKeyWithJWKS(self):
        self.assertRaises(Exception, self.middleware.extractPublicKey, "")
        self.assertEqual(self.middleware.extractPublicKey(TEST_JWKS["keys"]), PUB_KEY)

    def testExtractPublicKeyWithCert(self):
        self.assertEqual(self.middleware.extractPublicKey(CERT), PUB_KEY)

    @mock.patch.object(AuthMiddleware, "get_jwks")
    def testJWTClaimsValidator_x_nmos(self, mockGetJwk):
        mockGetJwk.return_value = TEST_JWK

        mock_req = mock.MagicMock()
        mock_req.headers.get.return_value = "Bearer " + BEARER_TOKEN["access_token"]

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

        ################## READ REQUESTS ##################
        mock_req.method = "GET"

        # Middleware should reject request with missing scope or missing token claim e.g. x-nmos-query
        self.middleware.api_name = "query"
        mock_req.path = "/x-nmos/query/"
        self.assertRaises(MissingClaimError, self.middleware.handleAuth, req=mock_req, environ=None)
        mock_req.path = "/x-nmos/query/v1.1/"
        self.assertRaises(MissingClaimError, self.middleware.handleAuth, req=mock_req, environ=None)
        mock_req.path = "/x-nmos/query/v1.1/senders"
        self.assertRaises(MissingClaimError, self.middleware.handleAuth, req=mock_req, environ=None)
        # Middleware should only permit requests to value of "api_name" i.e. query
        mock_req.path = "/x-nmos/registration/"
        self.assertRaises(MissingClaimError, self.middleware.handleAuth, req=mock_req, environ=None)


        # Middleware permits Read access due to x-nmos-connection token claim
        self.middleware.api_name = "connection"
        mock_req.path = "/x-nmos/connection/"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)
        mock_req.path = "/x-nmos/connection/v1.1/"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)
        mock_req.path = "/x-nmos/connection/v1.1/senders"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)


        # Middleware permits Read access due to x-nmos-registration token claim
        self.middleware.api_name = "registration"
        mock_req.path = "/x-nmos/registration/"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)
        mock_req.path = "/x-nmos/registration/v1.1/"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)
        mock_req.path = "/x-nmos/registration/v1.1/health"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)


        ################## WRITE REQUESTS ##################
        mock_req.method = "POST"

        # Middleware should reject request with missing scope or missing token claim e.g. x-nmos-query
        self.middleware.api_name = "query"
        mock_req.path = "/x-nmos/query/"
        self.assertRaises(MissingClaimError, self.middleware.handleAuth, req=mock_req, environ=None)
        mock_req.path = "/x-nmos/query/v1.1/"
        self.assertRaises(MissingClaimError, self.middleware.handleAuth, req=mock_req, environ=None)
        mock_req.path = "/x-nmos/query/v1.1/senders"
        self.assertRaises(MissingClaimError, self.middleware.handleAuth, req=mock_req, environ=None)
        # Middleware should only permit requests to value of "api_name" i.e. query
        mock_req.path = "/x-nmos/registration/"
        self.assertRaises(MissingClaimError, self.middleware.handleAuth, req=mock_req, environ=None)

        self.middleware.api_name = "connection"
        # Middleware permits Write Access at base resources due to scope / private claims
        mock_req.path = "/x-nmos/connection/"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)
        mock_req.path = "/x-nmos/connection/v1.1/"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)
        # Middleware denies Write access to subsequent paths
        mock_req.path = "/x-nmos/connection/v1.1/senders"
        self.assertRaises(InvalidClaimError, self.middleware.handleAuth, req=mock_req, environ=None)

        self.middleware.api_name = "registration"
        # Middleware should permits Read access due to token claims
        mock_req.path = "/x-nmos/registration/"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)
        mock_req.path = "/x-nmos/registration/v1.1/"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)
        mock_req.path = "/x-nmos/registration/v1.1/health"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)

    @mock.patch("nmoscommon.auth.claims_validator.getfqdn")
    @mock.patch.object(AuthMiddleware, "get_jwks")
    def testJWTClaimsValidator_aud(self, mockGetJwk, mockGetFQDN):
        mockGetJwk.return_value = TEST_JWK

        mock_req = mock.MagicMock()
        mock_req.headers.get.return_value = "Bearer " + BEARER_TOKEN["access_token"]
        mock_req.method = "GET"
        mock_req.path = "/x-nmos/registration/v1.1/health"

        self.middleware.api_name = "registration"

        # Same hostname as auth server succeeds
        mockGetFQDN.return_value = "ap-z420-5.rd.bbc.co.uk"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)

        # Different hostname succeeds
        mockGetFQDN.return_value = "tony_has_massive_halls.rd.bbc.co.uk"
        self.assertEqual(self.middleware.handleAuth(req=mock_req, environ=None), None)

        # Missing sub-domain fails
        mockGetFQDN.return_value = "something.bbc.co.uk"
        self.assertRaises(InvalidClaimError, self.middleware.handleAuth, req=mock_req, environ=None)

        # Missing domain fails
        mockGetFQDN.return_value = "malicious-site.co.uk"
        self.assertRaises(InvalidClaimError, self.middleware.handleAuth, req=mock_req, environ=None)


if __name__ == '__main__':
    unittest.main()
