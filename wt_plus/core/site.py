import os
import json
import re
import unidecode

from jinja2 import Template


class SiteExistsError(TypeError):
    pass


class SiteNotExistsError(TypeError):
    pass


class ProxyExistsError(TypeError):
    pass


class ProxyNotExistsError(TypeError):
    pass


class Site:
    MSG_SITE_EXISTS = "{site_id} site already exists! 😖"
    MSG_SITE_NOT_EXISTS = "Site '{site_id}' não existe! 😖"
    MSG_PROXY_EXISTS = "{proxy} proxy already exists! 😖"

    # TODO: fix orrible design
    def __init__(self, config, host, http, php, db, magento2):
        self.config = config
        self.db = db
        self.http = http
        self.php = php

        self.magento2 = magento2
        self.magento2.site = self
        self.magento2.php = php
        self.magento2.config = config
        self.magento2.db = db

        self.host = host

        self.ca_path = f'{self.config.wt_config_path}/ca-certificates'
        self.ca_crt_path = f'{self.ca_path}/WtEnvCASelfSigned.crt'
        self.ca_key_path = f'{self.ca_path}/WtEnvCASelfSigned.key'
        self.ca_srl_path = f'{self.ca_path}/WtEnvCASelfSigned.srl'
        self.cert_path = f'{self.config.wt_config_path}/certificates'

    def install(self):
        os.system(r'sudo apt install libnss3-tools')

    def configure(self):
        self.install()

    @property
    def default_site_id(self):
        default_site_id = os.path.basename(os.path.splitext(os.getcwd())[0][1:])
        default_site_id = unidecode.unidecode(default_site_id).lower()
        default_site_id = re.sub(r'[\W_]+', '-', default_site_id)

        return default_site_id

    @property
    def current_site_id(self):
        current_site_id = self.find_site_id_by_path(os.path.splitext(os.getcwd())[0])

        return current_site_id

    def find_site_by_id(self, site_id):
        if not self.is_site_exists(site_id):
            raise SiteNotExistsError(self.MSG_SITE_NOT_EXISTS.format(site_id=site_id))

        return self.config.get('sites').get(site_id)

    def find_site_id_by_path(self, path):
        sites = self.sites()

        site_id = None
        path = path.rstrip('/')

        for site in sites:
            site_path = self.config.get('sites').get(site).get('path')

            if site_path is None:
                continue

            site_path = site_path.rstrip('/')

            if site_path == path:
                site_id = site

        if site_id is None:
            path = os.path.dirname(path)

            if path == '':
                return None

            return self.find_site_id_by_path(path)

        return site_id

    def site_path(self):
        vhost = self.config.get('sites').get(self.current_site_id)

        if vhost is False:
            raise SiteNotExistsError(self.MSG_SITE_NOT_EXISTS.format(site_id=self.current_site_id))

        return vhost.get('path').rstrip('/')

    def is_site_exists(self, site_id) -> bool:
        if self.config.get('sites').get(site_id):
            return True

        return False

    def sites(self):
        sites_config = self.config.get('sites')
        sites = list()

        for site in sites_config:
            sites.append(site)

        return sites

    def use(self, version, site_id, update_cli=None):
        if update_cli:
            self.php.cli_version(version)

        self.config.set_site_config('php/version', version, site_id)

    def add(self, site_id, framework, unsecure):
        if self.is_site_exists(site_id):
            raise SiteExistsError(self.MSG_SITE_EXISTS.format(site_id=site_id))

        php_version = self.config.get_config('php/version') or 7.3
        public_path = None

        self.config.set_site_config('path',  os.getcwd() + "/", site_id)
        self.config.set_site_config('php', {"version": php_version}, site_id)

        if framework is not None:
            self.config.set_site_config('framework', framework, site_id)

            if framework == 'magento2':
                public_path = 'pub'

        if public_path is not None:
            self.config.set_site_config('public_path', public_path, site_id)

        if not unsecure:
            self.secure(site_id)

    def remove(self, site_id):
        if not self.is_site_exists(site_id):
            raise SiteNotExistsError(self.MSG_SITE_NOT_EXISTS.format(site_id=site_id))

        secure = self.config.get_site_config('secure', site_id)
        if not secure:
            self.unsecure(site_id)

        self.config.get('sites').pop(site_id, None)

    def add_alias(self, site_id, name):
        if not self.is_site_exists(site_id):
            raise SiteNotExistsError(self.MSG_SITE_NOT_EXISTS.format(site_id=site_id))

        for site in self.sites():
            aliases = self.config.get('sites').get(site).get('alias')

            if aliases is None:
                continue

            for alias in aliases:
                if alias == name:
                    aliases.remove(name)

        alias = self.config.get('sites').get(site_id).get('alias')
        if alias is None:
            alias = self.config.get('sites').get(site_id)['alias'] = list()

        alias.append(name)

    def del_alias(self, site_id, name):
        if not self.is_site_exists(site_id):
            raise SiteNotExistsError(self.MSG_SITE_NOT_EXISTS.format(site_id=site_id))

        aliases = self.config.get('sites').get(site_id).get('alias')

        if aliases is not None:
            for alias in aliases:
                if alias == name:
                    aliases.remove(name)

    def add_proxy(self, site_id, origin, target):
        if self.is_site_exists(site_id):
            site = self.find_site_by_id(site_id)
        else:
            site = self.config.get('sites')[site_id] = dict()

        proxies = site.get('proxy')

        if proxies is None:
            proxies = site['proxy'] = list()

        for proxy in proxies:
            if proxy.split(' ')[0] == origin:
                raise ProxyExistsError(self.MSG_PROXY_EXISTS.format(proxy=proxy))

        proxies.append(f'{origin} {target}')

    def rm_proxy(self, site_id, origin):
        site = self.find_site_by_id(site_id)

        proxies = site.get('proxy')

        if proxies is None:
            return

        _ = list()
        for proxy in proxies:
            if proxy.split(' ')[0] != origin:
                _.append(proxy)

        if _:
            site['proxy'] = _
        else:
            site.pop('proxy', None)

    def _create_ca(self):
        if os.path.exists(self.ca_crt_path) and os.path.exists(self.ca_key_path):
            return

        if not os.path.exists(self.ca_path):
            os.system(f'mkdir -p {self.ca_path}')

        o_name = 'Wt Env CA Self Signed Organization'
        c_name = 'Wt Env CA Self Signed CN'
        email = 'rootcertificate@wt_plus.test'

        cmd = f'openssl req -new -newkey rsa:2048 -days 730 -nodes -x509' \
              f' -subj "/C=/ST=/O={o_name}/localityName=/commonName={c_name}/organizationalUnitName=Developers/emailAddress={email}/"' \
              f' -keyout "{self.ca_key_path}" -out "{self.ca_crt_path}"'
        os.system(cmd)

        self._trust_ca()

    def _trust_ca(self):
        cmd = f'certutil -d sql:$HOME/.pki/nssdb -D -n "WtEnvCAcert.org"'
        os.system(cmd)

        cmd = f'certutil -d sql:$HOME/.pki/nssdb -A -t TC -n "WtEnvCAcert.org" -i {self.ca_crt_path}'
        os.system(cmd)

        cmd = f'sudo ln -sf {self.ca_crt_path} /usr/local/share/ca-certificates/WtEnvCASelfSigned.crt'
        os.system(cmd)

        mozilla_policy = {
            "policies": {
                "Certificates": {
                    "Install": [
                        "/usr/local/share/ca-certificates/WtEnvCASelfSigned.crt"
                    ]
                }
            }
        }

        os.system('sudo mkdir -p /usr/lib/firefox/distribution')
        os.system('sudo rm /usr/lib/firefox/distribution/policies.json')
        os.system(f"sudo bash -c 'echo {json.dumps(json.dumps(mozilla_policy))} > /usr/lib/firefox/distribution/policies.json'")

        cmd = 'sudo update-ca-certificates --fresh'
        os.system(cmd)

    def secure(self, site_id):
        self._create_ca()

        if not self.is_site_exists(site_id):
            raise SiteNotExistsError(self.MSG_SITE_NOT_EXISTS.format(site_id=site_id))

        aliases = self.config.get('sites').get(site_id).get('alias')

        domains = list()
        domains.append(f'{site_id}.test')
        domains.append(f'*.{site_id}.test')

        if aliases is not None:
            for alias in aliases:
                domain = ".".join(alias.split('.')[-2:])
                if domain not in domains:
                    domains.append(domain)
                    domains.append(f'*.{domain}')

        url = f'{site_id}.test'

        if not os.path.exists(self.cert_path):
            os.system(f'mkdir -p {self.cert_path}')

        key_path = f'{self.cert_path}/{site_id}.key'
        csr_path = f'{self.cert_path}/{site_id}.csr'
        crt_path = f'{self.cert_path}/{site_id}.crt'
        conf_path = f'{self.cert_path}/{site_id}.conf'

        openssl_template = Template(open(self.config.wt_path + '/templates/openssl.conf.jinja').read(),
                                    trim_blocks=True, lstrip_blocks=True)
        openssl_template.stream(site=site_id, domains=enumerate(domains)).dump(conf_path)

        # Generate private key
        cmd = f'openssl genrsa -out "{key_path}" 2048'
        os.system(cmd)

        # Create signin request
        cmd = f'openssl req -new -key {key_path} -out {csr_path} -subj "/C=/ST=/O=/localityName=/commonName=*.{url}/organizationalUnitName=/emailAddress=/" -config {conf_path} -passin pass:'
        os.system(cmd)

        ca_srl_param = f'-CAserial "{self.ca_srl_path}"'

        if not os.path.exists(self.ca_srl_path):
            ca_srl_param += ' -CAcreateserial'

        cmd = f'openssl x509 -req -sha256 -days 730 -CA "{self.ca_crt_path}" -CAkey "{self.ca_key_path}" {ca_srl_param} -in "{csr_path}" -out "{crt_path}" -extensions v3_req -extfile "{conf_path}"'
        os.system(cmd)

        self.config.get('sites').get(site_id)['secure'] = True

        framework = self.config.get('sites').get(site_id).get('framework')

        if framework == 'magento2' and self.magento2.version is not None:
            self.magento2.dev_config()

        self.config.set_site_config('secure', True, site_id)

    def unsecure(self, site_id):
        if not self.is_site_exists(site_id):
            raise SiteNotExistsError(self.MSG_SITE_NOT_EXISTS.format(site_id=site_id))

        self.config.get('sites').get(site_id).pop('secure', None)
        os.system(f'find {self.cert_path} -name "{site_id}.test*" -type f -delete')

        framework = self.config.get('sites').get(site_id).get('framework')

        if framework == 'magento2':
            self.magento2.dev_config()

    def dump_config(self):
        self.config.save()
        self.php.dump_config()
        self.http.dump_config()
        self.host.dump_config()
        self.php.restart_all()
        self.http.restart()

    def aliases_complete(self, ctx, args, incomplete):
        aliases = self.config.get('sites').get(self.current_site_id).get('alias')
        if aliases is None:
            aliases = list()

        return [k for k in aliases if incomplete in k]

    def sites_complete(self, ctx, args, incomplete):
        sites = self.sites()
        return [k for k in sites if incomplete in k]
