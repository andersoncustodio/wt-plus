from wt_plus.cli.wt import wt
from wt_plus.cli.db import db
from wt_plus.cli.magento2 import magento2
from wt_plus.cli.tools import tools
from wt_plus.cli.services import services

wt.add_command(db)
wt.add_command(magento2)
wt.add_command(tools)
wt.add_command(services)

if __name__ == '__main__':
    wt()
