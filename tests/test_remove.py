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
        self.srv = MsgCenterServer()

    def _add_retval_ok(self, retval):
        ret = False
        if 'doc_id' in retval:
            ret = True
        return ret

    async def test_remove_volatile(self):
        payload = {'level': 'warning',
                   'msg': 'just testing',
                   'permanent': False}

        # add a couple of volatile messages first
        for _ in range(10):
            retval = await self.srv.add(payload)
            self.assertTrue(self._add_retval_ok(retval))

        # then add some permanent messages
        payload.update({'permanent': True})
        for _ in range(10):
            retval = await self.srv.add(payload)
            self.assertTrue(self._add_retval_ok(retval))

        # execute routine that should remove if not tagged permanent
        self.srv._remove_volatile()

        # only permanent should the available at the list
        msg_list = await self.srv.get({})
        self.assertTrue('data' in msg_list)
        for msg in msg_list['data']:
            self.assertTrue(msg['permanent'])

    async def test_remove_by_db_id(self):
        payload = {'level': 'warning', 'msg': 'just testing: remove'}
        new_list = []

        # add a couple of messages, save doc_ids into list
        for _ in range(10):
            retval = await self.srv.add(payload)
            self.assertTrue(self._add_retval_ok(retval))
            new_list.append(retval['doc_id'])
            # print("add:", retval['doc_id'])

        # remove massages using listed doc_ids
        payload = {'doc_id': None}
        for doc_id in new_list:
            payload['doc_id'] = doc_id
            retval = await self.srv.remove(payload)
            self.assertTrue(retval == {})
            # print("remove:", doc_id)

        # should return a list with 1 entry
        msg_list = await self.srv.get({})
        self.assertTrue('data' in msg_list)
        self.assertTrue(len(msg_list['data']) == 1)

    async def test_remove_by_id(self):
        payload = {
            'level': 'info',
            'sender': 'unittest',
            'id': 777,
            'msg': 'testing: to remove specific message'
        }

        # add message two time (should remove both)
        retval = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(retval))
        retval = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(retval))

        # remove my messages from the database
        retval = await self.srv.remove(payload)
        self.assertTrue(retval == {})

        # should return an empty list
        msg_list = await self.srv.get(payload)
        self.assertTrue('data' in msg_list)
        self.assertFalse(msg_list['data'])

if __name__=='__main__':
    unittest.main()
