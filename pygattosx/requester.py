# pyxpcconnection: OS X XPC Bindings for Python
#
# Copyright (c) 2015 Matthew Else
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from future.utils import bytes_to_native_str, native_str_to_bytes
from future.builtins import int, bytes

from threading import Event

from .wrapper import ble_base

class GATTRequester():
    def __init__(self, address, connect=False):
        self.connected = False

        ble_base.registerEvent(38, self.onConnect)
        ble_base.registerEvent(40, self.onDisconnect)
        ble_base.registerEvent(56, self.onDiscover)
        ble_base.registerEvent(64, self.onDiscoverCharacteristics)
        ble_base.registerEvent(71, self.onReadResponse)
        ble_base.registerEvent(79, self.onReadResponse)

        self.uuid = address

        self.read_event = Event()
        self.write_event = Event()
        self.connect_event = Event()
        self.discover_event = Event()
        self.disconnection_event = Event()

        if connect:
            self.connect()

    def is_connected(self):
        return self.connected

    def connect(self, block = True, channel_type = 'random', security = None, psm = 0, mtu = 0):
        connect_data = {
            'kCBMsgArgOptions': {
                'kCBConnectOptionNotifyOnDisconnection': 1
            },
            'kCBMsgArgDeviceUUID': self.uuid
        }

        self.connect_event.clear()
        ble_base.write(31, connect_data)

        if block:
            self.connect_event.wait()

    def onConnect(self, args):
        # The waiting is over!
        print("Device Connected!")

        self.connected = True
        self.connect_event.set()

    def disconnect(self, block=False):
        self.connected = False

        disconnect_data = {
            'kCBMsgArgDeviceUUID', self.uuid
        }

        self.disconnection_event.clear()
        ble_base.write(32, disconnect_data)

        if block:
            self.disconnection_event.wait()

    def onDisconnect(self, args):
        self.disconnection_event.set()

    def discover_primary(self):
        discover_data = {
            'kCBMsgArgDeviceUUID': self.uuid
        }

        self.discover_event.clear()
        ble_base.write(45, discover_data)
        self.discover_event.wait()

        return self._discoveredServices

    def onDiscover(self, args):
        self._discoveredServices = []

        if 'kCBMsgArgServices' in args:
            for service in args['kCBMsgArgServices']:
                uuid = UUID(service['kCBMsgArgUUID'])
                start = service['kCBMsgArgServiceStartHandle']
                end = service['kCBMsgArgServiceEndHandle']

                self._discoveredServices.append({
                    'uuid': uuid,
                    'start': start,
                    'end': end
                })
        self.discover_event.set()

    def discover_characteristics(self, start, end):
        discover_data = {
            'kCBMsgArgDeviceUUID': self.uuid,
            'kCBMsgArgServiceStartHandle': start,
            'kCBMsgArgServiceEndHandle': end,
            'kCBMsgArgUUIDs': []
        }

        self.discover_event.clear()
        ble_base.write(62, discover_data)
        self.discover_event.wait()

        return self._discoveredCharacteristics

    def onDiscoverCharacteristics(self, args):
        chars = args['kCBMsgArgCharacteristics']

        self._discoveredCharacteristics = []

        for char in chars:
            uuid = UUID(bytes=char['kCBMsgArgUUID'])
            handle = char['kCBMsgArgCharacteristicHandle']
            valueHandle = char['kCBMsgArgCharacteristicValueHandle']
            properties = char['kCBMsgArgCharacteristicProperties']

            chars.append({
                'uuid': uuid,
                'handle': handle,
                'value_handle': valueHandle,
                'properties': properties
            })

        self.discover_event.set()

    def read_by_handle(self, valueHandle, characteristic, handle=None):
        self.read_data = None

        if characteristic:
            msg_id = 65
            read_data = {
                'kCBMsgArgDeviceUUID': self.uuid,
                'kCBMsgArgCharacteristicHandle': handle,
                'kCBMsgArgCharacteristicValueHandle': valueHandle
            }
        else:
            # descriptor
            msg_id = 77
            read_data = {
                'kCBMsgArgDeviceUUID': self.uuid,
                'kCBMsgArgDescriptorHandle': valueHandle
            }

        self.read_event.clear()
        ble_base.write(msg_id, read_data)
        self.read_event.wait()

        return self.read_data

    def onReadResponse(self, args):
        self.read_data = args['kCBMsgArgData']

