import os
from shutil import which


class Redis(object):
    def configure(self):
        if which('redis-cli') is None:
            os.system('sudo apt install -y redis-server')

    def start(self):
        os.system('sudo systemctl start redis.service')

    def stop(self):
        os.system('sudo systemctl stop redis.service')

    def restart(self):
        os.system('sudo systemctl restart redis.service')

    def enable(self,):
        os.system('sudo systemctl enable redis.service')

    def disable(self):
        os.system('sudo systemctl disable redis.service')

