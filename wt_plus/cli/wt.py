import os
import subprocess
import click
import wt_plus.core

from prettytable import PrettyTable


def php_versions(ctx, args, incomplete):
    versions = ['5.6', '7.1', '7.2', '7.3', '7.4', '8.0']
    return [k for k in versions if incomplete in k]


def status_complete(ctx, args, incomplete):
    status = ['on', 'off']
    return [k for k in status if incomplete in k]


def sapi_name_complete(ctx, args, incomplete):
    status = ['cli', 'fpm', 'all']
    return [k for k in status if incomplete in k]


def framework_complete(ctx, args, incomplete):
    versions = ['magento2']
    return [k for k in versions if incomplete in k]


wt = click.Group(name='wt')


@wt.command('about')
def about():
    click.echo("This is a CLI built with Click 🔥")


@wt.command('xdebug')
@click.argument('status', type=click.STRING, autocompletion=status_complete)
@click.option('--remote_autostart', default=False, is_flag=True)
@click.option('-s', '--sapi-name', type=str, default='fpm', autocompletion=sapi_name_complete, help="Sapi name")
@click.option('-v', '--php-version', type=str, autocompletion=php_versions, help="PHP version")
def xdebug(status, remote_autostart, sapi_name, php_version):
    current_site_id = wt_plus.core.site.current_site_id
    wt_plus.core.site.php.xdebug(status, remote_autostart, sapi_name, php_version, current_site_id)


@wt.command()
@click.argument('path', type=click.STRING, nargs=-1)
@click.option('--idekey', type=str, default='PHPSTORM', help="idekey")
def phpx(path, idekey):
    path = ' '.join(path)
    os.system(f'XDEBUG_CONFIG="idekey={idekey}" php -dzend_extension=xdebug.so -dxdebug.mode=debug {path}')


@wt.command()
@click.argument('path', type=click.STRING, autocompletion=wt_plus.core.config.config_path_complete)
@click.argument('value', type=click.STRING, autocompletion=wt_plus.core.config.config_value_complete, required=False)
@click.argument('site_id', default=wt_plus.core.site.current_site_id)
def config(path, value, site_id):
    if path not in wt_plus.core.config.public_configs:
        click.echo('Não disponível')
        return

    if value is None:
        click.echo(wt_plus.core.config.get_site_config(path, site_id))
        return

    if path == 'php/php_admin_value/auto_prepend_file':
        value = f'{wt_plus.core.config.current_path}/{value}'

    wt_plus.core.config.set_site_config(path, value, site_id)
    wt_plus.core.site.dump_config()


@wt.command()
@click.argument('path', type=click.STRING, autocompletion=wt_plus.core.config.config_path_complete)
@click.argument('site_id', default=wt_plus.core.site.current_site_id)
def unconfig(path, site_id):
    if path not in wt_plus.core.config.public_configs:
        click.echo('Não disponível')
        return

    click.echo(wt_plus.core.config.unset_site_config(path, site_id))
    wt_plus.core.config.save()


@wt.command('self-config')
def self_config():
    os.system(f"{os.getenv('EDITOR') or 'nano'} {wt_plus.core.config.file_config}")
    wt_plus.core.config.reload()
    wt_plus.core.site.dump_config()


@wt.command()
@click.argument('site_id', default=wt_plus.core.site.current_site_id)
def log(site_id):
    if not wt_plus.core.site.is_site_exists(site_id):
        click.echo('Site não existe')

    os.system(f'tail -f {wt_plus.core.config.wt_config_path}/log/{site_id}-*')


@wt.command()
def current():
    site_id = wt_plus.core.site.current_site_id

    if site_id is None:
        click.echo('Site não encontrado 😢')

    click.echo(wt_plus.core.site.current_site_id)

@wt.command()
@click.argument('version', required=False, type=click.FLOAT, autocompletion=php_versions)
@click.argument('site_id', default=wt_plus.core.site.current_site_id)
@click.option('--update-cli', default=False, is_flag=True, help='Update cli php')
def use(version, site_id, update_cli):
    try:
        if version is None:
            version = wt_plus.core.config.get_site_config('php/version', site_id) or 7.3
            update_cli = True

        wt_plus.core.site.use(version, site_id, update_cli)
        wt_plus.core.site.dump_config()
        click.echo(f"PHP {version} {site_id} 🔥")
    except wt_plus.core.SiteNotExistsError as e:
        click.echo(e)


@wt.command()
def links():
    table = PrettyTable(['Site', 'SSL', 'PHP', 'URL', 'Path/[public_html]'])
    table.align = 'l'

    sites = wt_plus.core.config.get('sites')

    for site in sites:
        curren_site = sites.get(site)

        ssl, http = ['', 'http']
        if wt_plus.core.config.get_site_config('secure', site) is True:
            ssl, http = ['X', 'https']

        url = f'{http}://{site}.test'

        if curren_site.get('alias'):
            for site_alias in curren_site.get('alias'):
                url += f'\n{http}://{site_alias}'

        php_version = wt_plus.core.config.get_site_config('php/version', site) or ''
        public_path = wt_plus.core.config.get_site_config('public_path', site) or ''
        path = wt_plus.core.config.get_site_config('path', site) or ''

        if not path == '' and not public_path == '':
            path += f'[{public_path}]'

        table.add_row([site, ssl, php_version, url, path])

    click.echo(table)


@wt.command()
@click.argument('site', default=wt_plus.core.site.default_site_id)
@click.option('--framework', default=None, autocompletion=framework_complete)
@click.option('--unsecure', default=False, is_flag=True)
def link(site, framework, unsecure):
    try:
        wt_plus.core.site.add(site, framework, unsecure)
        wt_plus.core.site.dump_config()
        click.echo(f"'{site}' run 🔥")
    except wt_plus.core.SiteExistsError as e:
        click.echo(e)


@wt.command()
@click.argument('site_id', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.site.sites_complete)
def unlink(site_id):
    try:
        wt_plus.core.site.remove(site_id)
        wt_plus.core.site.dump_config()
        click.echo(f"'{site_id}' remove 💦")
    except wt_plus.core.SiteNotExistsError as e:
        click.echo(e)


@wt.command()
@click.argument('site_id', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.site.sites_complete)
def secure(site_id):
    wt_plus.core.site.secure(site_id)
    wt_plus.core.site.dump_config()


@wt.command()
@click.argument('site_id', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.site.sites_complete)
def unsecure(site_id):
    wt_plus.core.site.unsecure(site_id)
    wt_plus.core.site.dump_config()


@wt.command()
@click.argument('name')
@click.argument('site_id', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.site.sites_complete)
def alias(name, site_id):
    try:
        wt_plus.core.site.add_alias(site_id, name)
        wt_plus.core.site.dump_config()
        click.echo(f"'{name}' adicionado 🔥")
    except wt_plus.core.SiteNotExistsError as e:
        click.echo(e)


@wt.command()
@click.argument('origin')
@click.argument('target')
@click.argument('site_id', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.site.sites_complete)
def proxy(origin, target, site_id):
    try:
        wt_plus.core.site.add_proxy(site_id, origin, target)
        wt_plus.core.site.dump_config()
        click.echo(f"'{origin}' -> '{target}' adicionado 🔥")
    except wt_plus.core.SiteNotExistsError as e:
        click.echo(e)
    except wt_plus.core.ProxyExistsError as e:
        click.echo(e)


@wt.command()
@click.argument('origin')
@click.argument('site_id', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.site.sites_complete)
def unproxy(origin, site_id):
    try:
        wt_plus.core.site.rm_proxy(site_id, origin)
        wt_plus.core.site.dump_config()
        click.echo(f"'{origin}' removido 💦")
    except wt_plus.core.SiteNotExistsError as e:
        click.echo(e)


@wt.command()
@click.argument('name', autocompletion=wt_plus.core.site.aliases_complete)
@click.argument('site_id', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.site.sites_complete)
def unalias(name, site_id):
    try:
        wt_plus.core.site.del_alias(site_id, name)
        wt_plus.core.site.dump_config()
        click.echo(f"'{name}' removido 💦")
    except wt_plus.core.SiteNotExistsError as e:
        click.echo(e)


@wt.command()
def reload():
    wt_plus.core.config.reload()
    wt_plus.core.site.http.dump_config()


@wt.command('open')
@click.argument('path', default='.')
@click.option('-d', default=False, is_flag=True, help='Chooose')
def open_(path, d):
    click.launch("{path}".format(path=path), locate=True)


@wt.command()
@click.argument('path', type=click.Path(exists=True), default=os.getcwd())
@click.argument('path_compare', type=click.Path(exists=True), required=False, default=None)
def phpstorm(path, path_compare):
    if path_compare:
        subprocess.run([f'nohup phpstorm diff {path} {path_compare} > /dev/null 2>&1 & disown'],
                       shell=True, executable='/bin/bash')
    else:
        subprocess.run([f'nohup phpstorm {path} > /dev/null 2>&1 & disown'],
                       shell=True, executable='/bin/bash')


@wt.command(hidden=True)
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish'], case_sensitive=False))
def completions(shell):
    os.system(f'LC_ALL=C _WT_COMPLETE={shell}_source wt')
