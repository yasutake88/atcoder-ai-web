import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock
from public_budget import run_sponsored, actual_micro_usd, OUTPUT_LIMIT

class SponsoredTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(admin_code='dummy', url='https://test.supabase.co', key='sb_secret_test')
        self.count = Mock(return_value=1000)
        self.generate = Mock(return_value=('answer', None, True))
        self.rpc = Mock(return_value={'allowed': True})
    def run_request(self, **kwargs):
        return run_sponsored(self.config, 'test-key', 'problem', False,
            self.count, self.generate, rpc_call=self.rpc, today=date(2026,11,8), **kwargs)
    def test_high_fixed(self):
        answer, usage, pending = self.run_request()
        self.assertEqual(self.generate.call_args.args[4:6], ('high', OUTPUT_LIMIT))
        self.assertEqual(self.rpc.call_args.args[2]['p_is_owner'], False)
        self.assertTrue(pending['p_completed'])
    def test_denial_never_calls_ai(self):
        for reason in ('budget', 'busy', 'disabled', 'duplicate'):
            self.rpc.return_value = {'allowed':False,'reason':reason}
            with self.assertRaises(ValueError): self.run_request()
        self.generate.assert_not_called()
    def test_database_outage_never_calls_ai(self):
        self.rpc.side_effect=TimeoutError()
        with self.assertRaises(TimeoutError): self.run_request()
        self.generate.assert_not_called()
    def test_timeout_no_refund_or_retry(self):
        self.generate.side_effect=TimeoutError()
        with self.assertRaises(TimeoutError): self.run_request()
        self.assertEqual(self.generate.call_count,1)
        self.assertEqual(self.rpc.call_count,1)
    def test_oversize_input_no_reservation(self):
        self.count.return_value=20001
        with self.assertRaises(ValueError): self.run_request()
        self.rpc.assert_not_called()
        self.generate.assert_not_called()
    def test_missing_key_closed(self):
        with self.assertRaises(ValueError):
            run_sponsored(self.config,'','prompt',False,self.count,self.generate,today=date(2026,11,8))
        self.count.assert_not_called()
    def test_price_expiry_closed(self):
        with self.assertRaises(ValueError):
            run_sponsored(self.config,'key','prompt',False,self.count,self.generate,today=date(2027,2,1))
        self.count.assert_not_called()
    def test_unknown_usage_keeps_reservation(self):
        self.assertIsNone(actual_micro_usd(None))
        self.assertIsNone(actual_micro_usd(SimpleNamespace(total_input_tokens=1,total_output_tokens=2)))
    def test_thinking_in_cost(self):
        usage=SimpleNamespace(total_input_tokens=1000,total_output_tokens=2000,total_thought_tokens=3000)
        self.assertEqual(actual_micro_usd(usage),39000)
    def test_redaction_and_incomplete(self):
        self.generate.return_value=('echo test-key',None,False)
        answer, _, payload=self.run_request()
        self.assertNotIn('test-key',answer)
        self.assertFalse(payload['p_completed'])

if __name__ == '__main__': unittest.main()
