from unittest import IsolatedAsyncioTestCase
from pyfakefs.fake_filesystem_unittest import TestCase

from msg_database import MsgDatabase

# pylint: disable=C0115 (missing-class-docstring)
# pylint: disable=C0116 (missing-function-docstring)
# pylint: disable=W0212 (protected-access)

class TestClass(TestCase, IsolatedAsyncioTestCase):
    ''' Unit testing class '''
    def setUp(self):
        self.setUpPyfakefs()
        self.fs.create_file("/systemrw/nid/dummy", contents="XXX")
        self.db = MsgDatabase('')
        self.cb_called = False

    def callBack(self):
        self.cb_called = True

    async def test_remove_volatile(self):
        self.db.register_callback(self.callBack)

        # Case 1: callback should be called when insert is called
        self.assertFalse(self.cb_called)
        self.db.insert({})
        self.assertTrue(self.cb_called)

        # reset
        self.cb_called = False

        # Case 1: callback should be called when remove is called
        self.assertFalse(self.cb_called)
        self.db.remove({})
        self.assertTrue(self.cb_called)