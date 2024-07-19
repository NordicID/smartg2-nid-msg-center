import unittest
import asyncio
from unittest import IsolatedAsyncioTestCase
from pyfakefs.fake_filesystem_unittest import TestCase

from nid_msg_center import MsgCenterServer

# pylint: disable=C0115 (missing-class-docstring)
# pylint: disable=C0116 (missing-function-docstring)
# pylint: disable=W0212 (protected-access)

class TestClass(TestCase, IsolatedAsyncioTestCase):
    ''' Unit testing class '''
    def setUp(self):
        ''' Setup unittest object '''
        self.setUpPyfakefs()
        self.fs.create_file("/systemrw/nid/dummy", contents="XXX")
        self.testDevName = "TestDevice"
        self.srv = MsgCenterServer()

    def _add_retval_ok(self, retval):
        ret = False
        if 'uuid' in retval:
            ret = True
        return ret

    async def test_get_all(self):
        await self.srv.initDatabase(self.testDevName)
        payload = {
            'level': 'info',
            'sender': 'unittest',
            'id': 555,
            'msg': 'just testing'
        }

        # add some messages
        for _ in range(10):
            retval = await self.srv.add(payload)
            self.assertTrue(self._add_retval_ok(retval))

        # try to read the list
        msg_list = await self.srv.get({})
        self.assertTrue('data' in msg_list)
        for msg in msg_list['data']:
            self.assertTrue('stamp' in msg)
            self.assertTrue('level' in msg)
            self.assertTrue('sender' in msg)
            self.assertTrue('id' in msg)
            self.assertTrue('msg' in msg)
            self.assertTrue('uuid' in msg)
            # print(msg['stamp'], msg['level'], msg['msg'])

    async def test_get_uuid(self):
        await self.srv.initDatabase(self.testDevName)
        payload = {
            'level': 'info',
            'sender': 'unittest',
            'id': 777,

            'msg': 'testing: to get specific message'
        }
        retval = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(retval))

        # ok case: should return a list
        msg_list = await self.srv.get(payload)
        self.assertTrue('data' in msg_list)
        self.assertTrue('msg' in msg_list['data'][0])

        # not nok case: should return an empty list
        payload.update({'uuid': 677})
        msg_list = await self.srv.get(payload)
        self.assertTrue('data' in msg_list)
        self.assertFalse(msg_list['data'])

    async def test_welcome_message_created(self):
        await self.srv.initDatabase(self.testDevName)
        msg_list = await self.srv.get([])
        self.assertTrue('data' in msg_list)
        self.assertTrue('msg' in msg_list['data'][0])
        entry = msg_list['data'][0]
        self.assertTrue(entry['level'] == 'reset')
        self.assertTrue(entry['sender'] == 'system')
        self.assertTrue(self.testDevName in entry['msg'])
        self.assertTrue(entry['id'] == 0)
        self.assertTrue(entry['uuid'] != None)

    async def test_creates_uuid(self):
        await self.srv.initDatabase(self.testDevName)
        payload = {
            'level': 'info',
            'sender': 'unittest',
            'id': 777,
            'msg': 'testing: to get specific message'
        }

        # Case 1: should create a new uuid as it is not in message
        retval = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(retval))

        msg_list = await self.srv.get(retval)
        self.assertTrue('data' in msg_list)
        self.assertTrue('uuid' in msg_list['data'][0])
        self.assertTrue(msg_list['data'][0]['uuid'] == retval['uuid'])

        # Case 2: should use provided uuid value
        new_uuid = 42
        payload.update({'uuid': new_uuid})
        retval = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(retval))

        msg_list = await self.srv.get(retval)
        self.assertTrue('data' in msg_list)
        self.assertTrue('uuid' in msg_list['data'][0])
        self.assertTrue(msg_list['data'][0]['uuid'] == new_uuid)

        # Case 3: should create a new uuid as it is empty
        empty_uuid = ''
        payload.update({'uuid': empty_uuid})
        retval = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(retval))

        msg_list = await self.srv.get(retval)
        self.assertTrue('data' in msg_list)
        self.assertTrue('uuid' in msg_list['data'][0])
        self.assertTrue(msg_list['data'][0]['uuid'] != empty_uuid)
        self.assertTrue(msg_list['data'][0]['uuid'] == retval['uuid'])

        # Case 4: should create a new uuid as it is None
        none_uuid = None
        payload.update({'uuid': none_uuid})
        retval = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(retval))

        msg_list = await self.srv.get(retval)
        self.assertTrue('data' in msg_list)
        self.assertTrue('uuid' in msg_list['data'][0])
        self.assertTrue(msg_list['data'][0]['uuid'] != none_uuid)
        self.assertTrue(msg_list['data'][0]['uuid'] == retval['uuid'])


if __name__=='__main__':
    unittest.main()
