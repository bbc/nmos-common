#!/usr/bin/env python

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
from copy import deepcopy
from nmoscommon.mdns.dnsUtils import checkDNSSDActive, getServiceTypes, discoverService
from nmoscommon.mdns.dnsUtils import getTXTRecord, getSRVRecord
from mock import MagicMock, patch
from nmoscommon.mdns.mdnsExceptions import DNSRecordNotFound


class TestDNSUtils(unittest.TestCase):

    def helper_setup_dns(self):
        def query_call(record, type):
            if record == self.expectedRecord:
                if type == self.expectedType:
                    return True
            print("record {} type {}".format(record, type))
            return False

        class NXDOMAIN(Exception):
            pass

        dns = self.dns
        dns.resolver = MagicMock()
        dns.resolver.query = MagicMock()
        dns.resolver.query.side_effect = query_call
        dns.resolver.NXDOMAIN = deepcopy(NXDOMAIN)
        search = MagicMock()
        dns.resolver.Resolver.return_value = search
        search.search = ["example.com", "result2"]
        return dns

    def helper_test_method(self, method, record, type, addDomain=False, addRecord=False):
        with patch('nmoscommon.mdns.dnsUtils.dns') as dns:
            self.dns = dns
            self.helper_setup_dns()
            if addDomain:
                self.expectedRecord = record + ".example.com"
            else:
                self.expectedRecord = record
            self.expectedType = type
            if addRecord:
                answer = method(record)
            else:
                answer = method()
            self.assertTrue(answer)

    def test_checkDNSDActive(self):
        self.helper_test_method(
            checkDNSSDActive,
            "lb._dns-sd._udp",
            "PTR",
            True
        )

    def test_checkDNSDFail(self):
        with patch('nmoscommon.mdns.dnsUtils.dns') as dns:
            self.dns = dns
            self.helper_setup_dns()
            self.dns.resolver.query.side_effect = self.dns.resolver.NXDOMAIN
            self.assertFalse(checkDNSSDActive())

    def test_get_service_types(self):
        self.helper_test_method(
            getServiceTypes,
            "_services._dns-sd._udp",
            "PTR",
            True
        )

    def test_get_discover_service(self):
        self.helper_test_method(
            discoverService,
            "_test_record",
            "PTR",
            False,
            True
        )

    def test_get_txt_record(self):
        self.helper_test_method(
            getTXTRecord,
            "_test_record",
            "TXT",
            False,
            True
        )

    def test_get_srv_record(self):
        self.helper_test_method(
            getSRVRecord,
            "_test_record",
            "SRV",
            False,
            True
        )


if __name__ == "__main__":
    unittest.main()
