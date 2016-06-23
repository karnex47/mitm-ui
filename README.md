# mitm-ui
A GUI implemented with PyQt5 for libmproxy. It does not have all the features of mitmproxy. I built it with fiddler web debugger in mind. The auto responder of fiddler helped me a lot when web developing. Since I didn't find anything thats fiddler-like on OSX, I decided to build one. I made this for my own personal use, but improvement is always welcome.

# Developement
requirements:
libmproxy, PyQt5/sip

I have no idea where I downloaded the libmproxy from[probably got installed with tamper]. But doing pip install mitmproxy and changing the name to libmproxy should work)

# Build
Run build.sh to build the application using pyinstaller
