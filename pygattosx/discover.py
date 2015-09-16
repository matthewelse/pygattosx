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

import time

from uuid import UUID
from collections import defaultdict

from .wrapper import ble_base

class DiscoveryService():
    def __init__(self, device=None):
        ble_base.registerEvent(37, self.discoveredDevice)

        default_dict = {
            'name': '(unknown)',
            'uuids': [],
            'flags': 0,
            'appearance': 0
        }

        self.discovered_devices = defaultdict(lambda: default_dict.copy())

    def discoveredDevice(self, args):
        # discovered a device
        args_ = defaultdict()
        args_.update(args)
        args = args_

        rssi = args['kCBMsgArgRssi'] or 0
        uuid = UUID(bytes=args['kCBMsgArgDeviceUUID'])
        ads = args['kCBMsgArgAdvertisementData'] or {}

        ad_data = defaultdict(lambda: None)
        ad_data.update(ads)

        name = ad_data['kCBAdvDataLocalName'] or ad_data['kCBMsgArgName']
        uuids = ad_data['kCBAdvDataServiceUUIDs']

        device = {
            'name': name,
            'uuids': uuids,
            'flags': 0,
            'appearance': 0
        }

        self.discovered_devices[uuid].update({k: v for k, v in device.items() if v is not None})

    def startScanning(self):
        scan_data = {
            'kCBMsgArgOptions': {
                'kCBScanOptionAllowDuplicates': 1
            },
            'kCBMsgArgUUIDs': []
        }

        ble_base.write(29, scan_data)

    def stopScanning(self):
        ble_base.write(30, None)

    def discover(self, timeout):
        self.startScanning()

        time.sleep(timeout)

        self.stopScanning()

        return dict(self.discovered_devices)
