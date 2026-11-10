# APIキー不要の公開版

既存のアプリと同じGitHubリポジトリから、**別のStreamlitアプリ**として公開します。
既存の `streamlit_app.py` は変更しません。新アプリの入口は `sponsored_app.py` です。

## 設定する順番

1. 既存のSupabaseプロジェクト `atcoder-ai-counter` のSQL Editorで `sponsored_setup.sql` を実行します。既存カウンターの初期化は不要です。追加SQLは既存の累計を消しません。
2. https://share.streamlit.io/ で **Create app**。Repositoryは `yasutake88/atcoder-ai-web`、Branchは `main`、Main file pathは **`sponsored_app.py`** を指定します。既存アプリの設定画面ではなく、新しいアプリの作成画面を使います。
3. 新しいアプリのSecretsに、既存アプリと同じ3項目（ADMIN_CODE、SUPABASE_URL、SUPABASE_SECRET_KEY）をコピーし、以下の2項目を追加します。

```toml
SPONSORED_GEMINI_API_KEY = "公開版専用のGemini APIキーに置き換える"
SPONSORED_ENABLED = true
```

本物のキーはGitHubやチャットに貼らず、StreamlitのSecretsに直接登録してください。
この公開版で使うGoogleプロジェクトは、他のAPI利用と分けてください。他のアプリで使った費用はこの予算管理には含まれません。

4. Python 3.12を選んでDeployし、アプリの公開範囲をEveryoneにします。新しいURLが発行されます。
5. 短い過去問で1回実行し、回答・PDF・共通カウンターを確認します。この実動作確認には通常のAPI料金が発生します。

## 固定仕様

- Gemini `gemini-3.8-flash`、思考 `high`。利用者によるモデル・思考設定の変更なし。
- 問題取得、コードのアップロード／貼り付け、レビュー、解答解説、PDF。
- ログインなし。個人別の制限はなく、全体の受付間隔10秒と月予算で制限します。一人で枠を使い切る可能性はあります。
- 既存の `record_atcoder_request` を使用。管理者本人／その他／合計の累計を共用します。管理者コードは分類のみで、予算制限は解除しません。
- カウンターは正常完了だけを加算。PDFダウンロードは加算しません。表示は記録時点の値で、自動リアルタイム更新ではありません。

## 月1,000円の目標と予算管理

- 内部上限は月6.25米ドル（1ドル160円換算で1,000円相当）。日本時間の各月で管理し、翌月は新しい枠を使用します。
- API送信前に1件0.32米ドルをDB上で確保します。同時受付も同じロックで処理するため二重に予算を使えません。
- 入力上限20,000トークン、出力上限32,768トークン（思考込み）。highでもこの上限は適用され、長い回答は途中終了する場合があります。
- 予算計算は割引を使わず入力1.50／出力7.50米ドル・100万トークンで保守的に算定。キャッシュ割引も使いません。
- 使用量が確認できたら予約との差額を戻します。不明・エラー・タイムアウトは予約額を保持し、自動再試行しません。0.32米ドルを毎回保持すると最大19回、使用量精算で余裕が出れば回数は増えます。実請求額・実行回数は保証しません。
- 月をまたいで完了した依頼は受付月に精算します。事業者の請求締め・為替・税・手数料・料金改定・別経路の利用によって、実際の円請求額とは差が出ます。月1,000円の絶対的な請求上限を保証する仕組みではありません。
- 料金確認期限は2027年1月31日。以降は料金とモデルを再確認してPython・SQLの両方を更新するまで停止します。
- 予算保存先に接続できない場合はAIを呼びません。正常完了後のDB保存に失敗したら「記録だけ再試行」で復旧できます。同じ依頼IDでの再試行は二重加算されません。ブラウザを閉じると未保存の完了通知が失われることがありますが、予約額はDBに残ります。
- 緊急停止は新アプリのSecretsで `SPONSORED_ENABLED = false`。DB側でも `update public.sponsored_settings set enabled=false where singleton;` で停止できます。既に送信済みの処理は取り消しません。

## 検証

`python -m unittest test_sponsored -v`

単体テスト10件と、Streamlitの未設定画面が安全に停止することを確認。
SQLはローカルのPostgreSQL互換環境で、予約・精算・重複防止・予算不足・権限制御を検証。
実際のSupabase接続と有料APIの実行、Streamlit Cloudへの新規公開は、Secrets設定後に確認が必要です。

参考：
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/thinking
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

## 既存公開版の月額枠を1,000円へ変更（2026-11-10）

既存のSupabaseプロジェクトのSQL Editorで `sponsored_budget_1000.sql` を1回実行してください。
今月の使用額・確保額・累計は保持し、月額枠だけを6.25米ドルに変更します。
実行後、公開版の「残額を更新」を押してください。翌月以降も新しい月額枠が適用されます。

## 出力上限32,768への更新

既存プロジェクトのSQL Editorで `sponsored_output_32768.sql` を実行します。新規依頼は0.32米ドル（51.20円）を確保します。既存の使用額・確保額・月額枠は変更しません。未適用の間、新版はAI生成を開始しません。使用量が確認できれば差額を精算します。
