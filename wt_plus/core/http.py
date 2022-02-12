import os
import re
from jinja2 import Template


class Http(object):

    def __init__(self, config):
        self.config = config

    def install(self):
        os.system(rf'mkdir -p {self.config.wt_config_path}/sites')
        os.system(rf'mkdir -p {self.config.wt_config_path}/log')
        os.system(rf'mkdir -p {self.config.wt_config_path}/config')
        os.system(r'sudo apt install -y apache2')
        os.system(r'sudo a2enmod ssl')
        os.system(r'sudo a2enmod actions fcgid alias proxy_fcgi')
        os.system(r'sudo a2enmod rewrite')
        os.system(r'sudo a2enmod headers')
        os.system(r'sudo a2enmod expires')
        os.system(r'sudo a2enmod include')
        os.system(r'sudo a2enmod proxy')
        os.system(r'sudo a2enmod proxy_http')
        os.system(r'sudo a2enmod proxy_wstunnel')

    def configure(self):
        self.install()

        # Add custom wt config home user
        config_wt = f'Timeout -1\n\nIncludeOptional {self.config.wt_config_path}/sites/*.conf\n'
        os.system(fr'sudo /bin/bash -c "echo \"{config_wt}\" > /etc/apache2/conf-available/wt.conf"')

        # Configuring envvars
        os.system(fr'sudo sed -i "s,^\(export APACHE_RUN_USER=\).*,\1{self.config.user},g" /etc/apache2/envvars')
        os.system(fr'sudo sed -i "s,^\(export APACHE_RUN_GROUP=\).*,\1{self.config.user},g" /etc/apache2/envvars')

        os.system(r"sudo sed -i 's/Listen 80/Listen 0.0.0.0:80/g' /etc/apache2/ports.conf")
        os.system(r"sudo sed -i 's/Listen 443/Listen 0.0.0.0:443/g' /etc/apache2/ports.conf")

        os.system('sudo a2enconf wt.conf')

        self.restart()

    def start(self):
        os.system('sudo systemctl start apache2')

    def stop(self):
        os.system('sudo systemctl stop apache2')

    def restart(self):
        os.system('sudo systemctl stop apache2 && sudo systemctl start apache2')

    def enable(self):
        os.system('sudo systemctl enable apache2')

    def disable(self):
        os.system('sudo systemctl disable apache2')

    def filter_proxies(self, proxies):
        proxies_pass = list()
        proxies_match = list()

        if proxies is not None:
            match_test = re.compile(r'.*[\[(^$].*')
            for _ in proxies:
                if match_test.match(_.split(' ')[0]):
                    proxies_match.append(_)
                else:
                    proxies_pass.append(_)

        return [proxies_pass, proxies_match]

    def dump_config(self):
        virtualhost_tpl = Template(open(self.config.wt_path + '/templates/apache/virtualhost.conf.jinja').read(),
                                   trim_blocks=True, lstrip_blocks=True)
        virtualhost_302_tpl = Template(
            open(self.config.wt_path + '/templates/apache/virtualhost-302.conf.jinja').read(), trim_blocks=True,
            lstrip_blocks=True)

        sites = self.config.get_config('sites')
        os.system(f'rm -rf {self.config.wt_config_path}/sites/*')

        for site in sites:
            site_config = sites.get(site)

            if site_config is None:
                continue

            path = site_config.get('path')
            public_path = site_config.get('public_path')
            custom = site_config.get('custom')
            aliases = site_config.get('alias')
            proxies = site_config.get('proxy')
            secure = site_config.get('secure')
            crt_path = f'{self.config.certificate_path}/{site}.crt'
            key_path = f'{self.config.certificate_path}/{site}.key'
            php_version = self.config.get_site_config('php/version', site)
            log_path = f'{self.config.wt_config_path}/log'

            if path is not None and not os.path.exists(path):
                continue

            server_name = f"{site}.test"
            if aliases is not None:
                aliases = ' '.join(aliases)

            proxies_pass, proxies_match = self.filter_proxies(proxies)

            public_html = str(path).rstrip('/')

            if public_path is not None:
                public_html += '/' + public_path

            virtualhost_tpl.stream(path='/var/www/html').dump(f'{self.config.wt_config_path}/sites/000-default.conf')
            virtualhost_tpl.stream(
                secure=True,
                path='/var/www/html',
                crt_path='/etc/ssl/certs/ssl-cert-snakeoil.pem',
                key_path='/etc/ssl/private/ssl-cert-snakeoil.key'
            ).dump(f'{self.config.wt_config_path}/sites/000-default-ssl.conf')

            if secure and os.path.exists(crt_path) and os.path.exists(key_path):
                virtualhost_302_tpl.stream(
                    server_name=server_name,
                    aliases=aliases).dump(f'{self.config.wt_config_path}/sites/{site}.conf')

                virtualhost_tpl.stream(
                    site_id=site,
                    log_path=log_path,
                    path=public_html,
                    server_name=server_name,
                    proxies_pass=proxies_pass,
                    proxies_match=proxies_match,
                    secure=secure,
                    crt_path=crt_path,
                    key_path=key_path,
                    custom=custom,
                    aliases=aliases,
                    php_version=php_version).dump(f'{self.config.wt_config_path}/sites/{site}-ssl.conf')
            else:
                virtualhost_tpl.stream(
                    site_id=site,
                    path=public_html,
                    log_path=log_path,
                    server_name=server_name,
                    proxies_pass=proxies_pass,
                    proxies_match=proxies_match,
                    custom=custom,
                    aliases=aliases,
                    php_version=php_version).dump(f'{self.config.wt_config_path}/sites/{site}.conf')
