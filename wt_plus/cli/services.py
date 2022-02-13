import click
import os
import wt_plus.core


services = click.Group(name='services')


@services.command()
def start():
    wt_plus.core.site.http.start()
    wt_plus.core.site.php.start_all()
    #wt_plus.core.db.start()
    wt_plus.core.mailhog.start()


@services.command()
def stop():
    wt_plus.core.site.http.stop()
    wt_plus.core.site.php.stop_all()
    #wt_plus.core.db.stop()
    wt_plus.core.mailhog.stop()


@services.command()
def restart():
    wt_plus.core.site.http.restart()
    wt_plus.core.site.php.restart_all()
    #wt_plus.core.db.restart()
    wt_plus.core.mailhog.restart()
    wt_plus.core.redis.restart()


@services.command()
def enable():
    wt_plus.core.site.http.enable()
    wt_plus.core.site.php.enable_all()
    #wt_plus.core.db.enable()
    wt_plus.core.mailhog.enable()
    wt_plus.core.redis.enable()


@services.command()
def disable():
    wt_plus.core.site.http.disable()
    wt_plus.core.site.php.disable_all()
    #wt_plus.core.db.disable()
    wt_plus.core.mailhog.disable()
    wt_plus.core.redis.disable()


@services.command()
def configure():
    os.system(r'sudo apt install -y oathtool')
    os.system(fr'cp {wt_plus.core.config.wt_path}/templates/config/recaptcha_keys.json '
              '{wt_plus.core.config.wt_config_path}/config/recaptcha_keys.json')
    wt_plus.core.site.configure()
    wt_plus.core.site.host.configure()
    wt_plus.core.site.http.configure()
    wt_plus.core.site.php.configure()
    wt_plus.core.db.configure()
    wt_plus.core.mailhog.configure()
    wt_plus.core.redis.configure()
    wt_plus.core.rabbitmq.configure()
    wt_plus.core.site.dump_config()
