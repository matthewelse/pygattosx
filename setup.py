"""
 pygattosx: BLE GATT Library for Mac OS X

 Copyright (c) 2015 Matthew Else

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from setuptools import setup, find_packages

def check_system(systems, message):
    import sys
    if sys.platform in systems:
        return
    print(message)
    sys.exit(1)

OTHER_OS_MESSAGE = """
        *****************************************************
        *         pygattosx only works on Mac OS X          *
        *                                                   *
        *    if you're using Linux, then try pygattlib      *
        * instead: https://github.com/matthewelse/pygattlib *
        *                                                   *
        *  if you're using Windows, then raise an issue at  *
        *  https://github.com/matthewelse/bleep suggesting  *
        *            that I add Windows support.            *
        *****************************************************
    """

# check that this is being installed on Mac OS X.
check_system(['darwin'], OTHER_OS_MESSAGE)

setup(
    name = "pygattosx",
    version = "0.0.1",
    author = "Matthew Else",
    author_email = "matthew.else@arm.com",
    description = "Python GATT Library for Mac OSX",
    license = "Apache-2.0",
    keywords = "ble",
    url = "about:blank",
    packages = find_packages(),
    install_requires = [
        'future',
        'pyxpcconnection'
    ],
    dependency_links = ['https://github.com/matthewelse/pyxpcconnection/archive/master.zip#egg=xpcconnection']
)
