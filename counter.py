"""Server-side cumulative counters. Never send prompts, API keys or the PIN here."""
import hmac
import re
from uuid import UUID

import requests


def load_counter_config(secrets):
    try:
        return {
            'admin_code': str(secrets.get('ADMIN_CODE', '')),
            'url': str(secrets.get('SUPABASE_URL', '')).rstrip('/'),
            'key': str(secrets.get('SUPABASE_SECRET_KEY', '')),
        }
    except (FileNotFoundError, KeyError):
        return {'admin_code': '', 'url': '', 'key': ''}


def configured(config):
    return (bool(config['admin_code'])
            and bool(re.fullmatch(r'https://[a-z0-9-]+\.supabase\.co', config['url']))
            and config['key'].startswith('sb_secret_'))


def classify(code, config):
    if not code:
        return False
    if not config['admin_code']:
        raise ValueError('管理者確認コードがサーバーに未設定です。')
    if not hmac.compare_digest(code.encode(), config['admin_code'].encode()):
        raise ValueError('管理者確認コードが一致しません。確認するか、空欄にして一般利用してください。')
    return True


def record_success(config, request_id, is_owner):
    """An idempotent, atomic RPC: retry the SAME id after an ambiguous timeout."""
    if not configured(config):
        raise ValueError('累計の保存先が未設定です。')
    request_id = str(UUID(request_id))
    with requests.post(
        config['url'] + '/rest/v1/rpc/record_atcoder_request',
        headers={'apikey': config['key'], 'Content-Type': 'application/json'},
        json={'p_request_id': request_id, 'p_is_owner': bool(is_owner)},
        timeout=(5, 10), allow_redirects=False,
    ) as response:
        if response.status_code != 200:
            raise ValueError('累計の保存先に接続できません。')
        data = response.json()
    if not isinstance(data, dict):
        raise ValueError('累計の応答が不正です。')
    if any(type(data.get(k)) is not int or data[k] < 0 for k in ('owner', 'others', 'total')):
        raise ValueError('累計の応答が不正です。')
    if data['owner'] + data['others'] != data['total']:
        raise ValueError('累計の応答が不正です。')
    return data


def counts_text(counts):
    return (f"累計依頼回数（記録時点）\n管理者本人の依頼：{counts['owner']:,}回"
            f"\nその他の利用者の依頼：{counts['others']:,}回"
            f"\n合計：{counts['total']:,}回")
