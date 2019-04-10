from flask import (
    Blueprint, flash, request, g, redirect,
    render_template, session, url_for, send_from_directory,
    jsonify
)
import json
import functools
import os
from . import serve_paper, main, get_connection

with open("tagger/.users.json") as userfile:
    creds = json.load(userfile)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.email is None:
            return redirect('/')
        return view(**kwargs)
    return wrapped_view



@main.before_app_request
def load_creds():
    g.email = session.get('email')
    g.fullname = session.get('fullname')
    
@main.route('/', methods=('GET', 'POST'))
def start():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email not in creds['users']:
            flash('Email not found.')
        elif password != creds['password']:
            flash('Password incorrect.')
        else:
            session['email'] = email
            session['fullname'] = creds['users'][email]
            return redirect('/edit')
    return render_template('start.html')
    
@main.route('/edit', methods=('GET', 'POST'))
@login_required
def new_tag():
    # try to find the last opened paper and return to the user
    paper_id = serve_paper.get_last_edited_paper(g.email, get_connection())
    # if it isn't found, give a random paper that has already been processed
    if paper_id is None:
        paper_id, _ = serve_paper.get_unedited_paper(get_connection())
    return redirect('/edit/' + paper_id)

@main.route('/edit/<string:paper_id>', methods=('GET', 'POST'))
@login_required
def tag_paper(paper_id):
    # render pages if they don't already exist in the ./renders folder
    g.num_images = serve_paper.render_and_generate_json(paper_id, g.email, get_connection())
    g.ssid = paper_id
    return render_template('tagging.html')
    
    
@main.route('/tagimgs/<string:ssid>/<int:n>')
@login_required
def get_rendered_image(ssid, n):
    return send_from_directory('render', os.path.join(ssid, 'img%d.png' % n))

@main.route('/tagbbs/<string:ssid>')
@login_required
def get_bb_json(ssid):
    return send_from_directory('render', os.path.join(ssid, 'bb.json'))

@main.route('/edit_list')
@login_required
def get_edited_papers():
    return jsonify(serve_paper.get_edited_list(g.email, get_connection()))

@main.route('/logout')
def logout():
    session.clear()
    return redirect('/')
