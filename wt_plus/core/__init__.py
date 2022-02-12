from .http import Http
from .php import Php
from .magento2 import Magento2
from .host import Host
from .config import Config
from .mailhog import MailHog
from .redis import Redis
from .rabbitmq import Rabbitmq
from .site import Site, SiteExistsError, SiteNotExistsError, ProxyExistsError, ProxyNotExistsError
from .db import Db, DbExistsError, DbNotExistsError, SqlFileNotExistsError


db = Db()
config = Config()
redis = Redis()
_host = Host(config)
_php = Php(config)
_http = Http(config)
_magento2 = Magento2()
site = Site(config, _host, _http, _php, db, _magento2)
mailhog = MailHog(config, site)
rabbitmq = Rabbitmq()
