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

from copy import copy
from threading import Event

from bleep.util import BLEUUID

from .wrapper import ble_base

class GATTRequester():
    def __init__(self, address, connect=False):
        self.connected = False

        ble_base.registerEvent(38, self.onConnect)
        ble_base.registerEvent(40, self.onDisconnect)
        ble_base.registerEvent(56, self.onDiscover)
        ble_base.registerEvent(64, self.onDiscoverCharacteristics)
        ble_base.registerEvent(70, self.onReadResponse) # characteristic
        ble_base.registerEvent(78, self.onReadResponse) # descriptors
        ble_base.registerEvent(71, self.onWriteResponse) # characteristic
        ble_base.registerEvent(79, self.onWriteResponse) # descriptors
        ble_base.registerEvent(76, self.onDiscoverDescriptors)
        ble_base.registerEvent(73, self.onNotifyEnabled)

        # register notifcation callback
        #ble_base.registerEvent(73, self.onNotification)

        self.uuid = address

        self.read_event = Event()
        self.write_event = Event()
        self.connect_event = Event()
        self.discover_event = Event()
        self.discover_desc_event = Event()
        self.disconnection_event = Event()
        self.notify_enable_event = Event()

        if connect:
            self.connect()

    def on_notification(self, handle, data):
        # stub
        pass

    def on_indication(self, handle, data):
        # stub
        pass

    def is_connected(self):
        return self.connected

    def connect(self, block = True, channel_type = 'random', security = None, psm = 0, mtu = 0):
        ble_base.mutex.acquire()

        connect_data = {
            'kCBMsgArgOptions': {
                'kCBConnectOptionNotifyOnDisconnection': 1
            },
            'kCBMsgArgDeviceUUID': self.uuid
        }

        self.connect_event.clear()
        ble_base.write(31, connect_data)

        ble_base.mutex.release()

        if block:
            self.connect_event.wait()
            
    def onConnect(self, args):
        # The waiting is over!
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
            'kCBMsgArgDeviceUUID': self.uuid,
            'kCBMsgArgUUIDs': []
        }

        self.discover_event.clear()
        ble_base.write(45, discover_data)

        self.discover_event.wait()

        return self._discoveredServices

    def onDiscover(self, args):
        self._discoveredServices = []

        if 'kCBMsgArgServices' in args:
            for i, service in args['kCBMsgArgServices'].iteritems():
                uuid = bytes(service['kCBMsgArgUUID'])
                start = service['kCBMsgArgServiceStartHandle']
                end = service['kCBMsgArgServiceEndHandle']

                self._discoveredServices.append({
                    'uuid': uuid,
                    'start': start,
                    'end': end
                })

        self.discover_event.set()

    def discover_characteristics(self, start, end):
        ble_base.mutex.acquire()
        discover_data = {
            'kCBMsgArgDeviceUUID': self.uuid,
            'kCBMsgArgServiceStartHandle': start,
            'kCBMsgArgServiceEndHandle': end,
            'kCBMsgArgUUIDs': []
        }

        self.discover_event.clear()
        ble_base.write(62, discover_data)

        ble_base.mutex.release()

        self.discover_event.wait()

        return self._discoveredCharacteristics

    def onDiscoverCharacteristics(self, args):
        chars = args['kCBMsgArgCharacteristics']

        self._discoveredCharacteristics = []

        for i, char in chars.iteritems():
            uuid = bytes(char['kCBMsgArgUUID'])
            handle = char['kCBMsgArgCharacteristicHandle']
            valueHandle = char['kCBMsgArgCharacteristicValueHandle']
            properties = char['kCBMsgArgCharacteristicProperties']

            self._discoveredCharacteristics.append({
                'uuid': uuid,
                'handle': handle,
                'value_handle': valueHandle,
                'properties': properties
            })

        self.discover_event.set()

    def discover_descriptors(self, characteristic, **kwargs):
        ble_base.mutex.acquire()
        discover_data = {
            'kCBMsgArgDeviceUUID': self.uuid,
            'kCBMsgArgCharacteristicHandle': characteristic.handle,
            'kCBMsgArgCharacteristicValueHandle': characteristic.value_handle
        }

        self.discover_desc_event.clear()
        ble_base.write(70, discover_data)

        ble_base.mutex.release()

        self.discover_desc_event.wait()

        return self._discoveredDescriptors

    def onDiscoverDescriptors(self, args):
        chars = args['kCBMsgArgDescriptors']

        self._discoveredDescriptors = []

        for i, char in chars.iteritems():
            uuid = bytes(char['kCBMsgArgUUID'])
            handle = char['kCBMsgArgDescriptorHandle']

            self._discoveredDescriptors.append({
                'uuid': uuid,
                'handle': handle
            })

        self.discover_desc_event.set()

    def read_by_handle(self, attribute, **kwargs):
        from bleep import GATTCharacteristic, GATTDescriptor
        self.read_data = None

        if isinstance(attribute, GATTCharacteristic):
            msg_id = 65
            read_data = {
                'kCBMsgArgDeviceUUID': self.uuid,
                'kCBMsgArgCharacteristicHandle': characteristic.handle,
                'kCBMsgArgCharacteristicValueHandle': characteristic.value_handle
            }
        elif isinstance(attribute, GATTDescriptor):
            # descriptor
            msg_id = 77
            read_data = {
                'kCBMsgArgDeviceUUID': self.uuid,
                'kCBMsgArgDescriptorHandle': attribute.value_handle
            }
        else:
            raise ValueError("invalid attribute")

        self.read_event.clear()
        ble_base.write(msg_id, read_data)
        self.read_event.wait()

        return self.read_data

    def onReadResponse(self, args):
        print("Received response!")
        data = args['kCBMsgArgData']

        if 'kCBMsgArgIsNotification' in args and data['kCBMsgArgIsNotification'] == 1:
            # this is actually a notification!
            self.on_notification(handle, data)

            # perhaps there shouldn't be a separate indication handler...
        else:
            # this is a boring old read
            self.read_data = data
            self.read_event.set()

    def _write_char_by_handle(self, data, handle, valueHandle, response):
        ble_base.mutex.acquire()
        print("Writing characteristic with handle %i" % handle)
        self.write_event.clear()

        write_data = {
            'kCBMsgArgDeviceUUID': self.uuid, 
            'kCBMsgArgCharacteristicHandle': handle,
            'kCBMsgArgCharacteristicValueHandle': valueHandle,
            'kCBMsgArgData': (data,),
            'kCBMsgArgType': 0 if response else 1
        }

        ble_base.write(66, write_data)
        ble_base.mutex.release()

        if response:
            self.write_event.wait()

    def _write_desc_by_handle(self, data, handle):
        print("Writing to descriptor with handle %i" % handle)
        ble_base.mutex.acquire()
        self.write_event.clear()

        write_data = {
            'kCBMsgArgDeviceUUID': self.uuid,
            'kCBMsgArgDescriptorHandle': handle,
            'kCBMsgArgData': (data,)
        }

        ble_base.write(77, write_data)
        ble_base.mutex.release()

        self.write_event.wait()

    def onWriteResponse(self, args):
        print("Received write response with args:")
        print(args)
        self.write_event.set()

    def write_by_handle(self, data, attribute, **kwargs):
        from bleep import GATTCharacteristic, GATTDescriptor

        if isinstance(attribute, GATTCharacteristic):
            self._write_char_by_handle(data, attribute.handle, attribute.value_handle, True)
        elif isinstance(attribute, GATTDescriptor):
            self._write_desc_by_handle(data, attribute.value_handle)
        else:
            raise ValueError("Invalid Attribute")

    def onNotifyEnabled(self, args):
        self.notify_enable_event.set()

    def enable_notify(self, characteristic):
        notify_data = {
            'kCBMsgArgDeviceUUID': self.uuid, 
            'kCBMsgArgCharacteristicHandle': characteristic.handle,
            'kCBMsgArgCharacteristicValueHandle': characteristic.value_handle,
            'kCBMsgArgState': 1
        }

        self.notify_enable_event.clear()
        ble_base.write(67, notify_data)
        self.notify_enable_event.wait()

    def write_without_response_by_handle(self, data, attribute, **kwargs):
        """Write without response to a handle: this is non-blocking"""
        from bleep import GATTCharacteristic, GATTDescriptor

        if isinstance(attribute, GATTCharacteristic):
            self._write_char_by_handle(data, attribute.handle, attribute.value_handle, False)
        else:
            raise ValueError("Invalid Attribute")
