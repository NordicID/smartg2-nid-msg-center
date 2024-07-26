''' message center database interface '''

import time
from enum import IntEnum
from tinydb import TinyDB, Query
import os.path
import uuid

# pylint: disable=C0115 (missing-class-docstring)
# pylint: disable=C0116 (missing-function-docstring)
# pylint: disable=W0613 (unused-argument)

State = IntEnum('State', ['NEW', 'READ'])

class MsgDatabase:
    def __init__(self, deviceName: str):
        dbPath = '/systemrw/nid/msgcenter_db.json'
        dbExists = os.path.isfile(dbPath)
        self.tinydb = TinyDB(dbPath)
        self.callBacks = []
        if(dbExists == False):
            payload = {
                'level': 'reset',
                'sender': 'system',
                'msg': 'Welcome to ' + deviceName + '!',
                'permanent': True,
                'uuid': 'welcome'
            }
            self.insert(payload)
        self.stateChanged = True

    def _create_uuid(self) -> str:
        return uuid.uuid4().hex

    def insert(self, payload: dict) -> int:
        stamp = time.clock_gettime(0)
        payload.update({'stamp': stamp})
        payload.update({'state': State.NEW})
        if 'uuid' not in payload or not payload['uuid']:
            uuid = self._create_uuid()
            payload.update({'uuid': uuid})
        msg = Query()
        self.tinydb.upsert(payload, (msg.uuid == payload['uuid']))
        self.state_changed = True
        self.notify()
        return payload['uuid']
    
    def search(self, payload: dict) -> dict:
        msg = Query()
        
        if 'uuid' in payload:
            query = (msg.uuid == payload['uuid'])
        elif 'sender' in payload:
            query = (msg.sender == payload['sender'])
        
        return self.tinydb.search(query)

    def all(self) -> dict:
        return self.tinydb.all()

    def remove(self, payload: dict, force=False) -> None:
        msg = Query()
        if 'uuid' in payload:
            self.tinydb.remove(msg.uuid == payload['uuid'])
        self.notify()

    def touch(self, payload: dict) -> None:
        msg = Query()
        query = (msg.uuid == payload['uuid'])
        self.tinydb.update({'state': State.READ}, query)
        if 'msg' in payload:
            self.tinydb.update({'msg': payload['msg']}, query)
        self.notify()

    def register_callback(self, observerCallback):
        if observerCallback != None:
            self.callBacks.append(observerCallback)

    def notify(self):
        for cb in self.callBacks:
            cb()
        
