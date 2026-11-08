import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from unittest.mock import patch, Mock
from budget_display import balance_text, show_balance
from streamlit.testing.v1 import AppTest


class BalanceTests(unittest.TestCase):
    def data(self, used=0, enabled=True):
        return dict(month='2026-11', monthly_micro_usd=5000000,
                    used_micro_usd=used, enabled=enabled)

    def test_unused_reserved_and_settled(self):
        for used, expected in [(0, '800.00円'), (160000, '774.40円'), (10000, '798.40円')]:
            self.assertIn(expected, balance_text(self.data(used)))

    def test_exhausted_and_disabled(self):
        self.assertIn('0.00円', balance_text(self.data(6000000)))
        self.assertIn('新規受付は終了', balance_text(self.data(4900000)))
        self.assertIn('受付を停止', balance_text(self.data(enabled=False)))

    def test_unknown_not_zero(self):
        slot = Mock()
        with patch('budget_display.rpc', side_effect=ValueError('private data')):
            show_balance(slot, {})
        text = slot.info.call_args.args[0]
        self.assertIn('取得できません', text)
        self.assertNotIn('private data', text)
        self.assertNotIn('0.00', text)
        for data in (None, {}, self.data(-1), self.data(True)):
            with self.assertRaises(ValueError):
                balance_text(data)

    def test_position_and_refresh_without_ai(self):
        app = Path(__file__).resolve().parents[1] / 'sponsored_app.py'
        with patch('budget_display.rpc', return_value=self.data()) as rpc, patch('core.generate') as ai:
            a = AppTest.from_file(str(app)).run()
            self.assertFalse(a.exception)
            self.assertIn('gemini', a.info[0].value)
            self.assertIn('800.00円', a.info[1].value)
            rpc.return_value = self.data(160000)
            next(b for b in a.button if b.label == '残額を更新').click().run()
            self.assertIn('774.40円', a.info[1].value)
            ai.assert_not_called()


if __name__ == '__main__':
    unittest.main()
