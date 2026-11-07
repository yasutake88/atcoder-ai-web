import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from core import diagnostic_text, safe_error
from streamlit.testing.v1 import AppTest

class DiagnosticTests(unittest.TestCase):
    def test_nested_timeout_no_secret(self):
        error = RuntimeError('SECRET body')
        error.__cause__ = TimeoutError('SECRET URL')
        text = diagnostic_text(error, 'api', 123.4)
        self.assertIn('時間切れ', safe_error(error))
        self.assertIn('TimeoutError', text)
        self.assertIn('123.4秒', text)
        self.assertNotIn('SECRET', text)

    def test_response_status_and_string_status(self):
        error = RuntimeError('SECRET')
        error.response = NS(status_code=503)
        self.assertIn('サーバー', safe_error(error))
        self.assertIn('503', diagnostic_text(error, 'api', 1))
        error.status_code = '429'
        self.assertIn('利用上限', safe_error(error))

    def test_unknown_type_and_cyclic_chain(self):
        error = type('SECRET', (Exception,), {})('SECRET')
        error.__cause__ = error
        error.code = 'SECRET'
        text = diagnostic_text(error, 'SECRET', 0)
        self.assertNotIn('SECRET', text)
        self.assertIn('OtherError', text)

    def test_api_and_postprocessing_errors(self):
        app = str(Path(__file__).resolve().parents[1] / 'streamlit_app.py')
        for cost_failure in (False, True):
            a = AppTest.from_file(app).run()
            a.radio[0].set_value('解答生成＋解説').run()
            a.text_area(key='problem').set_value('A+B').run()
            a.text_input(key='api_key').set_value('SECRET-key').run()
            a.checkbox[-1].check().run()
            with patch('core.generate', return_value=('OK', None, True),
                       side_effect=None if cost_failure else TimeoutError('SECRET')) as g, \
                 patch('core.usage_cost', side_effect=TypeError('SECRET')):
                next(b for b in a.button if b.label == '実行する').click().run()
                self.assertEqual(g.call_count, 1)
            self.assertFalse(a.exception)
            diagnostic = a.code[0].value
            self.assertIn('料金計算' if cost_failure else '応答の受信', diagnostic)
            self.assertNotIn('SECRET', diagnostic)
            a.run()
            self.assertFalse(a.exception)

if __name__ == '__main__':
    unittest.main()
