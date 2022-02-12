import os


class Host(object):
    def __init__(self, config):
        self.config = config

    def configure(self):
        create = f'[ $(grep -c "# ~BEGIN WT" /etc/hosts) == "0" ] && echo "\n# ~BEGIN WT\n\n# ~END WT" >> /etc/hosts'
        os.system(f'sudo /bin/bash -c \'{create}\'')

    def dump_config(self):
        plain_host = ''

        hosts = self.config.get_config('hosts')
        for host in hosts:
            plain_host += fr'{hosts[host]} {host}\n'

        sites = self.config.get_config('sites')
        for site in sites:
            site_config = sites.get(site)

            if site_config is None:
                continue

            aliases = site_config.get('alias')

            plain_host += f"127.0.0.1 {site}.test"

            if aliases:
                for alias in aliases:
                    plain_host += f' {alias}'

            plain_host += r'\n'

        cmd = r"sudo sed -i '\%# ~BEGIN WT%,\%# ~END WT%c # ~BEGIN WT\n'"
        cmd += f'"{plain_host}"' + "'# ~END WT' /etc/hosts"
        os.system(cmd)
