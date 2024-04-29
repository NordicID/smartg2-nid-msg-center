#!/usr/bin/python3

''' nid message center '''

import asyncio
import logging
import os
import nid_rpc

from msg_database import MsgDatabase

# pylint: disable=C0115 (missing-class-docstring)
# pylint: disable=C0116 (missing-function-docstring)
# pylint: disable=W0613 (unused-argument)

class MsgCenterServer:
    def __init__(self):
        path = None
        if os.path.isdir('webui_files'):
            path = os.path.abspath('webui_files')
        else:
            path = '/usr/lib/nid-web-api-backend-plugins/msgcenter'
        pages=[('msgcenter', 'index.html')]
        self.rpc = nid_rpc.NidRpcPlugin('builtin',
                                        'msgcenter',
                                        path, pages=pages)

        self.rpc.add_callback('/conf/get', self.conf_get)
        self.rpc.add_callback('/add', self.add)
        self.rpc.add_callback('/get', self.get)
        self.rpc.add_callback('/remove', self.remove)
        self.rpc.add_callback('/update', self.touch)
        self.rpc.freeze_api("1")

        self.msg_db = MsgDatabase()
        self.stop_event = asyncio.Event()

    def _valid_level(self, payload: dict) -> bool:
        valid = False
        if 'level' in payload:
            if payload['level'] == 'info':
                valid = True
            elif payload['level'] == 'warning':
                valid = True
            elif payload['level'] == 'error':
                valid = True
            elif payload['level'] == 'todo':
                valid = True
            else:
                valid = False
        return valid

    def _spam_detect(self, payload: dict) -> bool:
        spam = False
        spam_count = 0
        for _ in self.msg_db.get_id(payload):
            spam_count += 1
        if spam_count > 40:
            spam = True
        return spam

    def _remove_volatile(self) -> None:
        # Remove volatile notifications
        for msg in self.msg_db.all(None):
            if 'permanent' not in msg or not msg['permanent']:
                self.msg_db.remove_by_db_id(msg.doc_id, True)
                # print('Remove volatile msg:', msg['msg'])

    async def conf_get(self, payload: dict) -> dict:
        # print('conf_get:', payload)
        return {}

    async def add(self, payload: dict) -> dict:
        '''
        description: Add new notification.
        messages:
        - description: Get all or specific notifications
          payload:
            sender:
              description: notification sender name
              type: string
            id:
              description: notification id set by sender
              type: int
          responses:
          - title: List of notifications
            data: {}
        '''
        doc_id = None
        retval = {'doc_id': doc_id}
        if self._valid_level(payload):
            if 'permanent' not in payload:
                payload.update({'permanent': False})
            if 'sender' not in payload:
                payload.update({'sender': 'anonymous'})
            if 'id' not in payload:
                payload.update({'id': 0})
            if 'action' not in payload:
                payload.update({'action': {'api': None, 'params': None}})

            # SPAM filter: here:
            if self._spam_detect(payload):
                retval = {'warning': 'spam detected'}
            else:
                doc_id = self.msg_db.insert(payload)
                retval.update({'doc_id': doc_id})
        else:
            retval = {'error': 'not valid'}
        return retval

    async def get(self, payload: dict) -> dict:
        '''
        description: Get notifications.
        messages:
        - description: Get all or specific notifications
          payload:
            sender:
              description: notification sender name
              type: string
            id:
              description: notification id set by sender
              type: int
          responses:
          - title: List of notifications
            data: {}
        '''
        retval = {'error': 'syntax error'}
        msg_list = []

        if 'sender' in payload and 'id' in payload:
            for test in self.msg_db.get_id(payload):
                msg_list.append(test)
            retval = {'data': msg_list}
        else:
            for test in self.msg_db.all(None):
                msg = test
                msg.update({'doc_id': test.doc_id})
                msg_list.append(msg)
            retval = {'data': msg_list}
        return retval

    async def remove(self, payload: dict) -> dict:
        retval = {}
        if 'doc_id' in payload:
            doc_id = payload['doc_id']
            self.msg_db.remove_by_db_id(doc_id)
        elif 'sender' in payload and 'id' in payload:
            self.msg_db.remove_by_id(payload)
        return retval

    async def touch(self, payload: dict) -> dict:
        retval = {}
        if 'doc_id' in payload:
            self.msg_db.touch(payload)
        elif 'sender' in payload and 'id' in payload:
            self.msg_db.touch(payload)
        return retval

    async def run(self) -> None:
        self._remove_volatile()
        await self.rpc.connect()
        self.rpc.signal_startup_complete()
        await self.stop_event.wait()

def main() -> None:
    srv = MsgCenterServer()
    srv.rpc.filter_gmqtt_logs()
    tasks = asyncio.gather(srv.run())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tasks)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
