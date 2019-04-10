from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_tagger(debug = False):
    tagger = Flask(__name__)
    tagger.debug = debug
    tagger.config['SECRET_KEY'] = 'temporary' # change this!

    from .main import main as main_blueprint
    from .main import close_connection
    
    tagger.register_blueprint(main_blueprint)
    tagger.teardown_appcontext(close_connection)

    socketio.init_app(tagger)
    return tagger
