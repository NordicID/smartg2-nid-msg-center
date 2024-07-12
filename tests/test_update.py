import unittest
import asyncio
from enum import IntEnum
from unittest import IsolatedAsyncioTestCase
from pyfakefs.fake_filesystem_unittest import TestCase

from nid_msg_center import MsgCenterServer

# pylint: disable=C0115 (missing-class-docstring)
# pylint: disable=C0116 (missing-function-docstring)
# pylint: disable=W0212 (protected-access)

State = IntEnum('State', ['NEW', 'READ', 'REMOVED'])

class TestClass(TestCase, IsolatedAsyncioTestCase):
    ''' Unit testing class '''
    def setUp(self):
        ''' Setup unittest object '''
        self.setUpPyfakefs()
        self.fs.create_file("/systemrw/nid/dummy", contents="XXX")
        self.srv = MsgCenterServer()

    def _add_retval_ok(self, retval):
        ret = False
        if 'uuid' in retval:
            ret = True
        return ret

    async def test_update_msg_by_uuid(self):
        old_msg = 'this is old message, please forget'
        new_msg = 'this is shiny new message, use this'
        payload = {
            'level': 'info',
            'sender': 'unittest',
            'id': 123,
            'msg': old_msg,
            'permanent': False
        }

        retval = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(retval))

        msg_list = await self.srv.get({})
        self.assertTrue('data' in msg_list)
        self.assertTrue('msg' in msg_list['data'][1])
        entry = msg_list['data'][1]
        self.assertTrue(entry['msg'] == old_msg)
        payload.update({'msg': new_msg})
        await self.srv.touch(payload)

        msg_list = await self.srv.get({})
        self.assertTrue('data' in msg_list)
        self.assertTrue('msg' in msg_list['data'][1])
        entry = msg_list['data'][1]
        self.assertTrue(entry['msg'] == new_msg)

    async def test_should_add_and_read_message(self):
        payload = {
            'level': 'info',
            'sender': 'unittest',
            'id': 555,
            'msg': 'just testing'
        }

        # add message
        uuid = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(uuid))

        # try to read the message
        msg_list = await self.srv.get(uuid)
        self.assertTrue('data' in msg_list)
        for msg in msg_list['data']:
            self.assertTrue('stamp' in msg)
            self.assertTrue('level' in msg)
            self.assertTrue('sender' in msg)
            self.assertTrue('id' in msg)
            self.assertTrue('msg' in msg)
            self.assertTrue('uuid' in msg)
            self.assertTrue('state' in msg)

        msg = await self.srv.get(uuid)
        self.assertTrue(msg['data'][0]['state'] == State.NEW)

        await self.srv.touch(uuid)

        # State should be updated to read after touch
        msg = await self.srv.get(uuid)
        self.assertTrue(msg['data'][0]['state'] == State.READ)

if __name__=='__main__':
    unittest.main()
