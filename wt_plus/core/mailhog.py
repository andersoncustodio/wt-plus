import os


class MailHog(object):
    def __init__(self, config, site):
        self.config = config
        self.site = site

    def configure(self):
        if not os.path.exists('/usr/local/bin'):
            os.system(f'sudo mkdir -p /usr/local/bin')

        if not os.path.exists('/usr/local/bin/mailhog'):
            os.system('sudo wget https://github.com/mailhog/MailHog/releases/download/v1.0.1/MailHog_linux_amd64'
                      ' -O /usr/local/bin/mailhog')
            os.system('sudo chmod +x /usr/local/bin/mailhog')

        if not os.path.exists('/usr/local/bin/mhsendmail'):
            os.system('sudo wget https://github.com/mailhog/mhsendmail/releases/download/v0.2.0/mhsendmail_linux_amd64'
                      ' -O /usr/local/bin/mhsendmail')
            os.system('sudo chmod +x /usr/local/bin/mhsendmail')

        if not self.site.is_site_exists('proxy'):
            self.config.set_site_config('proxy', [
                '/api/v2/websocket ws://localhost:8025/api/v2/websocket',
                '/ http://localhost:8025/'
            ], 'mailhog')
            self.site.secure('mailhog')

        mailhog_service = """
            sudo tee /etc/systemd/system/mailhog.service <<EOL
[Unit]
Description=MailHog
After=network.target
[Service]
ExecStart=/usr/bin/env /usr/local/bin/mailhog > /dev/null 2>&1 &
[Install]
WantedBy=multi-user.target
EOL
"""
        if not os.path.exists('/etc/systemd/system/mailhog.service'):
            os.system(mailhog_service)
            os.system('sudo systemctl daemon-reload')

        os.system('sudo systemctl restart mailhog.service')

    def start(self):
        os.system('sudo systemctl start mailhog.service')

    def stop(self):
        os.system('sudo systemctl stop mailhog.service')

    def restart(self):
        os.system('sudo systemctl restart mailhog.service')

    def enable(self,):
        os.system('sudo systemctl enable mailhog.service')

    def disable(self):
        os.system('sudo systemctl disable mailhog.service')
