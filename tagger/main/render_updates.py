from flask import g
from .. import socketio
from . import get_connection
from . import serve_paper

@socketio.on('request new paper')
def handle_new_paper(json):
    socketio.emit('render request received', {})
    conn = get_connection()
    new_paper, new_title = serve_paper.get_unedited_paper(conn)
    socketio.emit('render started', {
        'ssid': new_paper,
        'title': new_title,
        'timestamp': json['timestamp']
    })
    serve_paper.render_and_generate_json(new_paper, json['email'], conn)
    socketio.emit('render finished', {'ssid': new_paper})
