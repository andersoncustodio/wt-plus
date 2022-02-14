import click
import subprocess
import wt_plus.core


def _app_import():
    subprocess.check_output(['n98 app:config:import'], shell=True)


def _cache_flush():
    subprocess.check_output(['n98 cache:flush'], shell=True)


def mage_versions(ctx, args, incomplete):
    return [k for k in wt_plus.core.site.magento2.versions if incomplete in k]


magento2 = click.Group(name='magento2')


@magento2.command('install')
@click.argument('version', default='2.4.3', type=click.STRING, autocompletion=mage_versions)
@click.option('--firstname', default='Wt')
@click.option('--admin_user', default='admin')
@click.option('--admin_password', default='admin123')
@click.option('--lastname', default='Env')
@click.option('--email', default=f'admin@{wt_plus.core.site.current_site_id}.test')
@click.option('--base-url', default=f'http://{wt_plus.core.site.current_site_id}.test')
@click.option('--with-sample-data', is_flag=True, default=False)
def install(version, admin_user, admin_password, firstname, lastname, email, base_url, with_sample_data):
    try:
        site_id = wt_plus.core.site.current_site_id
        wt_plus.core.site.magento2.install(site_id, version, admin_user, admin_password, firstname, lastname, email,
                                          base_url, with_sample_data)
        click.echo(base_url)
    except wt_plus.core.SiteNotExistsError as e:
        click.echo(e)


@magento2.command()
@click.argument('src')
@click.argument('dist', default=f'{wt_plus.core.site.current_site_id}.test')
@click.argument('db_name', default=wt_plus.core.site.current_site_id)
def change_base_url(src, dist, db_name):
    try:
        wt_plus.core.site.magento2.change_base_url(src, dist, db_name)
        click.echo(f"Changed domain 🔥")
    except wt_plus.core.SiteNotExistsError as e:
        click.echo(e)


@magento2.command()
def smtp_disable():
    try:
        subprocess.check_output(['n98 config:set transactional_emails/ddg_transactional/enabled 0'], shell=True)
    except:
        pass


@magento2.command('dev-config')
def dev_config():
    wt_plus.core.site.magento2.dev_config()


@magento2.command()
def version():
    click.echo(wt_plus.core.site.magento2.version)


@magento2.command()
@click.argument('admin_user', default="admin")
def token(admin_user):
    wt_plus.core.site.magento2.token(admin_user)


@magento2.command('sample-data')
def sample_data():
    wt_plus.core.site.magento2.install_sample_data()


@magento2.command()
def clean_static():
    wt_plus.core.site.magento2.clean_static()
    click.echo('Cleaning completed 🧹️')


@magento2.command('tfa-config')
@click.argument('admin_user', default="admin")
@click.argument('secret', default="MFRGGZDF")
def twofactorauth_change(admin_user, secret):
    wt_plus.core.site.magento2.twofactorauth(admin_user, secret)


@magento2.command()
@click.argument('status', type=click.Choice(['on', 'off'], case_sensitive=False))
def recaptcha(status):
    status = int(status == 'on')
    wt_plus.core.site.magento2.recaptcha(status)
