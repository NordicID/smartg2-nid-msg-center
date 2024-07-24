import unittest
import asyncio
from unittest import IsolatedAsyncioTestCase
from pyfakefs.fake_filesystem_unittest import TestCase
from unittest.mock import patch
from nid_rpc import NidRpcClient

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
        self.testDevName = 'this-is-a-test-device'

    async def test_create(self):
        with patch.object(NidRpcClient, 'call',
                          side_effect=self.mock_rpc_call) as mock_method:
            testObj = MsgCenterServer()
            await testObj.init_database()
            self.assertTrue(self.check_call_args('api/builtin/settings/persistent/get', mock_method.call_args_list))
            msg_list = await testObj.get([])
            entry = msg_list['data'][0]
            print(msg_list)
            self.assertTrue(self.testDevName in entry['msg'])

    def mock_rpc_call(self, *args, **kwargs):
        return {'nid-device-name': self.testDevName}
    
    def check_call_args(self, expected_arg, call_args_list):
        ret = False
        for call in call_args_list:
            args, _ = call
            if any(expected_arg in arg for arg in args):
                    ret = True
                    break
        return ret