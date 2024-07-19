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
        self.testDevName = 'Test-Device'

    def _add_retval_ok(self, retval):
        ret = False
        if 'uuid' in retval:
            ret = True
        return ret

    async def test_remove_volatile(self):
        await self.srv.initDatabase(self.testDevName)
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

    async def test_remove(self):
        await self.srv.initDatabase(self.testDevName)
        payload = {
            'level': 'info',
            'sender': 'unittest',
            'id': 777,
            'msg': 'testing: to remove specific message'
        }

        # add message two time (should remove both)
        first = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(first))
        
        second = await self.srv.add(payload)
        self.assertTrue(self._add_retval_ok(second))

        # remove my messages from the database
        await self.srv.remove(first)
        await self.srv.remove(second)

        # should return an empty list
        msg_list = await self.srv.get(first)
        self.assertTrue('data' in msg_list)
        self.assertFalse(msg_list['data'])


if __name__=='__main__':
    unittest.main()
