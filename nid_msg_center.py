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
        pages = ('msgcenter', 'index.html', '/System/Notifications[fa-envelope]')

        self.rpc = nid_rpc.NidRpcPlugin('builtin',
                                        'msgcenter',
                                        path, 
                                        pages=pages)

        self.rpc.add_callback('/conf/get', self.conf_get)
        self.rpc.add_callback('/add', self.add)
        self.rpc.add_callback('/get', self.get)
        self.rpc.add_callback('/remove', self.remove)
        self.rpc.add_callback('/update', self.touch)
        self.rpc.freeze_api("1")

        self.stop_event = asyncio.Event()

    async def init_database(self, devName=None):
        if not devName:
            devName = await self._get_device_name()
        self.msg_db = MsgDatabase(devName)

    async def _get_device_name(self, timeout=10) -> str:
        devName = ''
        while(timeout):
            res = await self.rpc.call('api/builtin/settings/persistent/get', {})
            if 'nid-device-name' in res:
                devName = res['nid-device-name']
            await asyncio.sleep(1)
            timeout -= 1
        return devName

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

    def _remove_volatile(self) -> None:
        # Remove volatile notifications
        for msg in self.msg_db.all(None):
            if 'permanent' not in msg or not msg['permanent']:
                self.msg_db.remove(msg, True)
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

        retval = {}
        if self._valid_level(payload):
            if 'permanent' not in payload:
                payload.update({'permanent': False})
            if 'sender' not in payload:
                payload.update({'sender': 'anonymous'})
            if 'id' not in payload:
                payload.update({'id': 0})
            if 'action' not in payload:
                payload.update({'action': {'api': None, 'params': None}})

            uuid = self.msg_db.insert(payload)
            retval.update({'uuid': uuid})
        else:
            retval = {'error': 'not valid'}
        return retval

    async def get(self, payload: dict) -> dict:
        '''
        description: Get notifications.
        messages:
        - description: Get all or specific notifications
          payload:
            uuid:
              description: universal unique identifier of the message
              type: string
            sender:
              description: sender name
              type: string
          responses:
          - title: List of notifications
            data: {}
        '''
        retval = {'error': 'syntax error'}
        msg_list = []
        try:
            if 'uuid' in payload or 'sender' in payload:
                for test in self.msg_db.search(payload):
                    msg_list.append(test)
                retval = {'data': msg_list}
            else:
                for test in self.msg_db.all(None):
                    msg = test
                    msg_list.append(msg)
                retval = {'data': msg_list}
        except AttributeError:
            retval = {'error': 'message database not initialized'}
        return retval

    async def remove(self, payload: dict) -> dict:
        retval = {}
        if 'uuid' in payload:
            self.msg_db.remove(payload)
        elif 'uuids' in payload:
            for item in payload['uuids']:
                self.msg_db.remove({'uuid': item})
        else:
            retval = {'error': 'uuid missing'}
        return retval

    async def touch(self, payload: dict) -> dict:
        retval = {}
        if 'uuid' in payload:
            self.msg_db.touch(payload)
        elif 'uuids' in payload:
            for item in payload['uuids']:
                self.msg_db.touch({'uuid': item})
        else:
            retval = {'error': 'uuid missing'}
        return retval

    async def run(self) -> None:
        await self.rpc.connect()
        await self.init_database()
        self.rpc.signal_startup_complete()
        self._remove_volatile()
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
