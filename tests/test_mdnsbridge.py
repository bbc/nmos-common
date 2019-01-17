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
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 100, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 100, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 100, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
        ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[0]["protocol"] + "://" + services[0]["hostname"] + ":" + str(services[0]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_first_service_with_matching_priority_including_ipv6(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 100, "protocol" : "http", "address" : "CAFE:FACE:BBC1:BBC2:BBC4:1337:DEED:2323", "port" : 12345, "hostname": None },
            { "priority" : 100, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": None },
            { "priority" : 100, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": None },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[0]["protocol"] + "://[" + services[0]["address"] + "]:" + str(services[0]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_only_service_with_matching_priority(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 97, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 100, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[2]["protocol"] + "://" + services[2]["hostname"] + ":" + str(services[2]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_only_service_with_matching_priority_https(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100
        self.UUT.config['https_mode'] = "enabled"

        services = [
            { "priority" : 97, "protocol" : "https", "address" : "service_address0", "port" : 12345, "hostname": "service_host0"},
            { "priority" : 13, "protocol" : "https", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 100, "protocol" : "https", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[2]["protocol"] + "://" + services[2]["hostname"] + ":" + str(services[2]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_lowest_priority_service_when_none_match(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 99
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 97, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 53, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[1]["protocol"] + "://" + services[1]["hostname"] + ":" + str(services[1]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=3) # guaranteed random, chosen by roll of fair die
    def test_gethref_when_multiple_services_have_same_priority_return_one_at_random(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 99
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 97, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 53, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address3", "port" : 12348, "hostname": "service_host3" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address4", "port" : 12349, "hostname": "service_host4" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address5", "port" : 12350, "hostname": "service_host5" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address6", "port" : 12351, "hostname": "service_host6" },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[5]["protocol"] + "://" + services[5]["hostname"] + ":" + str(services[5]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_empty_string_when_no_matching_services(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 100, "protocol" : "https", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 53, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
            ]

        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, "")

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_returns_empty_string_when_no_matching_services_https(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100
        self.UUT.config['https_mode'] = "enabled"

        services = [
            { "priority" : 100, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 53, "protocol" : "https", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
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
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 97, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 53, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
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
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 97, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 53, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
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
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 97, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 13, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 53, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
            ]

        get.side_effect=Exception
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, "")


    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_second_call_uses_cache(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 99
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 97, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0"},
            { "priority" : 13, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1"},
            { "priority" : 13, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2"},
            ]

        get.side_effect = [ mock.DEFAULT, Exception ]
        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[1]["protocol"] + "://" + services[1]["hostname"] + ":" + str(services[1]["port"]))

        get.reset_mock()
        href = self.UUT.getHref(srv_type)
        get.assert_not_called()
        self.assertEqual(href, services[2]["protocol"] + "://" + services[2]["hostname"] + ":" + str(services[2]["port"]))


    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_second_call_uses_cache_at_high_priority(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 100, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0"},
            { "priority" : 100, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1"},
            { "priority" : 100, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2"},
            ]

        get.side_effect = [ mock.DEFAULT, Exception ]
        get.return_value.status_code=200
        get.return_value.json.return_value = { "representation" : json.loads(json.dumps(services)) }
        href = self.UUT.getHref(srv_type)
        self.assertEqual(href, services[0]["protocol"] + "://" + services[0]["hostname"] + ":" + str(services[0]["port"]))

        get.reset_mock()
        href = self.UUT.getHref(srv_type)
        get.assert_not_called()
        self.assertEqual(href, services[0]["protocol"] + "://" + services[0]["hostname"] + ":" + str(services[0]["port"]))

    @mock.patch('requests.get')
    @mock.patch('random.randint', return_value=0) # guaranteed random, chosen by roll of fair die
    def test_gethref_second_call_rechecks_if_only_low_priority_servers_exist(self, rand, get):
        srv_type = "potato"
        self.UUT.config['priority'] = 100
        self.UUT.config['https_mode'] = "disabled"

        services = [
            { "priority" : 200, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 300, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 400, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
            ]

        second_services = [
            { "priority" : 200, "protocol" : "http", "address" : "service_address0", "port" : 12345, "hostname": "service_host0" },
            { "priority" : 300, "protocol" : "http", "address" : "service_address1", "port" : 12346, "hostname": "service_host1" },
            { "priority" : 400, "protocol" : "http", "address" : "service_address2", "port" : 12347, "hostname": "service_host2" },
            { "priority" : 100, "protocol" : "http", "address" : "service_address3", "port" : 12348, "hostname": "service_host3" },
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
        self.assertEqual(href, second_services[3]["protocol"] + "://" + second_services[3]["hostname"] + ":" + str(second_services[3]["port"]))
