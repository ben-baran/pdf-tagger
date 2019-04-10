from flask import Blueprint, g
from connect import create_mysql_connection

def get_connection():
    if 'conn' not in g:
        g.conn = create_mysql_connection()
    return g.conn

def close_connection(e = None):
    conn = g.pop('conn', None)
    if conn is not None:
        conn.close()

main = Blueprint('tag', __name__)

from . import static_pages, render_updates
