# Copyright 2017 British Broadcasting Corporation
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

import unittest
import mock
from nmoscommon.mdnsbridge import *
import traceback
import json

from nmoscommon.nmoscommonconfig import config as _config

class TestIppmDNSBridge(unittest.TestCase):

    @mock.patch('nmoscommon.mdnsbridge.Logger')
    def setUp(self, Logger):
        with mock.patch.dict(_config, { "test" : "active" }):
            self.UUT = IppmDNSBridge(logger=mock.sentinel.logger)
        Logger.assert_called_once_with("mdnsbridge", mock.sentinel.logger)
        self.logger = Logger.return_value
        self.assertIn("test", self.UUT.config)

    def test_init(self):
        pass

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_first_service_with_matching_priority(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100

        services = [
            { "priority" : 100, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 100, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 100, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[0]["txt"]["api_proto"] + "://" + services[0]["address"] + ":" + str(services[0]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_first_service_with_matching_priority_including_ipv6(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100

        services = [
            { "priority" : 100, "txt" : { "api_proto" : "https" }, "address" : "CAFE:FACE:BBC1:BBC2:BBC4:1337:DEED:2323", "port" : 12345 },
            { "priority" : 100, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 100, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[0]["txt"]["api_proto"] + "://[" + services[0]["address"] + "]:" + str(services[0]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_first_service_with_matching_priority(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100

        services = [
            { "priority" : 97, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 13, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 100, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[2]["txt"]["api_proto"] + "://" + services[2]["address"] + ":" + str(services[2]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_lowest_priority_service_when_none_match(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 99

        services = [
            { "priority" : 97, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 13, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 53, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[1]["txt"]["api_proto"] + "://" + services[1]["address"] + ":" + str(services[1]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=3) # guaranteed random, chosen by roll of fair die
    def test_gethref_when_multiple_services_have_same_priority_return_one_at_random(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 99

        services = [
            { "priority" : 97, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 13, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 53, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            { "priority" : 13, "txt" : { "api_proto" : "httpv" }, "address" : "service_address3", "port" : 12348 },
            { "priority" : 13, "txt" : { "api_proto" : "httpw" }, "address" : "service_address4", "port" : 12349 },
            { "priority" : 13, "txt" : { "api_proto" : "httpx" }, "address" : "service_address5", "port" : 12350 },
            { "priority" : 13, "txt" : { "api_proto" : "httpy" }, "address" : "service_address6", "port" : 12351 },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[5]["txt"]["api_proto"] + "://" + services[5]["address"] + ":" + str(services[5]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_empty_string_when_no_matching_services(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100

        services = [
            { "priority" : 97, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 13, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 53, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, "")

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_local_service_when_no_matching_query_service(self, rand, get):
        srv_type = "nmos-query"
        self.UUT.config['priority'] = 100

        services = [
            { "priority" : 97, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 13, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 53, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.return_value.status_code=200
        get.return_value.json.side_effect = [ { "representation" : json.loads(json.dumps(services)) }, mock.sentinel.SHOULD_BE_IGNORED ]
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, "http://127.0.0.1/x-nmos/query/v1.0/")

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_empty_string_when_no_matching_query_service_including_local(self, rand, get):
        srv_type = "nmos-query"
        self.UUT.config['priority'] = 100

        services = [
            { "priority" : 97, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 13, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 53, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.side_effect = [ mock.DEFAULT, Exception ]
        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, "")

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_empty_string_when_request_fails(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100

        services = [
            { "priority" : 97, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 13, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 53, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.side_effect=Exception
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, "")


    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_second_call_uses_cache(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 99

        services = [
            { "priority" : 97, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 13, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 13, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.side_effect = [ mock.DEFAULT, Exception ]
        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[1]["txt"]["api_proto"] + "://" + services[1]["address"] + ":" + str(services[1]["port"]))

        get.reset_mock()
        href = self.UUT.getHref(srv_type)
        get.assert_not_called()
        self.assertEqual(href, services[2]["txt"]["api_proto"] + "://" + services[2]["address"] + ":" + str(services[2]["port"]))


    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_second_call_uses_cache_at_high_priority(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100

        services = [
            { "priority" : 100, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 100, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 100, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        get.side_effect = [ mock.DEFAULT, Exception ]
        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[0]["txt"]["api_proto"] + "://" + services[0]["address"] + ":" + str(services[0]["port"]))

        get.reset_mock()
        href = self.UUT.getHref(srv_type)
        get.assert_not_called()
        self.assertEqual(href, services[0]["txt"]["api_proto"] + "://" + services[0]["address"] + ":" + str(services[0]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_second_call_rechecks_if_only_low_priority_servers_exist(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100

        services = [
            { "priority" : 200, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 300, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 400, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            ]

        second_services = [
            { "priority" : 200, "txt" : { "api_proto" : "https" }, "address" : "service_address0", "port" : 12345 },
            { "priority" : 300, "txt" : { "api_proto" : "httpt" }, "address" : "service_address1", "port" : 12346 },
            { "priority" : 400, "txt" : { "api_proto" : "httpu" }, "address" : "service_address2", "port" : 12347 },
            { "priority" : 100, "txt" : { "api_proto" : "httpv" }, "address" : "service_address3", "port" : 12348 },
            ]

        getmocks = [ mock.MagicMock(name="get1()"), mock.MagicMock(name="get2()") ]
        get.side_effect = [ getmocks[0], getmocks[1] ]
        getmocks[0].status_code=200
        getmocks[0].json.return_value = { "representation" : json.loads(json.dumps(services)) }
        getmocks[1].status_code=200
        getmocks[1].json.return_value = { "representation" : json.loads(json.dumps(second_services)) }
        href = self.UUT.getHref(srv_type)
        get.assert_called_once_with("http://127.0.0.1/x-ipstudio/mdnsbridge/v1.0/" + srv_type + "/", timeout=0.5, proxies={'http': ''})
        self.assertEqual(href, "")

        get.reset_mock()
        href = self.UUT.getHref(srv_type)
        get.assert_called_once_with("http://127.0.0.1/x-ipstudio/mdnsbridge/v1.0/" + srv_type + "/", timeout=0.5, proxies={'http': ''})
        self.assertEqual(href, second_services[3]["txt"]["api_proto"] + "://" + second_services[3]["address"] + ":" + str(second_services[3]["port"]))
