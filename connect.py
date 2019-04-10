import os
import configparser
import mysql.connector

_home_directory = os.path.dirname(os.path.realpath(__file__))

def create_mysql_connection(database_config = os.path.join(_home_directory, '.mysql.cfg')):
    config = configparser.ConfigParser()
    config.read(database_config)
    user = config['mysql'].get('user', 'paper')
    passwd = config['mysql']['passwd']
    database = config['mysql'].get('database', 'papers')
    host = config['mysql'].get('host', 'localhost')
    port = config['mysql'].get('port', 3306)
    connection = mysql.connector.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        passwd=passwd,
    )
    connection.set_charset_collation(charset="utf8", collation=None)
    return connection
