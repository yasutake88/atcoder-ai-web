import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace as NS
from uuid import uuid4

import core
import counter
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'streamlit_app.py')
CONFIG = {'admin_code': '9876', 'url': 'https://test-project.supabase.co', 'key': 'sb_secret_test'}
USAGE = NS(input_tokens=932, output_tokens=1686, input_tokens_details=NS(cached_tokens=0))


class CounterTests(unittest.TestCase):
    def test_currency(self):
        text = core.usage_cost('OpenAI', USAGE, (2, .1, 10), 160)
        self.assertIn('0.0187240', text)
        self.assertIn('約3.00円', text)
        self.assertIn('160円', text)
        self.assertIn('約3.01円', core.usage_cost('OpenAI', USAGE, (2, .1, 10), 161))
        self.assertNotIn('約', core.usage_cost('OpenAI', None, (2, .1, 10), 160))

    def test_identity(self):
        self.assertTrue(counter.classify('9876', CONFIG))
        self.assertFalse(counter.classify('', CONFIG))
        for code in ('bad', '９８７６'):
            with self.assertRaises(ValueError): counter.classify(code, CONFIG)
        self.assertFalse(counter.configured({**CONFIG, 'admin_code': ''}))
        self.assertFalse(counter.configured({**CONFIG, 'url': 'https://attacker.invalid'}))

    def test_rpc_payload_and_validation(self):
        request_id = str(uuid4())
        with patch('counter.requests.post') as post:
            response = post.return_value.__enter__.return_value
            response.status_code = 200
            response.json.return_value = {'owner': 2, 'others': 3, 'total': 5}
            self.assertEqual(counter.record_success(CONFIG, request_id, True)['total'], 5)
            self.assertEqual(post.call_args.kwargs['json'], {'p_request_id': request_id, 'p_is_owner': True})
            self.assertFalse(post.call_args.kwargs['allow_redirects'])
            response.json.return_value['total'] = 6
            with self.assertRaises(ValueError): counter.record_success(CONFIG, request_id, True)

    def test_generation_status(self):
        with patch('openai.OpenAI') as client:
            c = client.return_value.__enter__.return_value
            for status, text, expected in [('completed','OK',True), ('completed','',False), ('incomplete','partial',False), ('failed','message',False)]:
                c.responses.create.return_value = NS(output_text=text, usage=USAGE, status=status)
                result = core.generate('OpenAI','model','test','p','指定なし',1024,with_status=True)
                self.assertEqual(result[2], expected)

    def app(self, code=''):
        a = AppTest.from_file(APP).run()
        a.radio[0].set_value('解答生成＋解説').run()
        a.selectbox(key='provider').set_value('OpenAI').run()
        a.text_area(key='problem').set_value('A+B').run()
        a.text_input(key='api_key').set_value('test-api-key').run()
        a.text_input(key='admin_code_input').set_value(code).run()
        a.checkbox[-1].check().run()
        return a

    def execute(self, a):
        next(b for b in a.button if b.label == '実行する').click().run(timeout=30)
        self.assertFalse(a.exception)

    def test_owner_and_no_repeat_on_rerun(self):
        with patch('counter.load_counter_config',return_value=CONFIG), patch('counter.record_success',return_value={'owner':1,'others':0,'total':1}) as record, patch('core.generate',return_value=('answer',USAGE,True)) as generate:
            a = self.app('9876')
            self.assertEqual(a.number_input(key='yen_rate').value,160)
            self.assertEqual(a.number_input(key='yen_rate').step,1)
            self.execute(a)
            self.assertTrue(record.call_args.args[2])
            self.assertIn('管理者本人の依頼：1回',a.session_state['report'])
            self.assertIn('約3.00円',a.session_state['report'])
            self.assertNotIn('9876',a.session_state['report'])
            self.assertTrue(a.session_state['pdf'].startswith(b'%PDF'))
            a.number_input(key='yen_rate').set_value(161).run()
            self.assertIn('160円',a.session_state['report'])  # report is an execution snapshot
            self.assertEqual(generate.call_count,1)
            self.assertEqual(record.call_count,1)

    def test_wrong_code_stops_before_api(self):
        with patch('counter.load_counter_config',return_value=CONFIG), patch('core.generate') as generate, patch('counter.record_success') as record:
            a=self.app('bad'); self.execute(a)
            generate.assert_not_called(); record.assert_not_called()
            self.assertTrue(a.error)

    def test_retry_uses_same_id_without_ai(self):
        with patch('counter.load_counter_config',return_value=CONFIG), patch('counter.record_success',side_effect=[TimeoutError('PRIVATE'),{'owner':0,'others':1,'total':1}]) as record, patch('core.generate',return_value=('answer',USAGE,True)) as generate:
            a=self.app(); self.execute(a)
            old_pdf=a.session_state['pdf']
            next(b for b in a.button if b.label=='累計の記録だけ再試行').click().run()
            self.assertEqual(record.call_args_list[0].args,record.call_args_list[1].args)
            self.assertFalse(record.call_args.args[2])
            self.assertEqual(generate.call_count,1)
            self.assertIn('その他の利用者の依頼：1回',a.session_state['report'])
            self.assertNotIn('PRIVATE',a.session_state['report'])
            self.assertNotEqual(old_pdf,a.session_state['pdf'])
            self.assertFalse(a.session_state['pending_counts'])

    def test_api_failure_and_incomplete_not_counted(self):
        with patch('counter.load_counter_config',return_value=CONFIG), patch('counter.record_success') as record:
            a=self.app()
            with patch('core.generate',side_effect=RuntimeError('PRIVATE')): self.execute(a)
            self.assertTrue(a.error)
            with patch('core.generate',return_value=('partial',USAGE,False)): self.execute(a)
            record.assert_not_called()
            self.assertIn('加算していません',a.session_state['report'])

    def test_no_backend_keeps_answer(self):
        with patch('counter.load_counter_config',return_value={'admin_code':'','url':'','key':''}), patch('counter.record_success') as record, patch('core.generate',return_value=('answer',USAGE,True)):
            a=self.app(); self.execute(a)
            self.assertIn('未設定',a.session_state['report'])
            self.assertIn('約3.00円',a.session_state['report'])
            record.assert_not_called()


if __name__ == '__main__': unittest.main()
