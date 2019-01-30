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


import socket
from nmoscommon.mdns import dnsUtils
from nmoscommon.mdns.mdnsExceptions import DNSRecordNotFound
from threading import Timer


class DNSService(object):

    def __init__(
        self,
        pointerRecord,
        type,
        dnsListener,
        removeCallback,
        logger
    ):
        self.pointerRecord = pointerRecord
        self.dnsListener = dnsListener
        self.removeCallback = removeCallback
        self.type = type
        self.name = self.pointerRecord.to_text()
        self.logger = logger
        self._initialiseFromDNS()
        self.running = False

    def _initialiseFromDNS(self):
        self.serviceRecord = dnsUtils.getSRVRecord(self.pointerRecord.to_text())
        self.txtRecord = dnsUtils.getTXTRecord(self.pointerRecord.to_text())
        self.ttl = self.txtRecord.rrset.ttl
        self.txt = self._makeTXTDict(self.txtRecord[0])
        self._parseSRVRecord()

    def _makeTXTDict(self, record):
        toReturn = {}
        bits = record.to_text().split(" ")
        for bit in bits:
            fragments = bit.split("=")
            toReturn[fragments[0][1:]] = fragments[1][:-1]
        return toReturn

    def _removeTrailingDot(self, hostname):
        return hostname.rstrip(".")

    def _parseSRVRecord(self):
        for value in self.serviceRecord:
            entries = value.to_text().split(" ")
            self.hostname = self._removeTrailingDot(entries[3])
            self.address = socket.gethostbyname(self.hostname)
            self.port = int(entries[2])

    def _removeService(self):
        self.dnsListener.removeListener(self)
        self.ttlTimer.cancel()

    def _updateService(self):
        self.dnsListener.removeListener(self)
        self.dnsListener.addListener(self)

    def _addService(self):
        self.dnsListener.addListener(self)

    def _ttlTimerCallback(self):
        try:
            self._initialiseFromDNS()
            self._updateService()
        except DNSRecordNotFound:
            self.removeCallback(self)
        else:
            self._startTimer()

    def _startTimer(self):
        self.ttlTimer = Timer(self.ttl, self._ttlTimerCallback)
        self.ttlTimer.start()

    def start(self):
        self._startTimer()
        self.running = True
        self._addService()

    def stop(self):
        if self.running:
            self.ttlTimer.cancel()
        self.running = False

    def close(self, signum=None, frame=None):
        self.dnsListener.removeListener(self)
        self.stop()
