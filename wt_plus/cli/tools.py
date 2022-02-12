import click
import os

tools = click.Group(name='tools')


@tools.command()
@click.argument('url')
def redirects(url):
    os.system("curl -sILk '{url}' | grep -E 'HTTP|Loc' | sed 's/Loc/ -> Loc/g'".format(url=url))
