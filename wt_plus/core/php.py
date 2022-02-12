import os
from jinja2 import Template
import subprocess


class Php(object):
    def __init__(self, config):
        self.config = config
        self.site = None

    def configure(self):
        if not os.path.exists('/etc/apt/sources.list.d/ondrej-ubuntu-php-focal.list'):
            subprocess.run(['sudo apt install -y software-properties-common'], shell=True, executable='/bin/bash')
            subprocess.run(['sudo add-apt-repository -y ppa:ondrej/php'], shell=True, executable='/bin/bash')
            subprocess.run(['sudo apt update -y'], shell=True, executable='/bin/bash')

        cmd = 'sudo apt install -y php{5.6,7.1,7.2,7.3,7.4,8.0}-{common,gmp,curl,soap,bcmath,intl,mbstring,xmlrpc,mysql,gd,xml,cli,zip,dev,ldap,fpm,imap,apcu,imagick,mcrypt,yaml,oauth,xdebug}'
        subprocess.run([cmd], shell=True, executable='/bin/bash')

        subprocess.run(['sudo apt install -y composer'], shell=True, executable='/bin/bash')

        for version in self.versions():
            pool_path = f'{self.config.wt_config_path}/fpm/{version}/pool.d'

            if not os.path.exists(pool_path):
                cmd = f'mkdir -p {pool_path}'
                os.system(cmd)

            create = f'[ $(grep -c "include={pool_path}/\*.conf" /etc/php/{version}/fpm/php-fpm.conf) == "0" ] && echo "\ninclude={pool_path}/*.conf" >> /etc/php/{version}/fpm/php-fpm.conf'
            os.system(f'sudo /bin/bash -c \'{create}\'')
            os.system(f'echo "sendmail_path=/usr/local/bin/mhsendmail\n" | sudo tee /etc/php/{version}/mods-available/mailhog.ini')

        os.system('sudo phpenmod mailhog')
        os.system('sudo phpdismod -s cli xdebug')

    def start_all(self):
        for version in self.versions():
            self.service('start', version)

    def stop_all(self):
        for version in self.versions():
            self.service('stop', version)

    def restart_all(self):
        for version in self.versions():
            self.restart(version)

    def disable_all(self):
        for version in self.versions():
            self.disable(version)

    def enable_all(self):
        for version in self.versions():
            self.enable(version)

    def restart(self, version):
        self.service('restart', version)

    def enable(self, version):
        self.service('enable', version)

    def disable(self, version):
        self.service('disable', version)

    def service(self, option, php_version):
        os.system(f'sudo systemctl {option} php{php_version}-fpm.service')

    def versions(self):
        return ['5.6', '7.1', '7.2', '7.3', '7.4', '8.0']

    def cli_version(self, version):
        cmd = [
            "sudo update-alternatives --set php /usr/bin/php{version}",
            "sudo update-alternatives --set phar /usr/bin/phar{version}",
            "sudo update-alternatives --set phar.phar /usr/bin/phar.phar{version}",
            "sudo update-alternatives --set phpize /usr/bin/phpize{version}",
            "sudo update-alternatives --set php-config /usr/bin/php-config{version}"
        ]

        os.system(' && '.join(cmd).format(version=version))

    def current_version(self, site_id):
        return self.config.get('sites').get(site_id).get('php').get('version')

    def xdebug(self, status, remote_autostart, sapi_name, php_version, current_site_id):
        if php_version is None:
            php_version = self.current_version(current_site_id)

        self.phpmod('xdebug', status, sapi_name, php_version)

        self.restart(php_version)

    def phpmod(self, mod, status, sapi_name, php_version):
        if php_version is None:
            php_version = self.current_version(self.config.current_site_id)

        if status == 'on':
            os.system(f'sudo phpenmod -v {php_version} -s {sapi_name} {mod}')
        elif status == 'off':
            os.system(f'sudo phpdismod -v {php_version} -s {sapi_name} {mod}')

        self.restart(php_version)

    def parser_config(self, site_id):
        pool_template = Template(open(f'{self.config.wt_path}/templates/php/pool.conf.jinja').read())

        site = self.config.get('sites').get(site_id)

        if site is None:
            return

        php_config = site.get('php')
        user = self.config.user

        if not php_config:
            return

        php_version = php_config.get('version')

        php_flag = php_config.get('php_flag')
        php_flag = dict(php_flag) if php_flag else dict()
        if 'display_errors' not in php_flag:
            php_flag['display_errors'] = 'on'

        php_admin_value = php_config.get('php_admin_value')
        php_admin_value = dict(php_admin_value) if php_admin_value else dict()
        php_admin_value['error_log'] = f'{self.config.wt_config_path}/log/{site_id}-fpm-php.log'
        if 'xdebug.mode' not in php_admin_value:
            php_admin_value['xdebug.mode'] = 'debug'
        if 'xdebug.remote_enable' not in php_admin_value:
            php_admin_value['xdebug.remote_enable'] = True

        pool_template.stream(
            site_id=site_id,
            user=user,
            php_version=php_version,
            php_flag=php_flag,
            php_admin_value=php_admin_value).dump(f'{self.config.wt_config_path}/fpm/{php_version}/pool.d/{site_id}.conf')

    def dump_config(self):
        os.system(f'find {self.config.wt_config_path}/fpm/ -name "*.conf" -delete')

        for site_id in self.config.get('sites'):
            self.parser_config(site_id)

    def php_versions(self, ctx, args, incomplete):
        versions = ['5.6', '7.1', '7.2', '7.3', '7.4', '8.0']
        return [k for k in versions if incomplete in k]
