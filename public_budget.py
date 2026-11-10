"""Sponsored-only configuration; nothing here changes the BYOK application."""
from datetime import date
from decimal import Decimal, ROUND_CEILING
from uuid import uuid4
from counter import configured

MODEL = 'gemini-3.8-flash'
OUTPUT_LIMIT = 32768
INPUT_LIMIT = 20000
# Conservative, undiscounted USD/1M rates. Effective introductory fees may be lower.
PRICES = (1.5, 0.15, 7.5)
RESERVATION_MICRO_USD = 320000
YEN_RATE = 160
PRICE_REVIEW_DEADLINE = date(2027, 1, 31)

def actual_micro_usd(usage):
    if usage is None:
        return None
    values = [getattr(usage, name, None) for name in
              ('total_input_tokens', 'total_output_tokens', 'total_thought_tokens')]
    if any(type(v) is not int or v < 0 for v in values):
        return None
    inputs, outputs, thoughts = values
    # No cache discount: keep the budget conservative.
    return int((Decimal(inputs) * Decimal('1.5') +
                Decimal(outputs + thoughts) * Decimal('7.5')).to_integral_value(rounding=ROUND_CEILING))

def rpc(config, name, payload):
    import requests
    if not configured(config):
        raise ValueError('公開版の保存先が未設定です。')
    with requests.post(config['url'] + '/rest/v1/rpc/' + name,
                       headers={'apikey': config['key'], 'Content-Type': 'application/json'},
                       json=payload, timeout=(5, 15), allow_redirects=False) as response:
        if response.status_code != 200:
            raise ValueError('予算の確認・保存ができません。')
        data = response.json()
    if not isinstance(data, dict):
        raise ValueError('予算の応答が不正です。')
    return data

def run_sponsored(config, key, prompt, owner, count_tokens, generate, *, today=None, rpc_call=rpc):
    """No retry on either reservation or generation. Uncertain calls retain funds."""
    today = today or date.today()
    if today > PRICE_REVIEW_DEADLINE:
        raise ValueError('料金設定の確認期限を過ぎたため、受付を停止しています。')
    if not configured(config) or not key:
        raise ValueError('公開版の接続設定が未完了です。')
    if not prompt.strip() or len(prompt.encode('utf-8')) > 200000:
        raise ValueError('入力が空、または長すぎます。')
    tokens = count_tokens(key, prompt)
    if type(tokens) is not int or not 0 < tokens <= INPUT_LIMIT:
        raise ValueError('問題文とコードは合計20,000入力トークン以内にしてください。')
    request_id = str(uuid4())
    reservation = rpc_call(config, 'reserve_sponsored_request_v2',
                           {'p_request_id': request_id, 'p_is_owner': bool(owner)})
    if reservation.get('allowed') is not True:
        reason = reservation.get('reason')
        messages = {'budget': '今月の公開版の利用枠が終了しました。翌月に再開します。',
                    'busy': 'ただいま依頼が集中しています。少し時間をおいてください。',
                    'disabled': '公開版は現在受付を停止しています。'}
        raise ValueError(messages.get(reason, '依頼を受け付けられませんでした。'))
    if reservation.get('reserved_micro_usd') != RESERVATION_MICRO_USD:
        raise ValueError('予算確保額を確認できません。AIには送信していません。')
    answer, usage, completed = generate('Gemini', MODEL, key, prompt, 'high', OUTPUT_LIMIT, with_status=True)
    # A generation exception leaves the reservation intact, including timeouts.
    return answer.replace(key, '[非表示]'), usage, {
        'p_request_id': request_id,
        'p_actual_micro_usd': actual_micro_usd(usage),
        'p_completed': bool(completed),
    }

def count_prompt_tokens(key, prompt):
    from google import genai
    from google.genai import types
    with genai.Client(api_key=key, vertexai=False,
                      http_options=types.HttpOptions(timeout=30000,
                      retry_options=types.HttpRetryOptions(attempts=1))) as client:
        return client.models.count_tokens(model=MODEL, contents=prompt).total_tokens
