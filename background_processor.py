# This file periodically checks if someone in .users.json
# has fewer than MIN_PAPERS papers untouched.

import time
import json
from connect import create_mysql_connection
import tagger.main.serve_paper as serve_paper

SLEEP_TIME = 30
MIN_UNFINISHED_PAPERS = 5

GET_UNFINISHED_COUNT = "SELECT COUNT(*) FROM tagging WHERE user_email=%(email)s AND marked_as_done=0"

def process_paper(email, conn):
    print("processing new paper for %s..." % email)
    ssid, title = serve_paper.get_unedited_paper(conn)
    print("\trendering '%s'" % title)
    serve_paper.render_and_generate_json(ssid, email, conn)
    

def check_all_papers():
    conn = create_mysql_connection()
    cursor = conn.cursor()
    with open('tagger/.users.json') as f:
        users = json.load(f)['users']
        for email in users:
            print("checking processed papers for", email)
            cursor.execute(GET_UNFINISHED_COUNT, {'email': email})
            count = cursor.fetchall()[0][0]
            if count < MIN_UNFINISHED_PAPERS:
                for paper_i in range(MIN_UNFINISHED_PAPERS - count):
                    process_paper(email, conn)
    cursor.close()
    conn.close()

if __name__ == '__main__':
    while True:
        check_all_papers()
        print('sleeping...')
        time.sleep(SLEEP_TIME)
