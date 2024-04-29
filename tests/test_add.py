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
        self.fs.create_file("/systemrw/dummy", contents="XXX")
        self.srv = MsgCenterServer()

    def _add_retval_ok(self, retval):
        ret = False
        if 'doc_id' in retval:
            ret = True
        return ret

    async def test_get_all(self):
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
            self.assertTrue('doc_id' in msg)
            # print(msg['stamp'], msg['level'], msg['msg'])

    async def test_get_id(self):
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
        payload.update({'id': 677})
        msg_list = await self.srv.get(payload)
        self.assertTrue('data' in msg_list)
        self.assertFalse(msg_list['data'])

if __name__=='__main__':
    unittest.main()
