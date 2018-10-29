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

"""This class is passed a DNS PTR record for a DNS-SD service, and a DNS Listener. It uses
DNSUtils to fetch the service and txt records for the service and uses that information
to notify the dns listener about the new service. It then checks the service twice per TTL
time to ensure it is still there. If it is not, it notifies the DNS listener, then asks the
dnsServiceController to destroy it using a callback passed to it"""


from nmoscommon.mdns import dnsUtils
from nmoscommon.mdns.mdnsExceptions import DNSRecordNotFound
from threading import Timer


class DNSService(object):

    def __init__(
        self,
        pointerRecord,
        type,
        dnsListener,
        removeCallback
    ):
        self.pointerRecord = pointerRecord
        self.dnsListener = dnsListener
        self.removeCallback = removeCallback
        self.type = type
        self.name = self.pointerRecord.to_text()
        self._initialiseFromDNS()

    def _initialiseFromDNS(self):
        self.serviceRecord = dnsUtils.getSRVRecord(self.pointerRecord.to_text())
        self.txtRecord = dnsUtils.getTXTRecord(self.pointerRecord.to_text())
        self.ttl = self.txtRecord.rrset.ttl
        self.txt = self.txtRecord[0]
        self._parseSRVRecord()

    def _parseSRVRecord(self):
        self.addr = self.serviceRecord[3]
        self.port = self.serviceRecord[2]

    def _removeService(self):
        self.removeCallback(self.name)
        self.dnsListener.remove_service(self)
        self.timer = None

    def _ttlTimerCallback(self):
        try:
            self._initialiseFromDNS()
        except DNSRecordNotFound:
            self._removeService()
        else:
            self._startTimer()

    def _startTimer(self):
        self.ttlTimer = Timer(self.ttl, self._ttlTimerCallback)
        self.ttlTimer.start()

    def start(self):
        self._startTimer()

    def stop(self):
        self.ttlTimer.cancel()

    def close(self):
        self.dnsListener.remove_service(self)
        self.stop()
