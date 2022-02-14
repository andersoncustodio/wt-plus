import os
import click
import wt_plus.core

from prettytable import PrettyTable

db = click.Group(name='db')


@db.command('ls')
def db_list():
    table = PrettyTable(['Databases'])
    table.align = 'l'

    databases = wt_plus.core.db.db_list()

    for database in databases:
        table.add_row([database])

    click.echo(table)


@db.command('create')
@click.argument('db_name', default=wt_plus.core.site.current_site_id)
def db_create(db_name):
    try:
        wt_plus.core.db.db_create(db_name)
    except wt_plus.core.DbExistsError as e:
        click.echo(e)


@db.command('drop')
@click.argument('db_name', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.db.databases_complete)
def db_drop(db_name):
    if not wt_plus.core.db.db_exists(db_name):
        click.echo(wt_plus.core.db.MSG_DB_NOT_EXISTS.format(db_name=db_name))
        return

    click.confirm("Remove the '{db_name}' database? 😮".format(db_name=db_name), abort=True)
    wt_plus.core.db.db_drop(db_name)


@db.command('export')
@click.argument('sql_name', default='-')
@click.argument('db_name', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.db.databases_complete)
@click.option('--sql', default=False, is_flag=True, help='Plain sql to dump')
def db_dump(sql_name, db_name, sql):
    try:
        wt_plus.core.db.db_dump(sql_name, db_name, sql)
    except wt_plus.core.DbNotExistsError as e:
        click.echo(e)


@db.command('reset')
@click.argument('db_dest', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.db.databases_complete)
def db_reset(db_dest):
    if wt_plus.core.db.db_exists(db_dest):
        click.confirm("Overwrite the '{db_dest}' database? 😮".format(db_dest=db_dest), abort=True)
        wt_plus.core.db.db_drop(db_dest)

    wt_plus.core.db.db_create(db_dest)


@db.command('remove-definer')
@click.argument('sql_path', type=click.Path(exists=True), autocompletion=wt_plus.core.db.sql_file_complete)
def db_remove_definer(sql_path):
    wt_plus.core.db.db_remove_definer(sql_path)


@db.command('import')
@click.argument('sql_path', type=click.Path(exists=True), autocompletion=wt_plus.core.db.sql_file_complete)
@click.argument('db_dest', default=wt_plus.core.site.current_site_id, autocompletion=wt_plus.core.db.databases_complete)
def db_import(sql_path, db_dest):
    if wt_plus.core.db.db_exists(db_dest):
        click.confirm("Overwrite the '{db_dest}' database? 😮".format(db_dest=db_dest), abort=True)
        wt_plus.core.db.db_drop(db_dest)

    wt_plus.core.db.db_create(db_dest)

    try:
        wt_plus.core.db.db_import(sql_path, db_dest)
    except wt_plus.core.SqlFileNotExistsError as e:
        click.echo(e)


@db.command('clone')
@click.argument('db_src', autocompletion=wt_plus.core.db.databases_complete)
@click.argument('db_dest')
def db_clone(db_src, db_dest):
    click.echo(f"Copying '{db_src}' to '{db_dest}' 📸")

    if not wt_plus.core.db.db_exists(db_src):
        click.echo(wt_plus.core.db.MSG_DB_NOT_EXISTS.format(db_dest=db_src))
        return

    if wt_plus.core.db.db_exists(db_dest):
        click.confirm(f"Overwrite the '{db_dest}' database? 😮", abort=True)
        os.system("mysql -e\"DROP DATABASE {db_dest}\"".format(db_dest=db_dest))

    os.system("mysql -e\"CREATE DATABASE {db_dest}\"".format(db_dest=db_dest))

    cmd = "mysqldump {db_src} | mysql {db_dest}"
    os.system(cmd.format(db_src=db_src, db_dest=db_dest))
