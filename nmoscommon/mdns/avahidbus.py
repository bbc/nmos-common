#!/usr/bin/python

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

import time
import avahi
import gobject
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gevent
from gevent import monkey
import glib

monkey.patch_all()

__all__ = ["MDNSEngine"]

def _idle():
    gevent.sleep(0.1)
    return True

class MDNSEngine(object):
    def __init__(self, dns_mode=None):
        self.dns_mode = dns_mode
        self.loop = DBusGMainLoop()
        self.bus = dbus.SystemBus(mainloop=self.loop)
        self.server = dbus.Interface(self.bus.get_object(avahi.DBUS_NAME, '/'), avahi.DBUS_INTERFACE_SERVER)
        self.greenlet = None
        self.running = False
        self._mainloop = None
        # Advertisement variables
        self.reg_list = []
        self.unreg_queue = []
        # Discovery variables
        self.domains = set()
        self.domain_sbrowsers = {}
        self.callbacks = []

    def callback_on_services(self, regtype, callback, registerOnly=True, domain=None):
        """ Call from outside this class in order to add a callback for a particular service type """

        # Use of the 'domain' argument is no longer supported.
        for domain in self.domains:
            sbrowser = self._get_sbrowser(regtype, domain)
            self._add_callback_handler(sbrowser, callback, registerOnly)

        self.callbacks.append({
            "type": regtype,
            "callback": callback,
            "reg_only": registerOnly
        })

    def refresh_unicast_dns(self):
        """ Force a fetch from Avahi's cache of unicast DNS records, given callbacks do not fire for unicast case """
        full_domains = set(self.domains)
        for domain in full_domains:
            if domain == "local":
                continue

            self._remove_domain(None, None, domain)
            self._add_domain(None, None, domain)

    def register(self, name, regtype, port, txtRecord=None, callback=None):
        """ Advertise a new service vis multicast DNS """
        def _entrygroup_state_changed(name, regtype, port, txtRecord, callback):
            def _inner(state, error):
                if callback is not None:
                    if state == avahi.ENTRY_GROUP_COLLISION:
                        callback({ "action" : "collision", "name" : name, "regtype" : regtype, "port" : port, "txtRecord" : txtRecord})
                    elif state == avahi.ENTRY_GROUP_ESTABLISHED:
                        callback({ "action" : "established", "name" : name, "regtype" : regtype, "port" : port, "txtRecord" : txtRecord})
                    elif state == avahi.ENTRY_GROUP_FAILURE:
                        callback({ "action" : "failure", "name" : name, "regtype" : regtype, "port" : port, "txtRecord" : txtRecord})
            return _inner

        if txtRecord is None:
            txtRecord = {}
        entrygroup = self._findservice(name, regtype)
        if entrygroup is None:
            entrygroup = dbus.Interface(self.bus.get_object(avahi.DBUS_NAME,
                                                            self.server.EntryGroupNew()),
                                         avahi.DBUS_INTERFACE_ENTRY_GROUP)
        if entrygroup.GetState() == avahi.ENTRY_GROUP_ESTABLISHED:
            entrygroup.Reset()
        entrygroup.connect_to_signal("StateChanged", _entrygroup_state_changed(name, regtype, port, txtRecord, callback))
        entrygroup.AddService(avahi.IF_UNSPEC,
                              avahi.PROTO_UNSPEC,
                              dbus.UInt32(0),
                              name,
                              regtype,
                              "local",
                              '',
                              port,
                              avahi.dict_to_txt_array(txtRecord))
        entrygroup.Commit()
        self.reg_list.append((name, regtype, port, txtRecord, entrygroup))

    def update(self, name, regtype, txtRecord=None):
        """ Update the TXT record associated with an existing multicast DNS advertisement """
        if txtRecord is None:
            txtRecord = {}
        entrygroup = self._findservice(name, regtype)
        if entrygroup is not None:
            entrygroup.UpdateServiceTxt(avahi.IF_UNSPEC,
                                        avahi.PROTO_UNSPEC,
                                        dbus.UInt32(0),
                                        name,
                                        regtype,
                                        "local.",
                                        avahi.dict_to_txt_array(txtRecord))

    def unregister(self, name, regtype):
        """ Unregister a multicast DNS advertisement """
        for x in self.reg_list:
            if x[0] == name and x[1] == regtype:
                x[4].Free()
                self.reg_list.remove(x)

    def _add_domain(self, interface, protocol, domain, flags=None):
        """ Add a multicast or unicast domain to search for DNS-SD records """
        self.domains.add(domain)

        if domain not in self.domain_sbrowsers:
            self.domain_sbrowsers[domain] = {}

        for callback_data in self.callbacks:
            sbrowser = self._get_sbrowser(callback_data["type"], domain)
            self._add_callback_handler(sbrowser, callback_data["callback"], callback_data["reg_only"])

    def _remove_domain(self, interface, protocol, domain, flags=None):
        """ Remove a multicast or unicast domain to search for DNS-SD records """
        self.domains.discard(domain)

        if domain in self.domain_sbrowsers:
            for service_type in self.domain_sbrowsers[domain]:
                sbrowser = self.domain_sbrowsers[domain][service_type]
                self.bus.remove_signal_receiver(None,  # Wildcard: Remove all callbacks for this service browser
                                                "ItemNew",
                                                avahi.DBUS_INTERFACE_SERVICE_BROWSER,
                                                None,
                                                sbrowser)
                self.bus.remove_signal_receiver(None,  # Wildcard: Remove all callbacks for this service browser
                                                "ItemRemove",
                                                avahi.DBUS_INTERFACE_SERVICE_BROWSER,
                                                None,
                                                sbrowser)

    def _get_sbrowser(self, service_type, domain):
        """ Fetch or generate a service browser instance matching the domain and service type """
        sbrowser = None
        if service_type not in self.domain_sbrowsers[domain]:
            sbrowser = self.server.ServiceBrowserNew(avahi.IF_UNSPEC,
                                                     avahi.PROTO_UNSPEC,
                                                     service_type,
                                                     domain,
                                                     dbus.UInt32(0))
            self.domain_sbrowsers[domain][service_type] = sbrowser
        else:
            sbrowser = self.domain_sbrowsers[domain][service_type]
        return sbrowser

    def _add_callback_handler(self, sbrowser, callback, reg_only):
        """ Add a callback for a particular service browser reporting additions or removals of records """
        bcb = self._browse_callback(callback)
        self.bus.add_signal_receiver(bcb, "ItemNew", avahi.DBUS_INTERFACE_SERVICE_BROWSER, None, sbrowser)
        if not reg_only:
            rcb = self._remove_callback(callback)
            self.bus.add_signal_receiver(rcb, "ItemRemove", avahi.DBUS_INTERFACE_SERVICE_BROWSER, None, sbrowser)

    def _findservice(self, name, regtype):
        """ Find an existing registration for a given service type and name if one exists """
        for x in self.reg_list:
            if x[0] == name and x[1] == regtype:
                return x[4]
        return None

    def _error_handler(self, *args):
        """ Error handler for Avahi DBus callbacks """
        print "Error: %r" % (args,)

    def _resolve_callback(self, callback):
        """ Callback for the resolution of a DNS-SD record """
        def _inner(interface, protocol, name, stype, domain, host, arprotocol, address, port, txt, flags):
            txtd = dict( x.split('=') for x in avahi.txt_array_to_string_array(txt) )
            callback({"action": "add", "name": name, "type": stype, "address": address, "port": port, "txt": txtd, "interface": interface})
        return _inner

    def _browse_callback(self, callback):
        """ Callback for addition of a record to the DNS-SD browse space """
        def _inner(interface, protocol, name, stype, domain, flags):
            self.server.ResolveService(interface, protocol, name, stype, domain, avahi.PROTO_UNSPEC, dbus.UInt32(0),
                                       reply_handler=self._resolve_callback(callback), error_handler=self._error_handler)
        return _inner

    def _remove_callback(self, callback):
        """ Callback for removal of an existing record from the DNS-SD browse space """
        def _inner(interface, protocol, name, type, domain, flags):
            callback({"action": "remove", "name": name, "type": type})
        return _inner

    def start(self):
        """ Start the mDNS Engine """
        if not gobject.MainLoop().is_running():
            self.greenlet = gevent.spawn(self._run)
            self.running = True
            gevent.sleep(0)

        # Set up domains for multicast DNS
        if self.dns_mode != "unicast":
            self._add_domain(None, None, "local")

        # Set up domains for unicast DNS
        if self.dns_mode != "multicast":
            dbrowser = self.server.DomainBrowserNew(avahi.IF_UNSPEC, avahi.PROTO_UNSPEC, "", 0, dbus.UInt32(0))
            db_interface = dbus.Interface(self.bus.get_object(avahi.DBUS_NAME, dbrowser),
                                          avahi.DBUS_INTERFACE_DOMAIN_BROWSER)
            db_interface.connect_to_signal("ItemNew", self._add_domain)
            db_interface.connect_to_signal("ItemRemove", self._remove_domain)

    def stop(self):
        """ Stop the mDNS Engine """
        if self.greenlet is not None:
            if self._mainloop is not None:
                self._mainloop.quit()
                gevent.sleep(0)
            self._mainloop = None
            self.greenlet = None
        self.running = False

    def close(self):
        """ Remove all existing DNS-SD advertisements and close DBus connection """
        for x in self.reg_list:
            x[4].Free()
            self.reg_list.remove(x)
        for domain in self.domains:
            self._remove_domain(None, None, domain)
        self.bus.close()

    def _run(self):
        """ Start the run loop """
        glib.idle_add(_idle)
        self._mainloop = gobject.MainLoop()
        self._mainloop.run()


if __name__ == "__main__": # pragma: no cover
    import sys
    from gevent import monkey; monkey.patch_all()
    import traceback

    def print_results_callback(data):
        print data

    e = MDNSEngine()
    e.start()

    regtype = "_nmos-node._tcp"
    if len(sys.argv) > 1:
        regtype = sys.argv[1]

    e.register("python_avahi_test", "_test._tcp", 12345, {"Potato" : "very"})

    e.callback_on_services(regtype, callback=print_results_callback)

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
        except:
            traceback.print_exc()
            break

    e.stop()
    e.close()
