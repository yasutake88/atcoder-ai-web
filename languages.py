"""AtCoder official language/runtime snapshot, shared by both applications."""
import io
import json
from pathlib import Path

CATALOG = json.loads(Path(__file__).with_name('languages.json').read_text(encoding='utf-8'))
LANGUAGES = {item['name']: item['filename'] for item in CATALOG['languages']}
DEFAULT_LANGUAGE = 'Python (PyPy 3.11-v7.3.20)'


def language_selector():
    import streamlit as st
    names = list(LANGUAGES)
    selected = st.selectbox('提出・解答の言語（処理系・バージョン）', names,
                            index=names.index(DEFAULT_LANGUAGE), key='source_language')
    st.caption(f"AtCoder公式一覧の全{len(names)}項目（処理系の違いを含む）。"
               f"確認日：{CATALOG['checked']}。コンテストごとの利用可否は提出画面で確認してください。")
    st.caption('ソースはUTF-8で保存してください。PietはPPM画像も読み込めます。'
               'AIによる解析・生成であり、コンパイルや実行、ACの保証は行いません。')
    st.markdown(f"[AtCoder公式の言語・ライブラリ一覧]({CATALOG['source']})")
    return selected, LANGUAGES[selected]


def read_source(data, language):
    # Preserve significant whitespace and never execute uploaded code.
    if language.startswith('Piet ') and data.startswith((b'P6', b'P3')):
        from PIL import Image
        with Image.open(io.BytesIO(data)) as picture:
            if picture.format != 'PPM' or picture.width * picture.height > 16384:
                raise ValueError('Unsupported Piet image')
            rgb = picture.convert('RGB')
            pixels = list(rgb.getdata())
            rows = [' '.join(str(c) for pixel in pixels[start:start + rgb.width] for c in pixel)
                    for start in range(0, len(pixels), rgb.width)]
            return f'P3\n{rgb.width} {rgb.height}\n255\n' + '\n'.join(rows) + '\n'
    return data.decode('utf-8-sig')
