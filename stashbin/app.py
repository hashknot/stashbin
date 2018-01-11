#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import flask
import os
import constants
import stashbin

from flask import Flask, render_template, request, Response
from werkzeug import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = constants.UPLOAD_FOLDER

@app.route('/<identifier>', methods=['GET', 'POST'])
def handle_identifier(identifier):
    action = request.args.get('action')
    if action == 'download':
        return _download(identifier)
    elif action == 'delete':
        return _delete(identifier)
    elif action == 'upload':
        return _upload(identifier)
    else:
        return _default(identifier)

def _download(identifier):
    auth = request.authorization
    try:
        if auth:
            item = stashbin.get(identifier,
                                username=auth.username,
                                password=auth.password,
                                )
        else:
            item = stashbin.get(identifier)
    except stashbin.ItemNotFoundError:
        return flask.abort(404)
    except stashbin.AuthError:
        return _authenticate()
    return _initiate_download(item)

def _delete(identifier):
    auth = request.authorization
    try:
        if auth:
            item = stashbin.delete(identifier,
                                  username=auth.username,
                                  password=auth.password,
                                  key=request.args.get('key', None),
                                  )
        else:
            item = stashbin.delete(identifier, key=request.args.get('key', None))
    except stashbin.ItemNotFoundError:
        return flask.redirect('{}'.format(identifier))
    except stashbin.AuthError:
        return _authenticate()
    except stashbin.DeleteKeyError:
        return flask.abort(403)
    return flask.redirect('{}?status=deleted'.format(identifier))

def _upload(identifier):
    if request.method == 'POST':
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = secure_filename(file.filename)
            username = request.form['username']
            password = request.form['password']
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], identifier)
            file.save(filepath)

            item = stashbin.FileItem(identifier, name=filename, uri=filepath)

            if username and password:
                key = stashbin.stash(item, username=username, password=password)
            elif password:
                key = stashbin.stash(item, password=password)
            else:
                key = stashbin.stash(item)
            return flask.redirect('{}?status=uploaded&key={}'.format(identifier, key))
        else:
            return flask.redirect('{}'.format(identifier))

def _default(identifier):
    auth = request.authorization
    uploadNotify = (request.args.get('status') == 'uploaded')
    deleteNotify = (request.args.get('status') == 'deleted')
    key = request.args.get('key')
    try:
        if auth:
            stashbin.get(identifier,
                         username=auth.username,
                         password=auth.password,
                         )
        else:
            return stashbin.get(identifier)
    except stashbin.ItemNotFoundError:
        return render_template('upload.html', identifier=identifier, deleteNotify=deleteNotify)
    except stashbin.AuthError:
        return _authenticate()

    return render_template('download.html', identifier=identifier, uploadNotify=uploadNotify, key=key)

def _authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def _initiate_download(item):
    if os.path.exists(item.uri):
        return flask.send_file(item.uri, as_attachment=True,
                               attachment_filename=item.name)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
