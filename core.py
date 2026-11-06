from lxml import html

def parse_problem(page):
    tree = html.fromstring(page)
    nodes = tree.xpath('//*[@id="task-statement"]')
    if not nodes:
        raise ValueError("問題文を取得できません。公開済みの問題URLを確認してください。手動貼り付けも利用できます。")
    root = nodes[0]
    japanese = root.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," lang-ja ")]')
    if japanese:
        root = japanese[0]
    for node in root.xpath('.//script | .//style'):
        node.drop_tree()
    # Preserve TeX, input examples, block separation, and inline math spacing.
    for node in root.iter():
        if node.tag in ("h3", "p", "pre", "section", "li", "br", "div"):
            node.tail = "\n" + (node.tail or "")
        if node.tag == "var":
            node.tail = " " + (node.tail or "")
    text = root.text_content().strip()
    if not text:
        raise ValueError("取得した問題文が空です。")
    title = tree.xpath('//title/text()')
    return (title[0] if title else "AtCoder"), text

def usage_cost(provider, usage, prices, yen_rate=None):
    if usage is None:
        return "推定API料金は算出できません（使用量が返されませんでした）。"
    if provider == "Gemini":
        inputs = getattr(usage, "total_input_tokens", None)
        outputs = getattr(usage, "total_output_tokens", None)
        thoughts = getattr(usage, "total_thought_tokens", None)
        cached = getattr(usage, "total_cached_tokens", None)
        if thoughts is None and inputs is not None and outputs is not None:
            if getattr(usage, "total_tokens", None) == inputs + outputs:
                thoughts = 0
        if outputs is not None and thoughts is not None:
            outputs += thoughts
        else:
            outputs = None
    else:
        inputs = getattr(usage, "input_tokens", None)
        outputs = getattr(usage, "output_tokens", None)  # Includes reasoning tokens.
        cached = getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", None)
    if inputs is None or outputs is None:
        return "推定API料金は算出できません（使用量の内訳が不足）。"
    details = f"入力 {inputs:,} / 出力（思考込み）{outputs:,} トークン"
    if prices is None or inputs > 200000:
        return details + "\n推定API料金は算出できません（単価未設定、または長文料金の対象）。"
    count = cached or 0
    cost = ((inputs-count)*prices[0] + count*prices[1] + outputs*prices[2])/1_000_000
    note = "・キャッシュ不明のため割引なしで概算" if cached is None else ""
    yen = '' if yen_rate is None else f'（約{cost * yen_rate:,.2f}円）'
    rate = '' if yen_rate is None else f'\n換算レート：1ドル＝{yen_rate:,}円'
    return details + f"\n今回の推定API料金 US＄{cost:.7f}{yen}（税・決済手数料を含まない概算{note}）" + rate
import re
from urllib.parse import urlparse
import requests

MODELS = {
    'Gemini': ['gemini-4-argon', 'gemini-3.8-flash', 'gemini-3.1-pro-preview', 'その他（直接入力）'],
    'OpenAI': ['gpt-6.1-sol', 'gpt-6.1-terra', 'gpt-6-astra', 'gpt-6-luna', 'その他（直接入力）'],
}

def fetch_problem(url):
    p = urlparse(url.strip())
    if (p.scheme != 'https' or p.netloc != 'atcoder.jp' or
        not re.fullmatch(r'/contests/[\w-]+/tasks/[\w-]+/?', p.path)):
        raise ValueError('AtCoderの https://atcoder.jp/contests/.../tasks/... を指定してください。')
    # Never follow redirects to arbitrary hosts or internal network addresses.
    with requests.get('https://atcoder.jp' + p.path + '?lang=ja', timeout=(10, 30),
                      allow_redirects=False, stream=True) as response:
        if response.status_code != 200:
            raise ValueError('問題を取得できません。公開済みのURLを確認するか、問題文を貼り付けてください。')
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5_000_000:
                raise ValueError('ページが大きすぎます。')
    return parse_problem(data.decode('utf-8'))

def generate(provider, model, key, prompt, thinking, limit, *, with_status=False):
    if not key.strip():
        raise ValueError('APIキーを入力してください。')
    if not model.strip():
        raise ValueError('モデルIDを入力してください。')
    if provider == 'Gemini':
        from google import genai
        from google.genai import types
        with genai.Client(api_key=key, vertexai=False,
                          http_options=types.HttpOptions(timeout=600000,
                          retry_options=types.HttpRetryOptions(attempts=1))) as client:
            config = {'max_output_tokens': limit}
            if thinking != '指定なし':
                config['thinking_level'] = thinking
            result = client.interactions.create(model=model, input=prompt,
                        generation_config=config, store=False)
    else:
        from openai import OpenAI
        with OpenAI(api_key=key, base_url='https://api.openai.com/v1',
                    timeout=600, max_retries=0) as client:
            kwargs = {} if thinking == '指定なし' else {'reasoning': {'effort': thinking}}
            result = client.responses.create(model=model, input=prompt, store=False,
                         max_output_tokens=limit, **kwargs)
    text = getattr(result, 'output_text', '') or ''
    status = str(getattr(result, 'status', ''))
    countable = bool(text.strip()) and status == 'completed'
    if status in ('incomplete', 'failed', 'cancelled'):
        text += '\n\n【注意】回答が完了していません。出力上限やAPIの状態を確認してください。'
    if not text.strip():
        text = '本文が返りませんでした。出力上限、モデルの対応、APIの利用状況を確認してください。'
    response = (text, getattr(result, 'usage', None))
    return (*response, countable) if with_status else response

def safe_error(error):
    # Never show SDK exception bodies: they may contain user data or credentials.
    status = getattr(error, 'status_code', getattr(error, 'code', None))
    if status in (401, 403):
        return '認証または権限エラーです。キーとモデルの利用権限を確認してください。'
    if status == 429:
        return '利用上限に達しました。API側の残高・利用枠を確認してください。'
    if status == 400:
        return 'リクエストが拒否されました。モデルID、思考設定、問題文を確認してください。安全フィルターが原因の場合もあります。'
    if status == 404:
        return 'モデルが見つかりません。利用可能なモデルIDを指定してください。'
    return '通信またはAPI処理に失敗しました。自動再送はしていません。再実行の前にAPI側の使用量を確認してください。'
