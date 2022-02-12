import subprocess
import os
import click
import os.path
import magic
import uuid
import pymysql.cursors
from glob import glob
from datetime import datetime
from configparser import ConfigParser


class DbExistsError(TypeError):
    pass


class DbNotExistsError(TypeError):
    pass


class SqlFileNotExistsError(TypeError):
    pass


class Db:
    DATE_FORMAT = '%Y-%m-%d-%H%M%S'
    MSG_DB_EXISTS = "{db_name} database already exists! 😖"
    MSG_DB_NOT_EXISTS = "Banco '{db_name}' não existe! 😖"

    def __init__(self):
        self._db_connect = None

    def configure(self):
        pass

    @property
    def db_connect(self):
        if self._db_connect is None:
            config = ConfigParser()
            config.read(f"{os.path.expanduser('~')}/.my.cnf")

            host = config.get('client', 'host', fallback='127.0.0.1')
            user = config.get('client', 'user')
            password = config.get('client', 'password')

            self._db_connect = pymysql.connect(host=host,
                                               user=user,
                                               passwd=password,
                                               cursorclass=pymysql.cursors.DictCursor)

        return self._db_connect

    def start(self):
        os.system('sudo systemctl start mysql.service')

    def stop(self):
        os.system('sudo systemctl stop mysql.service')

    def restart(self):
        os.system('sudo systemctl restart mysql.service')

    def enable(self):
        os.system('sudo systemctl enable mysql.service')

    def disable(self):
        os.system('sudo systemctl disable mysql.service')

    def db_list(self):
        databases = list()

        with self.db_connect:
            with self.db_connect.cursor() as cur:
                cur.execute("show databases")
                result = cur.fetchall()
                for database in result:
                    if database['Database'] not in ['mysql', 'information_schema', 'performance_schema', 'phpmyadmin']:
                        databases.append(database['Database'])

        return databases

    def db_sql(self, sql):
        return 'mysql -e "{sql}"'.format(sql=sql)

    def db_exists(self, db_name):
        cmd = "mysql -e \"SELECT if(COUNT(*) = 0, 0, 1) FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'\" | sed -n 2p | tr -d '\n'"
        output = subprocess.check_output([cmd.format(db_name=db_name)], shell=True)

        return '1' == output.decode('utf-8')

    def db_create(self, db_name):
        if self.db_exists(db_name):
            raise DbExistsError(self.MSG_DB_EXISTS.format(db_name=db_name))

        cmd = "mysql -e \"CREATE DATABASE {db_name}\""
        os.system(cmd.format(db_name=db_name))

    def db_drop(self, db_name):
        if not self.db_exists(db_name):
            raise DbExistsError(self.MSG_DB_NOT_EXISTS.format(db_name=db_name))

        os.system("mysql -e\"DROP DATABASE {db_name}\"".format(db_name=db_name))

    def db_reset(self, db_name):
        self.db_drop(db_name)
        self.db_create(db_name)

    def db_dump(self, file_name, db_name, is_sql):
        if not self.db_exists(db_name):
            raise DbNotExistsError(self.MSG_DB_NOT_EXISTS.format(db_name=db_name))

        now = datetime.now()

        cmd = "mysqldump --column-statistics=0 {db_name} "

        if file_name == '-':
            file_name = "{db_name}-{now}.sql".format(now=now.strftime(self.DATE_FORMAT), db_name=db_name)

        if not is_sql:
            cmd += "| gzip -9 -c "
            file_name += ".gz"

        cmd += " > {file_name}"

        msg = f"Dumping the '{db_name}' database 📥"
        click.echo(msg)
        os.system(cmd.format(db_name=db_name, file_name=file_name))

    def db_import(self, sql_path, db_name):
        if not self.db_exists(db_name):
            raise DbExistsError(self.MSG_DB_EXISTS.format(db_name=db_name))

        if not os.path.isfile(sql_path):
            raise SqlFileNotExistsError(f"SQL file '{sql_path}' was not found")

        mime = magic.from_file(sql_path, mime=True)

        cmd = ''

        if mime == 'application/gzip':
            cmd += 'z'

        cmd += 'cat "{sql_path}" | mysql {db_dest}'
        os.system(cmd.format(sql_path=sql_path, db_dest=db_name))

    def db_remove_definer(self, sql_path):
        if not os.path.isfile(sql_path):
            raise SqlFileNotExistsError(f"SQL file '{sql_path}' was not found")

        tmp_path = "/tmp/{hash}".format(hash=uuid.uuid4().hex)

        mime = magic.from_file(sql_path, mime=True)

        if mime == 'application/gzip':
            cmd = list()
            cmd.append(rf'zcat "{sql_path}" | sed "s/DEFINER=[^*]*\*/\*/g" > "{tmp_path}"')
            cmd.append(rf'gzip -9 -c "{tmp_path}" > "{sql_path}"')
            cmd.append(rf'rm "{tmp_path}"')

            os.system(' && '.join(cmd))
            return

        os.system(rf'sed -i "s/DEFINER=[^*]*\*/\*/g" "{sql_path}"')

    def sql_file_complete(self, ctx, args, incomplete):
        files = glob('*.sql') + glob('*.sql.gz')
        files.append(args)
        return [k for k in files if incomplete in k]

    def databases_complete(self, ctx, args, incomplete):
        databases = self.db_list()
        return [k for k in databases if incomplete in k]
