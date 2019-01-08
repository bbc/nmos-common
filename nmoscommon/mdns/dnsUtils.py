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

import dns.resolver  # Importing dns alone is not enough for NXDOMAIN to work
from nmoscommon.mdns.mdnsExceptions import DNSRecordNotFound


def _defaultDomain():
    resolve = dns.resolver.Resolver()
    return str(resolve.search[0])


def _appendDomain(record, domainName):
    record = record + "." + domainName
    return record


def _dnsRequest(record, recordType, addDomain=True, customDomain=None):
    if addDomain:
        if customDomain:
            record = _appendDomain(record, customDomain)
        else:
            record = _appendDomain(record, _defaultDomain())
    try:
        answers = dns.resolver.query(record, recordType)
    except dns.resolver.NXDOMAIN:
        print("Could not find {} type record at {}".format(recordType, record))
        raise DNSRecordNotFound
    else:
        return answers


def checkDNSSDActive(customDomain=None):
    try:
        _dnsRequest('lb._dns-sd._udp', 'PTR', True, customDomain)
    except DNSRecordNotFound:
        return False
    else:
        return True


def getServiceTypes(customDomain=None):
    return _dnsRequest('_services._dns-sd._udp', 'PTR', True, customDomain)


def discoverService(regType, customDomain=None):
    return _dnsRequest(regType, 'PTR', True, customDomain)


def getTXTRecord(service):
    return _dnsRequest(service, 'TXT', False)


def getSRVRecord(service):
    return _dnsRequest(service, 'SRV', False)
