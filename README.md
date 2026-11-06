# AtCoder AI Web

Gemini / OpenAIを選んで、AtCoderのレビューまたは解答＋解説を生成し、PDFを保存するStreamlitアプリです。
**公開・各自APIキー方式**です。運営者のキーは設定しないでください。

## 最初の公開手順（パソコンでの操作推奨）

1. ZIPを展開し、`AtCoderAI_Web` フォルダを開きます。
2. https://github.com/ でログインし、右上の「+」→「New repository」。名前を `atcoder-ai-web` とし、公開するなら Public を選んで作成します。
3. 「uploading an existing file」または「Add file」→「Upload files」を開きます。
4. このフォルダの**中身**をアップロードして「Commit changes」を押します。ZIPそのものではありません。リポジトリ直下に `streamlit_app.py` と `requirements.txt` がある状態にします。
5. `.streamlit/config.toml` もアップロードします。隠しフォルダが選べない場合はGitHubの「Add file」→「Create new file」で、ファイル名 `.streamlit/config.toml` を指定し、同梱ファイルの内容を貼り付けます。
6. https://share.streamlit.io/ で登録し、GitHubへの連携を許可します。
7. 「Create app」からリポジトリ `atcoder-ai-web`、ブランチ `main`、実行ファイル `streamlit_app.py` を指定します。
8. Advanced settingsでPython 3.12を選択します。AI利用だけならSecretsは空欄です。累計機能を使う場合は下記の「累計回数の初期設定」を行ってください。運営者のGemini／OpenAI APIキーは登録しません。
9. 「Deploy」を押します。起動後に表示される `https://....streamlit.app` がアプリURLです。
10. 公開設定を確認し、まずご自身のキーで短い問題を試します。その後URLを他の人に案内できます。

GitHubやStreamlitの画面名称は変わることがあります。アカウント連携と初回Deployは利用者のログインが必要です。このZIPだけではまだ公開されません。

## iPhoneでの利用

1. Googleドライブ／OneDriveアプリを入れてログインします。
2. iPhoneの「ファイル」→「ブラウズ」→「…」→「編集」で該当サービスを有効にします。
3. SafariでアプリURLを開き、問題URLを入力して「問題文を取得」。取得文に制約・入力例が含まれるか確認します。
4. レビューならコード選択ボタンから「ファイルを選択」で `.py` を選びます。表示されなければiPhone内へコピーするか直接貼り付けます。
5. 解答生成ならコード選択は不要です。アルゴリズム・全変数の説明を依頼します。
6. AI・モデル・自分のAPIキーを入力して同意をチェックし「実行する」。
7. 「PDFをダウンロード」後、共有メニュー→「ファイルに保存」でGoogleドライブ等の保存先を選びます。元コードのフォルダへ自動保存する機能はありません。
8. 終わったら「入力・回答・キーをすべて消去」。

## キーとデータ

- APIキー必須。環境変数、Streamlit Secrets、運営者キーへのフォールバックはありません。
- キー・提出コード・回答は利用者ごとのStreamlit接続で保持し、アプリからディスクや共通キャッシュへ保存しません。
- キーはブラウザ→アプリサーバー→選択AI事業者を経由します。運営者やホスティング事業者に対して暗号学的に秘匿する仕組みではありません。信頼する運営元でのみ使用してください。
- APIキーはプロンプトに含めません。生のAPI例外やリクエスト内容を表示・ログ出力しません。
- store=Falseを指定しますが、AI事業者側の不正利用監視などを含む完全な非保持を保証するものではありません。
- APIキー消去ボタンはアプリ内のキー入力を消去します。すでに送信されたリクエストの取り消し・キー失効ではありません。
- ダウンロードは追加のAI呼び出しなし。再読み込みや休止で回答が失われる場合があります。
- 公開ソースにキーを書かないでください。公開アプリは運営者がソースを変更できるため、利用者には運営者への信頼が必要です。

## モデル・料金・制約

- モデル候補は既存Windows版を引き継いでいます。利用可否・思考設定はAPIアカウントごとに異なります。「その他」で任意のモデルIDを指定できます。
- 思考は初期値「指定なし」。非対応エラーが出るときも「指定なし」に戻してください。
- チェックなしではアプリ作成時点のモデル別登録単価を使用します。「個別に単価を設定する」で上書きできます。通常入力・出力の増減幅は0.1ドル、キャッシュ入力は0.01ドルです。単価は自動更新しません。未設定・使用量不足・20万入力トークン超は算出不可と表示します。
- 推定額は通常のテキスト生成トークン料金のみ。税・決済手数料等は含みません。円換算は初期値1ドル160円、1円刻みで変更できます。実行時のレートを画面・テキスト・PDFに記載します。正式な請求額は各社の管理画面で確認してください。
- Geminiでは思考トークンを出力に加算し、OpenAIでは出力内に含まれる思考トークンを二重加算しません。
- APIは最大10分のタイムアウト、自動再試行なし。タイムアウトでも事業者側で処理や課金が完了している場合があります。
- AtCoder公開問題URLのみ取得。リダイレクトは追いません。図は取得しないため必要条件を手入力してください。
- 提出コードを実行しません。モデルの反例・正しさは未検証です。ACを保証しません。
- PDFは日本語対応のプレーンテキスト形式。Markdown表・数式は記法のままです。長い行は折り返します。画面も外部画像等を読み込まないプレーンテキストです。
- Community Cloudの資源上限・休止があります。大量同時アクセスを前提としたサービスではありません。

## ローカルで試す（Windows PowerShell）

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Python 3.12がない場合は3.13でも試せます。コマンドの `py -3.12` を `py` に変更してください。

## テスト

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

テストは外部APIを模擬し、課金なしで実行します。実際のAPIキーでの応答・Streamlit Cloud上の実動作・iPhone Safariでの操作は、公開後に確認してください。

## 主なファイル

- streamlit_app.py: Web画面
- core.py: 問題取得・API呼び出し・料金計算
- prompts.py: レビュー／解答生成指示
- pdf_output.py: 日本語PDF作成
- .streamlit/config.toml: アップロード制限・エラー表示設定

## 公式資料

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- https://ai.google.dev/gemini-api/docs/text-generation
- https://developers.openai.com/api/reference/resources/responses/methods/create

公開ソースはMITライセンスです。同梱LICENSEを参照してください。依存ライブラリは各ライセンスに従います。


## 累計回数の初期設定（管理者が一度だけ行う）

累計を再起動後も保持するため、Supabaseの専用プロジェクトに保存します。
AI機能・円換算は保存先が未設定でも使えます。未設定を0回とは表示しません。

1. https://supabase.com/dashboard でアカウントにログインし、専用プロジェクトを作成します。
2. プロジェクトのSQL Editorで、このリポジトリの `counter_setup.sql` を貼り付けて実行します。
3. プロジェクトの接続情報からProject URLとSecret API key（`sb_secret_`で始まるサーバー専用キー）を確認します。publishable／anonキーは使えません。
4. Streamlit Community Cloudの対象アプリのSettings → Secretsに次を設定します。
   プレースホルダーを自分の値に置き換えてください。管理者確認コードも文字列（引用符付き）です。

```toml
ADMIN_CODE = "自分で決めた管理者確認コード"
SUPABASE_URL = "https://プロジェクトID.supabase.co"
SUPABASE_SECRET_KEY = "sb_secret_ここを置き換える"
```

5. 保存後にアプリを再読み込みします。自分の実行では「管理者本人として利用する場合」を開き、管理者確認コードを入力します。一般利用者は空欄にします。

Secretsの内容はGitHubにアップロードしないでください。コード・SQL・README・テストに本物の確認コードやキーは含めていません。確認コードは依頼の分類だけに使い、管理権限や運営者のAIキーを提供しません。コードを知る人は本人扱いになる簡易識別方式であり、厳密な本人認証ではありません。

### 数え方と障害時の扱い

- 設定後、APIが `completed` と非空の回答を返した依頼を1回と数えます。レビュー・解答生成の両方を含みます。
- エラー・タイムアウト・途中終了・空回答は数えません。請求件数とは異なります。
- ページ表示・設定変更・PDFの作成／再ダウンロードは加算しません。
- 保存はランダムな依頼UUIDと本人区分のみです。問題文・コード・回答・APIキー・確認コードはデータベースに保存しません。
- データベースのトランザクションとUUIDによる重複排除を使い、同時実行の取りこぼしと再試行による二重加算を防ぎます。
- 累計は記録時点のスナップショットを費用表示の後に記載します。PDFも同じ値です。他の利用者の実行後に古いPDFの値は変わりません。
- 保存失敗時も回答は保持し、「累計の記録だけ再試行」で同じUUIDを再送できます。AIへの再送信・追加API料金はありません。
- 保存失敗後にブラウザを閉じたりサーバーが停止すると、未保存分の再試行情報は失われる場合があります。外部DBの停止中や設定前の件数・過去の件数を推測で補いません。
- 累計はプロジェクトを維持する限りStreamlitの再起動に依存しません。Supabaseの休止・削除・利用制限は別途管理してください。

参考：
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://supabase.com/docs/guides/getting-started/api-keys
- https://supabase.com/docs/guides/database/functions
