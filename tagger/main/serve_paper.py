import os
import subprocess
import glob
import json
import time

GET_LAST_EDITED_PAPER = (
    "SELECT ssid FROM tagging WHERE "
    "user_email=%(user_email)s"
    "ORDER BY last_edited DESC "
    "LIMIT 1"
)

def get_last_edited_paper(email, conn):
    cursor = conn.cursor()
    cursor.execute(GET_LAST_EDITED_PAPER, {'user_email': email})
    fetch = cursor.fetchall()
    cursor.close()
    if len(fetch) == 0:
        return None
    return fetch[0][0]
    
GET_TITLE_FOR_SSID = (
    "SELECT title FROM ss_paper WHERE ssid=%(ssid)s "
    "LIMIT 1"
)

def get_title_for_ssid(cursor, ssid):
    cursor.execute(GET_TITLE_FOR_SSID, {'ssid': ssid})
    return cursor.fetchall()[0][0]
    
GET_UNEDITED_PAPER = (
    "SELECT ssid FROM processed "
    "WHERE ssid NOT IN (SELECT ssid FROM tagging) "
    "ORDER BY RAND() "
    "LIMIT 1"
)

def get_unedited_paper(conn):
    cursor = conn.cursor()
    cursor.execute(GET_UNEDITED_PAPER)
    ssid = cursor.fetchall()[0][0]
    title = get_title_for_ssid(cursor, ssid)
    cursor.close()
    return ssid, title

GET_FILEPATH_FOR_SSID = (
    "SELECT filename FROM processed "
    "WHERE ssid=%(ssid)s"
)

GET_PAGE_DIMENSIONS = (
    "SELECT n, width, height FROM pages "
    "WHERE ssid=%(ssid)s"
)

GET_ALL_PARAGRAPH_BBS = (
    "SELECT paragraph_id,n,page,x,y,width,height FROM paragraph_bb "
    "WHERE paragraph_id IN (SELECT paragraph_id FROM paragraphs WHERE ssid=%(ssid)s)"
)

GET_PARAGRAPH_SENTENCE_BOUNDS = (
    "SELECT sentence_start, sentence_end FROM paragraphs "
    "WHERE paragraph_id=%(paragraph_id)s"
)

GET_SENTENCES_FOR_BOUNDS = (
    "SELECT sentence_id, n, page, x, y, width, height FROM sentence_bb "
    "WHERE sentence_id IN "
        "(SELECT sentence_id FROM sentences WHERE "
        "ssid=%(ssid)s AND sentence_n >= %(sentence_start)s AND sentence_n <= %(sentence_end)s)"
)

INSERT_TAGGING_ENTRY = (
    "INSERT INTO tagging (user_email, ssid, last_edited) "
    "VALUES (%(user_email)s, %(ssid)s, %(last_edited)s)"
)


def render_and_generate_json(paper_id, email, conn):
    render_dir = os.path.join('tagger', 'render', paper_id)
    render_prefix = os.path.join(render_dir, 'img')
    json_filepath = os.path.join(render_dir, 'bb.json')
    
    if not os.path.isdir(render_dir): # already created
        cursor = conn.cursor()
        os.makedirs(render_dir)
        cursor.execute(GET_FILEPATH_FOR_SSID, {'ssid': paper_id})
        pdf_file = cursor.fetchall()[0][0]
        
        # actual rendering
        subprocess.run(['java', '-jar', 'tagger/pdfbox-app-2.0.14.jar', 'PDFToImage',
                       '-outputPrefix', render_prefix,
                        '-imageType', 'png',
                        '-dpi', '200',
                        pdf_file], stdout = subprocess.DEVNULL)
        
        # generating the json
        pages = {}
        cursor.execute(GET_PAGE_DIMENSIONS, {'ssid': paper_id})
        for n, width, height in cursor:
            pages[n] = [width, height]
        
        paragraphs = []
        paragraph_ids = set()
        cursor.execute(GET_ALL_PARAGRAPH_BBS, {'ssid': paper_id})
        for paragraph_id, n, page, x, y, width, height in cursor:
            paragraph_ids.add(paragraph_id)
            paragraphs.append({
                'paragraph_id': paragraph_id,
                'n': n,
                'page': page,
                'x': x / pages[page][0],
                'y': y / pages[page][1],
                'width': width / pages[page][0],
                'height': height / pages[page][1]
            })
            
        sentences = []
        for paragraph_id in paragraph_ids:
            cursor.execute(GET_PARAGRAPH_SENTENCE_BOUNDS, {
                'paragraph_id': paragraph_id
            })
            sentence_start, sentence_end = cursor.fetchall()[0]
            cursor.execute(GET_SENTENCES_FOR_BOUNDS, {
                'sentence_start': sentence_start,
                'sentence_end': sentence_end,
                'ssid': paper_id
            })
            for sentence_id, n, page, x, y, width, height in cursor:
                sentences.append({
                    'sentence_id': sentence_id,
                    'parent_id': paragraph_id,
                    'n': n,
                    'page': page,
                    'x': x / pages[page][0],
                    'y': y / pages[page][1],
                    'width': width / pages[page][0],
                    'height': height / pages[page][1]
                })
            
        all_bbs = {
            'paragraphs': paragraphs,
            'sentences': sentences
        }
        with open(json_filepath, 'w') as json_file:
            json.dump(all_bbs, json_file)
        
        # lock the paper into the current user
        cursor.execute(INSERT_TAGGING_ENTRY, {
            'user_email': email,
            'ssid': paper_id,
            'last_edited': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        conn.commit()
        cursor.close()
        
    n_pages = len(list(glob.glob(render_prefix + '*.png')))
    return n_pages

GET_EDITED_LIST = (
    "SELECT ssid FROM tagging WHERE user_email = %(email)s"
)

def get_edited_list(email, conn):
    cursor = conn.cursor(buffered = True)
    inner_cursor = conn.cursor()
    print('email: ', email)
    cursor.execute(GET_EDITED_LIST, {'email': email})
    papers = [{
            'ssid': ssid,
            'title': get_title_for_ssid(inner_cursor, ssid)
        } for ssid, in cursor]
    cursor.close()
    inner_cursor.close()
    return {'papers': papers}
