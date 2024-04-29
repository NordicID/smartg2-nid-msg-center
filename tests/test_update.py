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

    async def test_update_msg_by_doc_id(self):
        old_msg = 'this is old message, please forget'
        new_msg = 'this is shiny new message, use this'
        payload = {'level': 'info', 'msg': old_msg, 'permanent': False}
        retval = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(retval))
        doc_id = retval['doc_id']

        msg_list = await self.srv.get({})
        self.assertTrue('data' in msg_list)
        self.assertTrue('msg' in msg_list['data'][0])
        entry = msg_list['data'][0]
        # print('OLD:', entry['msg'])
        self.assertTrue(entry['msg'] == old_msg)
        payload.update({'doc_id': doc_id})
        payload.update({'msg': new_msg})
        await self.srv.touch(payload)

        msg_list = await self.srv.get({})
        self.assertTrue('data' in msg_list)
        self.assertTrue('msg' in msg_list['data'][0])
        entry = msg_list['data'][0]
        # print('NEW:', entry['msg'])
        self.assertTrue(entry['msg'] == new_msg)

    async def test_update_msg_by_sender_id(self):
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
        self.assertTrue('msg' in msg_list['data'][0])
        entry = msg_list['data'][0]
        # print('OLD:', entry['msg'])
        self.assertTrue(entry['msg'] == old_msg)
        payload.update({'msg': new_msg})
        await self.srv.touch(payload)

        msg_list = await self.srv.get({})
        self.assertTrue('data' in msg_list)
        self.assertTrue('msg' in msg_list['data'][0])
        entry = msg_list['data'][0]
        # print('NEW:', entry['msg'])
        self.assertTrue(entry['msg'] == new_msg)

if __name__=='__main__':
    unittest.main()
