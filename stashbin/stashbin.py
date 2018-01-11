#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import hashlib
import uuid
from constants import *

from pymongo import MongoClient

class StashbinError(Exception):
    pass

class ItemNotFoundError(StashbinError):
    pass

class AuthError(StashbinError):
    pass

class DeleteKeyError(StashbinError):
    pass

class Item(object):
    _type = {}
    def __init__(self, identifier):
        self.identifier = identifier

    @staticmethod
    def factory(type):
        return Item._type[type]

    def getDocument(self):
        return {'identifier': self.identifier}

    def upload(self):
        pass

    def remove(self):
        pass

    @staticmethod
    def build(document):
        return Item(document['identifier'])

class FileItem(Item):
    def __init__(self, identifier, name=None, uri=None):
        super(FileItem, self).__init__(identifier)
        self.name = name
        self.uri = uri

    def getDocument(self):
        doc = super(FileItem, self).getDocument()
        doc['type'] = 'file'
        doc['name'] = self.name
        doc['uri'] = self.uri
        return doc

    def upload(self):
        pass

    @staticmethod
    def build(document):
        return FileItem(document['identifier'],
                        name=document['name'],
                        uri=document['uri'])

Item._type['file'] = FileItem

class Stashbin(object):
    def __init__(self):
        connStr = 'mongodb://{}:{}@{}/{}'.format(MONGO_DB_USERNAME, MONGO_DB_PASSWORD, MONGO_DB_HOST, MONGO_DB_NAME)
        self._itemsCollection = MongoClient(connStr)[MONGO_DB_NAME]['items']

    def _hash(self, string):
        return hashlib.sha1(string).hexdigest()

    def get(self, identifier, username=None, password=None):
        try:
            cursor = self._itemsCollection.find({'identifier': identifier})
            doc = cursor.next()
        except StopIteration:
            raise ItemNotFoundError

        u = doc.get('username', '')
        p = doc.get('password', '')

        if u and (username != u):
            raise AuthError
        if p and (self._hash(password) != p):
            raise AuthError

        return Item.factory(doc['type']).build(doc)

    def stash(self, item, username=None, password=None):
        item.upload()
        document = item.getDocument()
        if username:
            document['username'] = username
        if password:
            document['password'] = self._hash(password)
        key = uuid.uuid1().hex
        document['key'] = key
        self._itemsCollection.insert_one(document)
        return key

    def delete(self, identifier, username=None, password=None, key=None):
        try:
            cursor = self._itemsCollection.find({'identifier': identifier})
            doc = cursor.next()
        except StopIteration:
            raise ItemNotFoundError

        u = doc.get('username', '')
        p = doc.get('password', '')
        k = doc.get('key')

        if u or p:
            if u and username != u:
                raise AuthError
            if p and self._hash(password) != p:
                raise AuthError
        else:
            if k != key:
                raise DeleteKeyError

        item = Item.factory(doc['type']).build(doc)
        self._itemsCollection.delete_one({"identifier": identifier})
        item.remove()

_stashbin = Stashbin()
def get(identifier, username=None, password=None):
    return _stashbin.get(identifier, username=username, password=password)

def stash(item, username=None, password=None):
    return _stashbin.stash(item, username=username, password=password)

def delete(identifier, username=None, password=None, key=None):
    return _stashbin.delete(identifier, username=username, password=password, key=key)
