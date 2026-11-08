import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from unittest.mock import patch
from languages import LANGUAGES, read_source
from prompts import build_prompt
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class LanguageTests(unittest.TestCase):
    def setUp(self):
        patcher = patch('budget_display.rpc', return_value=dict(month='2026-11', monthly_micro_usd=5000000, used_micro_usd=0, enabled=True))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_every_runtime_in_both_prompt_modes(self):
        self.assertEqual(len(LANGUAGES), 117)
        for language, filename in LANGUAGES.items():
            for mode in ('レビュー', '解答生成＋解説'):
                prompt = build_prompt(mode, 'A+B {example}', 'code {x}', 'AC',
                                      language=language, filename=filename)
                self.assertIn(language, prompt)
                self.assertIn(filename, prompt)
                self.assertIn('A+B {example}', prompt)
                if not language.startswith('Python'):
                    self.assertNotIn('Python', prompt)
                if mode == 'レビュー':
                    self.assertIn('判定はACですが', prompt)
                else:
                    self.assertIn('すべての変数', prompt)

    def test_whitespace_and_piet(self):
        self.assertEqual(read_source(b' \t\n\t ', 'Whitespace'), ' \t\n\t ')
        self.assertEqual(read_source(b'P6\n1 1\n255\n\xff\x00\x00', 'Piet image'),
                         'P3\n1 1\n255\n255 0 0\n')
        with self.assertRaises(ValueError):
            read_source(b'P6\n20000 1\n255\n', 'Piet image')

    def test_both_apps_send_selected_language_and_export_it(self):
        for app in ('streamlit_app.py', 'sponsored_app.py'):
            for mode in ('レビュー', '解答生成＋解説'):
                with self.subTest(app=app, mode=mode):
                    a = AppTest.from_file(str(ROOT / app))
                    a.secrets.update(ADMIN_CODE='test-admin', SUPABASE_URL='https://test.supabase.co',
                                     SUPABASE_SECRET_KEY='sb_secret_test',
                                     SPONSORED_GEMINI_API_KEY='test-key', SPONSORED_ENABLED=True)
                    a.run()
                    self.assertEqual(a.selectbox(key='source_language').value, 'Python (PyPy 3.11-v7.3.20)')
                    a.radio[0].set_value(mode)
                    a.selectbox(key='source_language').set_value('C++23 (GCC 15.2.0)')
                    a.run()
                    a.text_area(key='problem').set_value('A+Bを出力')
                    if mode == 'レビュー':
                        next(t for t in a.text_area if t.key != 'problem').set_value('int main() {}')
                    if app == 'streamlit_app.py':
                        a.text_input(key='api_key').set_value('test-key')
                    a.checkbox[-1].check().run()
                    counts = {'owner': 0, 'others': 1, 'total': 1}
                    with patch('core.generate', return_value=('回答', None, True)) as generate, \
                         patch('counter.record_success', return_value=counts), \
                         patch('public_budget.count_prompt_tokens', return_value=100), \
                         patch('public_budget.run_sponsored', return_value=('回答', None, {'p_completed': True})) as sponsored, \
                         patch('public_budget.rpc', return_value={'counts': counts}):
                        next(b for b in a.button if b.label == '実行する').click().run(timeout=30)
                        self.assertFalse(a.exception)
                        prompt = generate.call_args.args[3] if app == 'streamlit_app.py' else sponsored.call_args.args[2]
                        self.assertIn('C++23 (GCC 15.2.0)', prompt)
                        self.assertNotIn('Python', prompt)
                        report = a.session_state['report' if app == 'streamlit_app.py' else 'report_base']
                        self.assertIn('使用言語: C++23 (GCC 15.2.0)', report)

    def test_sponsored_heading(self):
        a = AppTest.from_file(str(ROOT / 'sponsored_app.py')).run()
        self.assertFalse(a.exception)
        texts = [m.value for m in a.markdown]
        disclaimer = ':red[※ 個人が開発・運営する非公式ツールです。AtCoder株式会社とは一切関係ありません。]'
        self.assertLess(texts.index(disclaimer), texts.index('APIキー不要の公開版'))
        self.assertFalse(any(s.value == 'APIキー不要の公開版' for s in a.subheader))


if __name__ == '__main__':
    unittest.main()
