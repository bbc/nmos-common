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

import dns
from dns import resolver
from nmoscommon.mdns.mdnsExceptions import DNSRecordNotFound


def _appendDomain(record):
    resolve = dns.resolver.Resolver()
    machineDomiain = resolve.search[0]
    record = record + "." + str(machineDomiain)
    return record


def _dnsRequest(record, type, addDomain=True):
    if addDomain:
        record = _appendDomain(record)
    try:
        answers = dns.resolver.query(record, type)
    except dns.resolver.NXDOMAIN:
        print("Could not find {} type record at {}".format(type, record))
        raise DNSRecordNotFound
    else:
        return answers


def checkDNSSDActive():
    return bool(_dnsRequest('lb._dns-sd._udp', 'PTR'))


def getServiceTypes():
    return _dnsRequest('_services._dns-sd._udp', 'PTR')


def discoverService(regType):
    return _dnsRequest(regType, 'PTR', False)


def getTXTRecord(service):
    return _dnsRequest(service, 'TXT', False)


def getSRVRecord(service):
    return _dnsRequest(service, 'SRV', False)
