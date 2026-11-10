"""Read-only public budget display; no AI calls or accounting writes."""
import re
from decimal import Decimal
from public_budget import YEN_RATE, RESERVATION_MICRO_USD, rpc


def balance_text(data):
    if not isinstance(data, dict):
        raise ValueError('Invalid balance')
    month = data.get('month')
    limit, used = data.get('monthly_micro_usd'), data.get('used_micro_usd')
    if (not isinstance(month, str) or not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', month)
            or any(type(v) is not int or v < 0 for v in (limit, used))
            or type(data.get('enabled')) is not bool):
        raise ValueError('Invalid balance')
    remaining = max(0, limit - used)
    yen = Decimal(remaining) * YEN_RATE / 1000000
    total_yen = Decimal(limit) * YEN_RATE / 1000000
    message = f'今月の利用枠の残額：{yen:,.2f}円 ／ {total_yen:,.2f}円（{month}・日本時間）'
    if not data['enabled']:
        message += '\n現在、受付を停止しています。'
    elif remaining < RESERVATION_MICRO_USD:
        message += '\n次の1回に必要な確保額（51.20円）に満たないため、今月の新規受付は終了しています。'
    return message


def show_balance(slot, config):
    try:
        text = balance_text(rpc(config, 'get_sponsored_balance', {}))
    except Exception:
        slot.info('今月の利用枠の残額：取得できません（残額表示の設定または通信を確認してください）。')
    else:
        slot.info(text)
