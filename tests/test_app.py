import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace as NS
import core
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'streamlit_app.py')

class CoreTests(unittest.TestCase):
    def test_url_rejection(self):
        for u in ['http://atcoder.jp/contests/a/tasks/a', 'https://evil.test/contests/a/tasks/a', 'https://atcoder.jp@127.0.0.1/contests/a/tasks/a', 'https://atcoder.jp:444/contests/a/tasks/a']:
            with self.assertRaises(ValueError): core.fetch_problem(u)
    def test_parse(self):
        title, text = core.parse_problem('<title>T</title><div id="task-statement"><span class="lang-ja"><p>整数<var>A</var></p><pre>1 2\n3 4</pre></span></div>')
        self.assertIn('1 2\n3 4', text)
        self.assertEqual(title, 'T')
    def test_no_key(self):
        with self.assertRaises(ValueError): core.generate('Gemini', 'model', '', 'p', '指定なし', 1000)
    def test_openai(self):
        with patch('openai.OpenAI') as factory:
            c=factory.return_value.__enter__.return_value
            c.responses.create.return_value=NS(output_text='OK',usage=None,status='completed')
            self.assertEqual(core.generate('OpenAI','model','test-key','prompt','指定なし',1024)[0],'OK')
            self.assertEqual(factory.call_args.kwargs['api_key'],'test-key')
            self.assertFalse(c.responses.create.call_args.kwargs['store'])
            self.assertNotIn('reasoning',c.responses.create.call_args.kwargs)
    def test_gemini(self):
        with patch('google.genai.Client') as factory:
            c=factory.return_value.__enter__.return_value
            c.interactions.create.return_value=NS(output_text='OK',usage=None,status='completed')
            self.assertEqual(core.generate('Gemini','model','test-key','prompt','medium',1024)[0],'OK')
            self.assertFalse(c.interactions.create.call_args.kwargs['store'])
            self.assertEqual(c.interactions.create.call_args.kwargs['generation_config']['max_output_tokens'],1024)
    def test_cost(self):
        u=NS(input_tokens=1000, output_tokens=2000,input_tokens_details=NS(cached_tokens=200))
        self.assertIn('0.0216200',core.usage_cost('OpenAI',u,(2,.1,10)))
        self.assertIn('算出できません',core.usage_cost('OpenAI',u,None))
    def test_safe_error(self):
        self.assertNotIn('SECRET',core.safe_error(Exception('SECRET')))

class UITests(unittest.TestCase):
    def test_solve_and_isolation(self):
        a=AppTest.from_file(APP).run()
        self.assertFalse(a.exception)
        a.radio[0].set_value('解答生成＋解説').run()
        a.text_area(key='problem').set_value('A+Bを出力').run()
        a.text_input(key='api_key').set_value('test-key').run()
        a.checkbox[-1].check().run()
        with patch('core.generate', return_value=('解答\nprint(3)',None,True)) as g:
            next(b for b in a.button if b.label=='実行する').click().run(timeout=30)
            self.assertEqual(g.call_count,1)
            self.assertIn('すべての変数',g.call_args.args[3])
            self.assertIn('report',a.session_state)
            self.assertTrue(a.session_state['pdf'].startswith(b'%PDF'))
            a.run()
            self.assertEqual(g.call_count,1)
        other=AppTest.from_file(APP).run()
        self.assertEqual(other.text_input(key='api_key').value,'')
        self.assertNotIn('report',other.session_state)
        next(b for b in a.button if b.label=='APIキーを消去').click().run()
        self.assertEqual(a.text_input(key='api_key').value,'')
        self.assertFalse(a.exception)
    def test_ac_review_and_pdf_failure(self):
        a=AppTest.from_file(APP).run()
        a.text_area(key='problem').set_value('A+Bを出力').run()
        next(w for w in a.text_area if w.label.startswith('コードを直接')).set_value('print(0)').run()
        next(w for w in a.selectbox if w.label=='AtCoderの判定').set_value('AC').run()
        a.text_input(key='api_key').set_value('test-key').run()
        a.checkbox[-1].check().run()
        with patch('core.generate', return_value=('回答',None,True)) as g, patch('pdf_output.pdf_bytes', side_effect=RuntimeError('secret')):
            next(b for b in a.button if b.label=='実行する').click().run()
            self.assertEqual(g.call_count,1)
            self.assertIn('判定はACですが',g.call_args.args[3])
            self.assertIn('print(0)',g.call_args.args[3])
            self.assertIn('report',a.session_state)
            self.assertTrue(a.warning)
            self.assertFalse(a.exception)
        next(b for b in a.button if b.label=='PDFを再作成').click().run()
        self.assertTrue(a.session_state['pdf'].startswith(b'%PDF'))

    def test_empty_key_no_api(self):
        a=AppTest.from_file(APP).run()
        a.checkbox[-1].check().run()
        with patch('core.generate') as g:
            next(b for b in a.button if b.label=='実行する').click().run()
            g.assert_not_called()
        self.assertTrue(a.error)

if __name__ == '__main__': unittest.main()
