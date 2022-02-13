import os
import re
import subprocess
import json
from packaging import version as packaging_version


class Magento2(object):
    def __init__(self):
        self.site = None
        self.config = None
        self.db = None
        self._version = None
        self.versions = ['2.4.3', '2.4.2-p2', '2.4.2-p1', '2.4.2', '2.4.1-p1', '2.4.1', '2.4.0-p1', '2.4.0',
                         '2.3.7-p1', '2.3.7', '2.3.6-p1', '2.3.6', '2.3.5-p2', '2.3.5-p1', '2.3.5', '2.3.4-p2',
                         '2.3.4', '2.3.3-p1', '2.3.3', '2.3.2-p2', '2.3.2', '2.3.1', '2.3.0']

    @property
    def version(self):
        if self._version is not None:
            return self._version

        magento2_base_composer = rf'{self.site.site_path()}/vendor/magento/magento2-base/composer.json'

        if not os.path.isfile(magento2_base_composer):
            return None

        with open(magento2_base_composer) as jsonFile:
            json_object = json.load(jsonFile)
            jsonFile.close()

        self._version = json_object['version']

        return self._version

    def magento(self, cmd):
        os.system(f'{self.site.site_path()}/bin/magento {cmd}')

    def twofactorauth(self, user, secret):
        self.magento('config:set twofactorauth/general/force_providers google')
        self.magento('config:set twofactorauth/google/otp_window 60')
        self.magento(f'security:tfa:google:set-secret {user} {secret}')

    def config_set(self, path, value, options=''):
        self.magento(f'config:set {path} "{value}" {options}')

    def install_sample_data(self):
        self.magento('sampledata:deploy')
        self.magento('setup:upgrade')

    def clean_static(self):
        subprocess.check_output(['rm -rf var/view_preprocessed'], shell=True)
        subprocess.check_output(['find pub/static -maxdepth 1 -mindepth 1 ! '
                                 '-name ".htaccess" -exec rm -rf {} +'], shell=True)
        self.magento('cache:clean full_page block_html')

    def dev_config(self):
        self.magento('app:config:import')

        self.clean_token_request_log()

        self.config_set('admin/security/password_lifetime', '0')
        self.config_set('admin/security/password_is_forced', '0')

        self.config_set('admin/url/custom_path', 'admin', '--lock-env')
        self.config_set('admin/url/use_custom', '0', '--lock-env')

        if self.config.get('sites').get(self.site.current_site_id).get('secure'):
            self.config_set('web/secure/use_in_frontend', '1')
            self.config_set('web/secure/use_in_adminhtml', '1')
        else:
            self.config_set('web/secure/use_in_frontend', '0')
            self.config_set('web/secure/use_in_adminhtml', '0')

        self.config_set('admin/security/use_form_key', '0')

        self.config_set('admin/security/session_lifetime', '31536000')

        self.config_set('web/cookie/cookie_domain', '')
        self.config_set('web/cookie/cookie_path', '')

        self.config_set('admin/captcha/enable', '0')
        self.config_set('customer/captcha/enable', '0')

        self.config_set('dev/debug/template_hints_storefront', '1')
        self.config_set('dev/debug/template_hints_storefront_show_with_parameter', '1')

        self.config_set('web/seo/use_rewrites', '1')

        self.config_set('google/analytics/active', '0')

        self.config_set('system/full_page_cache/caching_application', '1')

        self.config_set('sales_email/general/async_sending', '0')
        self.config_set('dev/grid/async_indexing', '0')

        self.magento('deploy:mode:set developer')
        self.magento('cache:disable full_page block_html')

        self.magento('app:config:import')

        if os.path.isfile('./vendor/bin/ece-patches'):
            os.system('php ./vendor/bin/ece-patches apply')

        self.magento('cache:clean')

    def change_base_url(self, src, dist, db_name):
        with self.db.db_connect:
            with self.db.db_connect.cursor() as cur:
                cur.execute(f'SELECT * FROM {db_name}.core_config_data WHERE '
                            f'path like "%base_url" OR path like "%base_link_url"')
                result = cur.fetchall()

                sql_update = f"UPDATE {db_name}.core_config_data SET value = %s WHERE config_id = %s"

                for base_url in result:
                    config_id = base_url['config_id']
                    new_url = base_url['value'].replace(src, dist)

                    if re.search("/secure/", base_url['path']):
                        new_url = new_url.replace('http://', 'https://')
                    else:
                        new_url = new_url.replace('https://', 'http://')

                    cur.execute(sql_update, (new_url, config_id))

                self.db.db_connect.commit()

    def token(self, admin_user="admin"):
        os.system(f'oathtool --base32 --totp $(php {self.config.wt_path}/scripts/magento/taf-secret-token.php '
                  f'{admin_user} {self.site.site_path()})')

    # It does not work in all cases
    def recaptcha(self, status):
        public_key = ''
        private_key = ''
        version = 'v2'

        if packaging_version.parse(self.version.split('-')[0]) >= packaging_version.parse('2.4'):
            version = 'v3'

        with open(f"{self.config.wt_config_path}/config/recaptcha_keys.json") as f:
            recaptcha_keys = json.load(f)

        if status == 1:
            public_key = recaptcha_keys[version]['public_key']
            private_key = recaptcha_keys[version]['private_key']

        self.magento('app:config:import')

        if version == 'v3':
            self.config_set('recaptcha_backend/type_recaptcha_v3/public_key', public_key)
            self.config_set('recaptcha_backend/type_recaptcha_v3/private_key', private_key)

            self.config_set('recaptcha_frontend/type_recaptcha_v3/public_key', public_key)
            self.config_set('recaptcha_frontend/type_recaptcha_v3/private_key', private_key)
        else:
            self.config_set('msp_securitysuite_recaptcha/general/public_key', public_key)
            self.config_set('msp_securitysuite_recaptcha/general/private_key', private_key)

            self.config_set('msp_securitysuite_recaptcha/backend/enabled', status)
            self.config_set('msp_securitysuite_recaptcha/frontend/enabled', status)

        self.magento('cache:flush')

    def clean_token_request_log(self):
        with self.db.db_connect:
            with self.db.db_connect.cursor() as cur:
                cur.execute(f'TRUNCATE {self.site.current_site_id}.oauth_token_request_log')

    def install(self, site_id, version, admin_user, admin_password, firstname, lastname, mail, base_url, with_sample_data=False):
        php_version = 7.3
        if packaging_version.parse(version) < packaging_version.parse('2.4'):
            php_version = 7.2

        base_url_secure = base_url.replace('http://', 'https://')
        self.site.php.cli_version(php_version)
        self.site.use(php_version, site_id)

        os.system(f'composer create-project --repository-url=https://repo.magento.com/ '
                  f'magento/project-community-edition={version} .')
        self.db.db_create(site_id)

        cmd = list()
        cmd.append('bin/magento setup:install')
        cmd.append(f'--base-url="{base_url}"')
        cmd.append(f'--base-url-secure="{base_url_secure}"')
        cmd.append('--use-rewrites=1')
        cmd.append('--use-sample-data')

        cmd.append('--db-host=127.0.0.1')
        cmd.append(f'--db-name={site_id}')
        cmd.append('--db-user=root')
        cmd.append('--db-password=root')

        cmd.append('--backend-frontname=admin')
        cmd.append(f'--admin-firstname={firstname}')
        cmd.append(f'--admin-lastname={lastname}')
        cmd.append(f'--admin-email={mail}')
        cmd.append(f'--admin-user={admin_user}')
        cmd.append(f'--admin-password={admin_password}')

        cmd.append('--language=pt_BR')
        cmd.append('--currency=BRL')
        cmd.append('--timezone=America/Sao_Paulo')

        if packaging_version.parse(version) >= packaging_version.parse('2.4'):
            cmd.append('--search-engine="elasticsearch7"')
            cmd.append('--elasticsearch-host="127.0.0.1"')
            cmd.append('--elasticsearch-port=9200')
            cmd.append(f'--elasticsearch-index-prefix="{site_id}"')

        cmd.append('--amqp-host="127.0.0.1"')
        cmd.append('--amqp-port="5672"')
        cmd.append('--amqp-user="guest"')
        cmd.append('--amqp-password="guest"')
        cmd.append('--amqp-virtualhost="/"')

        cmd.append('--session-save="redis"')
        cmd.append('--session-save-redis-host="127.0.0.1"')
        cmd.append('--session-save-redis-port=6379')
        cmd.append('--session-save-redis-timeout=1')

        cmd.append('--cache-backend="redis"')
        cmd.append('--cache-backend-redis-server="127.0.0.1"')
        cmd.append('--cache-backend-redis-port=6379')

        cmd.append('--page-cache="redis"')
        cmd.append('--page-cache-redis-server="127.0.0.1"')
        cmd.append('--page-cache-redis-port=6379')

        cmd = ' '.join(cmd)

        os.system(cmd)
        self.dev_config()

        if packaging_version.parse(version) >= packaging_version.parse('2.4'):
            self.twofactorauth(admin_user, 'MFRGGZDF')

        if with_sample_data:
            self.install_sample_data()
