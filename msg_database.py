''' message center database interface '''

import time
from enum import IntEnum
from tinydb import TinyDB, Query
import os.path

# pylint: disable=C0115 (missing-class-docstring)
# pylint: disable=C0116 (missing-function-docstring)
# pylint: disable=W0613 (unused-argument)

State = IntEnum('State', ['NEW', 'READ', 'REMOVED'])

class MsgDatabase:
    def __init__(self):
        dbPath = '/systemrw/nid/msgcenter_db.json'
        dbExists = os.path.isfile(dbPath)
        self.tinydb = TinyDB(dbPath)
        if dbExists == False:
            payload = {
                'level': 'reset',
                'sender': 'system',
                'id': 0,
                'msg': 'welcome'
            }
            self.insert(payload)

    def insert(self, payload: dict) -> int:
        stamp = time.clock_gettime(0)
        payload.update({'stamp': stamp})
        payload.update({'state': State.NEW})
        doc_id = self.tinydb.insert(payload)
        return doc_id

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

    def all(self, payload: dict) -> dict:
        msg = Query()
        return self.tinydb.search(msg.state != State.REMOVED)

    def remove_by_db_id(self, doc_id: int, force=False) -> None:
        if force:
            self.tinydb.remove(doc_ids=[doc_id])
        else:
            self.tinydb.update({'state': State.REMOVED}, doc_ids=[doc_id])

    def remove_by_id(self, payload: dict, force=False) -> None:
        msg = Query()
        query = (msg.id == payload['id']) \
            & (msg.sender == payload['sender'])
        msg_list = self.tinydb.search(query)
        remove_list = []
        for msg in msg_list:
            remove_list.append(msg.doc_id)
        self.tinydb.update({'state': State.REMOVED}, doc_ids=remove_list)

    def touch(self, payload: dict) -> None:
        doc_ids = []
        if 'doc_id' in payload:
            doc_ids.append(payload['doc_id'])
        elif 'sender' in payload and 'id' in payload:
            msg = Query()
            query = (msg.id == payload['id']) \
                & (msg.sender == payload['sender'])
            msg_list = self.tinydb.search(query)
            for msg in msg_list:
                doc_ids.append(msg.doc_id)
        self.tinydb.update({'state': State.READ}, doc_ids=doc_ids)
        if 'msg' in payload:
            self.tinydb.update({'msg': payload['msg']}, doc_ids=doc_ids)
