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

from six import PY2

import unittest
import mock

with mock.patch("nmoscommon.query.monkey"):
    from nmoscommon.query import *

import traceback

class TestQueryInit(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestQueryInit, self).__init__(*args, **kwargs)
        if PY2:
            self.assertCountEqual = self.assertItemsEqual

    def test_init_with_ipv6_fallback(self):
        self.query_url = "http://query.example/"
        self.mdns_bridge = mock.MagicMock(name="mdnsbridge")
        self.mdns_bridge.getHref.side_effect = [ "fe80:BBC1:BBC2:BBC4:BBC1:BBC2:BBC4:CAFE" for _ in range(0,12) ] + [ self.query_url ] + [ Exception ]
        with mock.patch("nmoscommon.query.Logger") as Logger:
            try:
                self.UUT = QueryService(self.mdns_bridge, logger=mock.sentinel.logger, apiversion=QUERY_APIVERSION,  priority=mock.sentinel.priority)
            except Exception as e:
                self.fail(msg="QueryService.__init__ raises unexpected exception: %s" % (traceback.format_exc(),))
            self.logger = Logger.return_value
        expected_calls = [ mock.call(QUERY_MDNSTYPE, mock.sentinel.priority) for _ in range(0, 13) ]
        self.assertListEqual(self.mdns_bridge.getHref.mock_calls, expected_calls)

    def test_init_with_ipv6_fallback_accepts_ipv6_after_too_many_retries(self):
        self.query_url = "http://query.example/"
        self.mdns_bridge = mock.MagicMock(name="mdnsbridge")
        self.mdns_bridge.getHref.side_effect = [ "fe80:BBC1:BBC2:BBC4:BBC1:BBC2:BBC4:CAFE" for _ in range(0,22) ] + [ Exception ]
        with mock.patch("nmoscommon.query.Logger") as Logger:
            try:
                self.UUT = QueryService(self.mdns_bridge, logger=mock.sentinel.logger, apiversion=QUERY_APIVERSION,  priority=mock.sentinel.priority)
            except Exception as e:
                self.fail(msg="QueryService.__init__ raises unexpected exception: %s" % (traceback.format_exc(),))
            self.logger = Logger.return_value
        expected_calls = [ mock.call(QUERY_MDNSTYPE, mock.sentinel.priority) for _ in range(0, 22) ]
        self.assertListEqual(self.mdns_bridge.getHref.mock_calls, expected_calls)

class TestQuery(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestQuery, self).__init__(*args, **kwargs)
        if PY2:
            self.assertCountEqual = self.assertItemsEqual

    def setUp(self):
        self.query_url = "http://query.example/"
        self.mdns_bridge = mock.MagicMock(name="mdnsbridge")
        self.mdns_bridge.getHref.return_value = self.query_url
        with mock.patch("nmoscommon.query.Logger") as Logger:
            try:
                self.UUT = QueryService(self.mdns_bridge, logger=mock.sentinel.logger, apiversion=QUERY_APIVERSION,  priority=mock.sentinel.priority)
            except Exception as e:
                self.fail(msg="QueryService.__init__ raises unexpected exception: %s" % (traceback.format_exc(),))
            self.logger = Logger.return_value
        self.mdns_bridge.getHref.assert_called_once_with(QUERY_MDNSTYPE, mock.sentinel.priority)

    @mock.patch("requests.get")
    def assert_get_services_correct(self, get, with_node_id=False, status_code=200, with_exceptions=0):
        service_urn = mock.sentinel.service_urn
        get.side_effect = [ Exception for _ in range(0,with_exceptions) ] + [ mock.DEFAULT ]
        get.return_value.status_code = status_code
        get.return_value.json.return_value = [ { "id" : mock.sentinel.node_id,
                                                     "services" : [ { "id" : mock.sentinel.id0, "type" :  mock.sentinel.service_urn },
                                                                    { "id" : mock.sentinel.id1, "type" :  mock.sentinel.other_service_urn1 },
                                                                    { "id" : mock.sentinel.id2, "type" :  mock.sentinel.other_service_urn2 },
                                                                    { "id" : mock.sentinel.id3, "type" :  mock.sentinel.other_service_urn3 },
                                                                    ] },
                                                { "id" : mock.sentinel.other_node_id1,
                                                      "services" : [ { "id" : mock.sentinel.id4, "type" :  mock.sentinel.service_urn },
                                                                    { "id" : mock.sentinel.id5, "type" :  mock.sentinel.other_service_urn5 },
                                                                    { "id" : mock.sentinel.id6, "type" :  mock.sentinel.other_service_urn6 },
                                                                    { "id" : mock.sentinel.id7, "type" :  mock.sentinel.other_service_urn7 },
                                                                    ] },
                                                { "id" : mock.sentinel.other_node_id2,
                                                      "services" : [ { "id" : mock.sentinel.id8, "type" :  mock.sentinel.other_service_urn8 },
                                                                    { "id" : mock.sentinel.id9, "type" :  mock.sentinel.other_service_urn9 },
                                                                    { "id" : mock.sentinel.id10, "type" :  mock.sentinel.other_service_urn10 },
                                                                    { "id" : mock.sentinel.id11, "type" :  mock.sentinel.other_service_urn11 },
                                                                    ] },]
        self.mdns_bridge.getHref.side_effect = [ self.query_url + str(n) for n in range(0,5) ]

        if with_exceptions >= 3:
            with self.assertRaises(QueryNotFoundError):
                r = self.UUT.get_services(service_urn, node_id=(mock.sentinel.node_id if with_node_id else None))
        else:
            r = self.UUT.get_services(service_urn, node_id=(mock.sentinel.node_id if with_node_id else None))

        expected_get_calls = ([ mock.call("{}/{}/{}/{}{}".format(self.query_url, QUERY_APINAMESPACE, QUERY_APINAME, QUERY_APIVERSION, "/nodes/")) ] +
                                  [ mock.call("{}/{}/{}/{}{}".format(self.query_url + str(n), QUERY_APINAMESPACE, QUERY_APINAME, QUERY_APIVERSION, "/nodes/")) for n in range(0, min(2,with_exceptions)) ])
        self.assertListEqual([ x for x in get.mock_calls if x[0] == "" ], expected_get_calls)
        if with_exceptions < 3:
            if status_code == 200:
                if not with_node_id:
                    self.assertCountEqual(r, [ { "id" : mock.sentinel.id0, "type" :  mock.sentinel.service_urn },
                                                { "id" : mock.sentinel.id4, "type" :  mock.sentinel.service_urn },
                                            ])
                else:
                    self.assertCountEqual(r, [ { "id" : mock.sentinel.id0, "type" :  mock.sentinel.service_urn } ])
            else:
                self.assertListEqual(r, [])

    def test_get_services(self):
        self.assert_get_services_correct(with_node_id=False)

    def test_get_services_with_node_id(self):
        self.assert_get_services_correct(with_node_id=True)

    def test_get_services_with_404(self):
        self.assert_get_services_correct(status_code=404)

    def test_get_services_with_one_timeout(self):
        self.assert_get_services_correct(with_exceptions=1)

    def test_get_services_with_two_timeouts(self):
        self.assert_get_services_correct(with_exceptions=2)

    def test_get_services_with_three_timeouts(self):
        self.assert_get_services_correct(with_exceptions=3)

    @mock.patch("websocket.WebSocketApp")
    @mock.patch("requests.post")
    def assert_subscribe_topic_correct(self, post, WebSocketApp, status_code=200, query_url=None, bad_json=False, socket_fail=False):
        if query_url is None:
            query_url = self.query_url
        topic = "dummy_topic"
        on_event = mock.MagicMock(name="on_event")
        on_open  = mock.MagicMock(name="on_open")
        self.mdns_bridge.getHref.return_value = query_url
        post.return_value.status_code = status_code
        if not bad_json:
            post.return_value.json.return_value = { "ws_href" : mock.sentinel.ws_href }
        else:
            post.return_value.json.return_value = {}
        if socket_fail:
            WebSocketApp.return_value = None

        if status_code not in [200, 201] or query_url == "" or bad_json:
            with self.assertRaises(BadSubscriptionError):
                self.UUT.subscribe_topic(topic, on_event, on_open=on_open)
            WebSocketApp.assert_not_called()
        elif socket_fail:
            with self.assertRaises(BadSubscriptionError):
                self.UUT.subscribe_topic(topic, on_event, on_open=on_open)
            WebSocketApp.assert_called_once_with(mock.sentinel.ws_href,
                                                    on_open=mock.ANY,
                                                    on_message=mock.ANY,
                                                    on_close=mock.ANY)
        else:
            self.UUT.subscribe_topic(topic, on_event, on_open=on_open)

            WebSocketApp.assert_called_once_with(mock.sentinel.ws_href,
                                                    on_open=mock.ANY,
                                                    on_message=mock.ANY,
                                                    on_close=mock.ANY)
            _on_open    = WebSocketApp.call_args[1]["on_open"]
            _on_message = WebSocketApp.call_args[1]["on_message"]
            _on_close   = WebSocketApp.call_args[1]["on_close"]

            WebSocketApp.return_value.run_forever.assert_called_once_with()

            # Should do nothing, and in particular not call on_open or on_event
            _on_close()

            # Test on_open works correctly
            on_open.assert_not_called()
            _on_open(mock.sentinel.unused_args)
            on_open.assert_called_once_with()

            # Test on_message works correctly
            on_event.assert_not_called()
            _on_message(mock.sentinel.unused_args, json.dumps({"grain" : {"data" : [ "event0", "event1", "event2", ]}}))
            self.assertListEqual(on_event.mock_calls, [ mock.call("event0"),
                                                                mock.call("event1"),
                                                                mock.call("event2"), ])

            # Test on_message works correctly
            on_event.reset_mock()
            _on_message(mock.sentinel.unused_args, json.dumps({"grain" : {"data" : {"foo" : "bar"}}}))
            on_event.assert_called_once_with({"foo" : "bar"})

    def test_subscribe_topic_works_with_200(self):
        self.assert_subscribe_topic_correct(status_code=200)

    def test_subscribe_topic_works_with_201(self):
        self.assert_subscribe_topic_correct(status_code=201)

    def test_subscribe_topic_raises_with_blank_query_url(self):
        self.assert_subscribe_topic_correct(query_url="")

    def test_subscribe_topic_raises_on_404(self):
        self.assert_subscribe_topic_correct(status_code=404)

    def test_subscribe_topic_raises_on_bad_json(self):
        self.assert_subscribe_topic_correct(bad_json=True)

    def test_subscribe_topic_raises_on_bad_socket(self):
        self.assert_subscribe_topic_correct(socket_fail=True)
