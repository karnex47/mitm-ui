# mitm-ui
A GUI implemented with PyQt4 for libmproxy. It does not have all the features of mitmproxy. I built it with fiddler web debugger in mind. The auto responder of fiddler helped me a lot when web developing. Since I didn't find anything thats fiddler-like on OSX, I decided to build one. I made this for my own personal use, but improvement is always welcome.

# Developement
requirements:
libmproxy, PyQt4/sip

I have setup a virtual env for those to libraires and commited them (since PyQy4 cannot be installed through pip, and no idea where I downloaded the libmproxy from[probably bower]. But doing pip install mitmproxy and changing the name to libmproxy should work), Will remove them later

# Build
Have a setup.py and build.sh to be used for py2app. Currently the deployment build is breaking with "Abort trap: 6", but that maybe just my system.
