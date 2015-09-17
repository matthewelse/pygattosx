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
from threading import Event, Lock
from collections import deque

from xpcconnection import XpcConnection

class BLEBase(XpcConnection):
    def __init__(self, device=None):
        super(BLEBase, self).__init__('com.apple.blued')

        self._events = {}

        self.events = deque([])
        self.event_happening = False

        self.mutex = Lock()

        self.registerEvent(6, self.adapterStateChanged)
        self.readyEvent = Event()

        self.init()

    def write(self, id, args):
        message = {
            'kCBMsgId': id,
            'kCBMsgArgs': args
        }

        self.sendMessage(message)

    def init(self):
        # init
        init_data = {
            'kCBMsgArgName': 'py-' + str(time.time()),
            'kCBMsgArgOptions': {
                'kCBInitOptionShowPowerAlert': 0
            },
            'kCBMsgArgType': 0
        }

        self.write(1, init_data)

        self.readyEvent.wait()

    def registerEvent(self, id, func):
        self._events[id] = func

    def onEvent(self, data):
        msg_id = data['kCBMsgId']
        args = data['kCBMsgArgs']

        self.schedule(msg_id, None if msg_id not in self._events else self._events[msg_id], args)
    
    def schedule(self, msg_id, event, args):
        self.events.append((msg_id, event, args))

        if not self.event_happening:
            self.mutex.acquire()

            for i in range(len(self.events)):
                msg_id, event, args = self.events.popleft()

                if event is not None:
                    event(args)
                else:
                    print("No scheduled event for kCBMsgId%i" % msg_id)

            self.mutex.release()

    def adapterStateChanged(self, args):
        # state changed
        STATE_TYPES = ['unknown', 'resetting', 'unsupported', 'unauthorized', 'poweredOff', 'poweredOn']

        if STATE_TYPES[args['kCBMsgArgState']] != 'poweredOn':
            raise RuntimeError("Bluetooth Device Unavailable")
        else:
            self.readyEvent.set()
            
    def onError(self, data):
        pass

    def handler(self, event):
        e_type, data = event

        if e_type == 'event':
            self.onEvent(data)
        elif e_type == 'error':
            self.onError(data)
        else:
            # que?
            pass

ble_base = BLEBase()
