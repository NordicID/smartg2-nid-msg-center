''' message center database interface '''

import time
from enum import IntEnum
from tinydb import TinyDB, Query
import os.path
import uuid
from nid_rpc import NidRpcClient

# pylint: disable=C0115 (missing-class-docstring)
# pylint: disable=C0116 (missing-function-docstring)
# pylint: disable=W0613 (unused-argument)

State = IntEnum('State', ['NEW', 'READ', 'REMOVED'])

class MsgDatabase:
    def __init__(self, deviceName: str):
        dbPath = '/systemrw/nid/msgcenter_db.json'
        dbExists = os.path.isfile(dbPath)
        self.tinydb = TinyDB(dbPath)
        if(dbExists == False):
            payload = {
                'level': 'reset',
                'sender': 'system',
                'id': 0,
                'msg': 'Welcome to ' + deviceName + '!',
                'permanent': True
            }
            self.insert(payload)

    def __createUUID(self) -> str:
        return uuid.uuid4().hex

    def insert(self, payload: dict) -> int:
        stamp = time.clock_gettime(0)
        payload.update({'stamp': stamp})
        payload.update({'state': State.NEW})
        if 'uuid' not in payload or not payload['uuid']:
            uuid = self.__createUUID()
            payload.update({'uuid': uuid})
        self.tinydb.insert(payload)
        return payload['uuid']

    def search(self, payload: dict) -> dict:
        msg = Query()
        query = (msg.level == payload['level']) \
            & (msg.state != State.REMOVED)
        return self.tinydb.search(query)

    def get_id(self, payload: dict) -> dict:
        msg = Query()
        query = (msg.id == payload['id']) \
            & (msg.sender == payload['sender']) \
            & (msg.state != State.REMOVED)
        return self.tinydb.search(query)
    
    def get_uuid(self, payload: dict) -> dict:
        msg = Query()
        query = (msg.uuid == payload['uuid'])
        return self.tinydb.search(query)

    def all(self, payload: dict) -> dict:
        msg = Query()
        return self.tinydb.search(msg.state != State.REMOVED)

    def remove(self, payload: dict, force=False) -> None:
        msg = Query()
        self.tinydb.remove(msg.uuid == payload['uuid'])

    def touch(self, payload: dict) -> None:
        msg = Query()
        query = (msg.uuid == payload['uuid'])
        self.tinydb.update({'state': State.READ}, query)
        if 'msg' in payload:
            self.tinydb.update({'msg': payload['msg']}, query)
