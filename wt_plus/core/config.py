from ruamel import yaml
import pathlib
import os
import getpass
from glob import glob


class Config(object):
    def __init__(self):
        self.file_config = rf'{self.wt_config_path}/config/wt.yml'
        self.config = None
        self.reload()
        self._config = None
        self.public_configs = [
            'php/php_admin_value/auto_prepend_file'
        ]

    def reload(self):
        config_file = self.file_config
        if not os.path.isfile(self.file_config):
            config_file = f'{self.wt_path}/templates/config/wt.yml'
        self.config = yaml.YAML().load(open(config_file).read())

    def get(self, key):
        return self.config.get(key)

    def save(self):
        test = pathlib.Path(self.file_config)
        yaml.YAML().dump(self.config, test)

    def save_test(self):
        test = pathlib.Path(self.file_config.replace('.yml', '-test.yml'))
        yaml.YAML().dump(self.config, test)

    @property
    def certificate_path(self):
        return f'{self.wt_config_path}/certificates'

    @property
    def wt_path(self) -> str:
        return str(pathlib.Path(__file__).parent.parent.resolve())

    @property
    def home_path(self):
        return os.path.expanduser("~")

    @property
    def wt_config_path(self):
        return f'{self.home_path}/.wt'

    @property
    def user(self):
        return getpass.getuser()

    @property
    def current_path(self):
        return pathlib.Path().resolve()

    def _set_config(self, parts, value, config):
        if len(parts) == 1:
            if value == dict():
                value = yaml.CommentedMap(value)
            config.insert(1, parts[0], value)
            return True
        elif len(parts):
            if parts[0] not in config:
                config.insert(1, parts[0], yaml.CommentedMap())
            config = config.get(parts[0])
            return self._set_config(parts[1:], value, config)
        return parts

    def set_config(self, path, value):
        parts = path.rstrip('/').split('/')
        return self._set_config(parts, value, self.config)

    def set_site_config(self, path, value, site_id):
        path = f'sites/{site_id}/{path}'
        return self.set_config(path, value)

    def _get_config(self, parts, config):
        if len(parts) == 1:
            if parts[0] not in config:
                return None
            return config.get(parts[0])
        elif parts[0] in config:
            config = config.get(parts[0])
            if config is None:
                return None
            return self._get_config(parts[1:], config)

    def get_config(self, path):
        parts = path.split('/')
        return self._get_config(parts, self.config)

    def get_site_config(self, path, site_id):
        path = f'sites/{site_id}/{path}'
        return self.get_config(path)

    def _unset_config(self, parts, config):
        try:
            if len(parts) == 2:
                config.get(parts[0]).pop(parts[1], None)
                if config.get(parts[0]) == {}:
                    config.pop(parts[0], None)
                return True
            elif len(parts):
                config = config.get(parts[0])
                return self._unset_config(parts[1:], config)
        except AttributeError:
            return False

    def unset_config(self, path):
        parts = path.rstrip('/').split('/')
        return self._unset_config(parts, self.config)

    def unset_site_config(self, path, site_id):
        path = f'sites/{site_id}/{path}'
        return self.unset_config(path)

    def config_path_complete(self, ctx, args, incomplete):
        return [k for k in self.public_configs if incomplete in k]

    def config_value_complete(self, ctx, args, incomplete):
        values = glob('*.php')
        return [k for k in values if incomplete in k]
