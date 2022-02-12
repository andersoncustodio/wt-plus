import os
from shutil import which


class Rabbitmq(object):
    def configure(self):
        if which('rabbitmq-server') is None:
            os.system('sudo apt install -y rabbitmq-server')
            os.system('sudo rabbitmq-plugins enable rabbitmq_management && sudo rabbitmqctl add_user admin admin '
                      '&& sudo rabbitmqctl set_user_tags admin administrator')

    def start(self):
        os.system('sudo systemctl start rabbitmq-server.service')
        pass

    def stop(self):
        os.system('sudo systemctl stop rabbitmq-server.service')
        pass

    def restart(self):
        os.system('sudo systemctl restart rabbitmq-server.service')
        pass

    def enable(self,):
        os.system('sudo systemctl enable rabbitmq-server.service')
        pass

    def disable(self):
        os.system('sudo systemctl disable rabbitmq-server.service')
        pass
