from tagger import create_tagger, socketio

tagger = create_tagger(debug=True)

if __name__ == '__main__':
    socketio.run(tagger)
