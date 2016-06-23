import ConfigParser
from libmproxy import platform
from libmproxy.proxy.config import ProxyConfig
from netlib import http_auth, http
import os, sys, re

TRANSPARENT_SSL_PORTS = [443, 8443]
PROXY_OPTIONS = "ProxyOptions"
CONFIG_KEYS = {
    "addr": str,
    "ignore_hosts": list,
    "tcp_hosts": list,
    "port": int,
    "ssl_ports": list,
    "regular_proxy": bool,
    "reverse_proxy": bool,
    "socks_proxy": bool,
    "transparent_proxy": bool,
    "upstream_proxy": bool,
    "upstream_server": str,
    "certs": list,
    "clientcerts": str,
    "ciphers": str,
    "certforward": bool,
    "no_upstream_cert": bool,
    "confdir": str,
    "auth_nonanonymous": bool,
    "requires_singleuser": bool,
    "auth_singleuser": str,
    "requires_htpasswd": bool,
    "auth_htpasswd": str
}


def resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)

        return os.path.join(os.path.abspath("."), relative_path)


class Config(object):
        def __init__(self):
            self.__dict__ = {
                "addr": '',
                "ignore_hosts": [],
                "tcp_hosts": [],
                "port": 1025,
                "regular_proxy": True,
                "reverse_proxy": False,
                "socks_proxy": False,
                "transparent_proxy": False,
                "upstream_proxy": False,
                "upstream_server": None,
                "certs": [],
                "clientcerts": None,
                "ciphers":None,
                "certforward": False,
                "no_upstream_cert": False,
                "confdir": resource_path('mitmproxy'),
                "ssl_ports": list(TRANSPARENT_SSL_PORTS),
                "auth_nonanonymous": False,
                "requires_singleuser": False,
                "auth_singleuser": None,
                "requires_htpasswd": False,
                "auth_htpasswd": None
            }

        def update(self, adict):
            self.__dict__.update(adict)

        def __getattr__(self, item):
            if not item in self.__dict__:
                return None
            return object.__getattribute__(self, item)

        def __getitem__(self, item):
            if not item in self.__dict__:
                return None
            return object.__getattribute__(self, item)


class Singleton:
    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


@Singleton
class AppConfig:
    proxy_config = None
    config = Config()

    def parseConfig(self, section):
        configParser = ConfigParser.SafeConfigParser()
        if not os.path.isfile(resource_path('config.ini')):
            return {}
        configParser.read(resource_path('config.ini'))
        config = configParser._sections[section]
        for key in CONFIG_KEYS.keys():
            if key in config.keys():
                if CONFIG_KEYS[key] is list:
                    config[key] = [i.strip() for i in config[key].split(',')]
                if CONFIG_KEYS[key] is bool:
                    config[key] = config[key] in ['True', 'true']
                if CONFIG_KEYS[key] is str and config[key] in ['None', 'none']:
                    config[key] = None
        return config

    def writeConfig(self, section, config):
        configParser = ConfigParser.SafeConfigParser()
        if not os.path.isfile(resource_path('config.ini')):
            return {}
        configParser.read(resource_path('config.ini'))
        for key in config.keys():
            value = config[key]
            if type(value) is list:
                value = ', '.join(str(i) for i in value)
            configParser.set(section, key, str(value))
        with open(resource_path('config.ini'), 'wb') as configfile:
            configParser.write(configfile)


    def getProxyConfig(self):
        if not self.proxy_config:
            config = self.parseConfig(PROXY_OPTIONS)
            self.config.update(config)
            self.proxy_config = self.parse_proxy_options(self.config)
        return self.proxy_config

    def getConfig(self):
        return self.config

    def updateConfig(self, newConfig):
        self.config.update(newConfig)
        proxyModes = {
            "regular_proxy": False,
            "reverse_proxy": False,
            "socks_proxy": False,
            "transparent_proxy": False,
            "upstream_proxy": False,
        }
        for key in proxyModes.keys():
            if key in newConfig.keys():
                proxyModes[key] = newConfig[key]
            else:
                newConfig[key] = proxyModes[key]
        self.config.update(proxyModes)
        proxy_config = self.parse_proxy_options(self.config)
        self.proxy_config = proxy_config
        self.writeConfig(PROXY_OPTIONS, newConfig)

    def parse_proxy_options(self, options):
        c = 0
        mode, upstream_server = None, None
        if options.transparent_proxy:
            c += 1
            if not platform.resolver:
                error("Transparent mode not supported on this platform.")
            mode = "transparent"
        if options.socks_proxy:
            c += 1
            mode = "socks5"
        if options.reverse_proxy:
            c += 1
            mode = "reverse"
            upstream_server = parse_server_spec(options.upstream_server)
        if options.upstream_proxy:
            c += 1
            mode = "upstream"
            upstream_server = parse_server_spec(options.upstream_server)
        if c > 1:
            error("Transparent, SOCKS5, reverse and upstream proxy mode are mutually exclusive.")

        if options.clientcerts:
            options.clientcerts = os.path.expanduser(options.clientcerts)
            if not os.path.exists(options.clientcerts) or not os.path.isdir(options.clientcerts):
                error("Client certificate directory does not exist or is not a directory: %s" % options.clientcerts)

        if (options.auth_nonanonymous or options.requires_singleuser or options.requires_htpasswd):
            if options.requires_singleuser and options.auth_singleuser:
                if len(options.auth_singleuser.split(':')) != 2:
                    error("Invalid single-user specification. Please use the format username:password")
                username, password = options.auth_singleuser.split(':')
                password_manager = http_auth.PassManSingleUser(username, password)
            elif options.auth_nonanonymous:
                password_manager = http_auth.PassManNonAnon()
            elif options.requires_htpasswd and options.auth_htpasswd:
                try:
                    password_manager = http_auth.PassManHtpasswd(options.auth_htpasswd)
                except ValueError, v:
                    error(v.message)
            authenticator = http_auth.BasicProxyAuth(password_manager, "mitmproxy")
        else:
            authenticator = http_auth.NullProxyAuth(None)

        certs = []
        for i in options.certs:
            parts = i.split("=", 1)
            if len(parts) == 1:
                parts = ["*", parts[0]]
            parts[1] = os.path.expanduser(parts[1])
            if not os.path.exists(parts[1]):
                error("Certificate file does not exist: %s" % parts[1])
            certs.append(parts)

        ssl_ports = options.ssl_ports
        if options.ssl_ports != TRANSPARENT_SSL_PORTS:
            ssl_ports = ssl_ports[len(TRANSPARENT_SSL_PORTS):]
        ssl_ports = [int(i) for i in ssl_ports]

        return ProxyConfig(
            host=options.addr,
            port=int(options.port),
            confdir=options.confdir,
            clientcerts=options.clientcerts,
            no_upstream_cert=options.no_upstream_cert,
            mode=mode,
            upstream_server=upstream_server,
            ignore_hosts=options.ignore_hosts,
            tcp_hosts=options.tcp_hosts,
            authenticator=authenticator,
            ciphers=options.ciphers,
            certs=certs,
            certforward=options.certforward,
            ssl_ports=ssl_ports
        )


def parse_server_spec(url):
    normalized_url = re.sub("^https?2", "", url)

    p = http.parse_url(normalized_url)
    if not p or not p[1]:
        raise ValueError("Invalid server specification: %s" % url)

    if url.lower().startswith("https2http"):
        ssl = [True, False]
    elif url.lower().startswith("http2https"):
        ssl = [False, True]
    elif url.lower().startswith("https"):
        ssl = [True, True]
    else:
        ssl = [False, False]

    return ssl + list(p[1:3])


def error(msg):
    raise ValueError(msg)
