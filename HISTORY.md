# HISTORY.md (springlearn2)

学習の履歴ログ。演習アプリの進捗、つまずいたポイント・Q&A、次にやりたいことを都度追記していく。
方針は`CLAUDE.md`を参照。

## 演習アプリ別ログ

### todolist7x(ToDoアプリ、参考書のサンプル)

- 2026-11-16: 参考書のサンプル(`sampleSource/`)を`todolist7x/`にコピーしてプロジェクト作成。ビルド・起動(`GET /todo`)・DB接続(`tododb`)を確認済み
- 構成: `controller/TodoListController` → `service/TodoService` → `repository/TodoRepository`(JpaRepository) / `dao/TodoDaoImpl`(EntityManager で条件検索+ページング)。`form/TodoData`(入力フォーム)、`form/TodoQuery`(検索条件)、`entity/Todo`、`common/Utils`
- 前シーズンの todolist_ver1 との違い(ざっと見た範囲): Spring Boot 4.0.1 / Java 21、`@RequiredArgsConstructor`でのコンストラクタインジェクション、`hibernate-processor`(JPAメタモデル生成)の追加
- 2026-11-24: 参考書の7章版として `参考ソース/back/todolist7x/` に移動(読み取り専用。ソースノートの「元」)

### todolist8b(参考書8章のサンプル。テーマ: 多言語対応 i18n)

- 2026-11-24: 参考書の8章サンプル(`参考ソース/Todolist8b/`、Eclipse形式)から src・sql・Gradle設定を `todolist8b/` にコピーして、VSCodeで動く形にした。`gradlew build`(テスト含む)と起動を確認済み。ブラウザの言語が日本語なら日本語、英語なら英語で画面が出ることも確認した
- ソースノートに反映(元 = todolist7x / 改修後 = todolist8b を切り替えて表示、差分に色付け)

#### 7章 → 8章の変更ファイル(2026-11-24反映。空白・インデントだけの違いは除く)

| ファイル | 区分 | 変更の狙い(コードから読み取れる範囲) |
|---|---|---|
| `application.properties(.example)` | 変更 | `spring.messages.basename` でメッセージファイル(`i18n/FixedDisplayStrings`、`i18n/ValidationMessages`)を読み込む。`fallback-to-system-locale=false` で、該当言語が無いときはOSの言語ではなく既定ファイルを使う |
| `i18n/FixedDisplayStrings(_en/_ja).properties` | 追加 | 画面の固定文言(見出し・ボタン・選択肢・ページ送り)を言語別のファイルに外出し。`_ja` は `件名` のようなUnicodeエスケープで書かれている。既定ファイルは `Title(default)` となっていて、どのファイルが使われたか見分けられる |
| `i18n/ValidationMessages(_en/_ja).properties` | 追加 | 入力チェックのエラーメッセージを言語別に。キーは `NotBlank.todoData.title`(アノテーション名.オブジェクト名.フィールド名)形式と、独自チェック用(`DoubleSpace...`、`InvalidFormat...`、`Past...`) |
| `form/TodoData.java` | 変更 | `@NotBlank(message = "…")` などから `message` を削除。メッセージはファイルから自動で引かれる |
| `service/TodoService.java` | 変更 | `MessageSource` を注入し、独自チェックのエラー文を `messageSource.getMessage(キー, null, locale)` で取得。2つの `isValid` に `Locale` 引数を追加 |
| `controller/TodoListController.java` | 変更 | 検索・登録・更新の各メソッドに引数 `Locale locale` を追加して `isValid` に渡す。(インデントがスペース→タブに変わっているが、差分からは除外) |
| `templates/todoForm.html` | 変更 | 固定文言を `th:text="#{label.title}"` などに置き換え。各項目にHTMLコメントを追加 |
| `templates/todoList.html` | 変更 | 固定文言を `#{…}` に置き換え。ページ表示は `#{text.paging(現在, 全体)}` で引数つき。完了表示は `'__#{text.done}__'`(先行評価)。HTMLコメントを追加 |
| `settings.gradle` / `Todolist8bApplication.java` / テスト | 変更 | プロジェクト名・クラス名を 7x → 8b に変えただけ |

その他の小さな変更(2026-11-24 本人に確認済み):
- `todoList.html` 先頭の `${#locale.language}=<span th:text="${#locale.language}">` … 今の言語を画面に出す**動作確認用**
- `todoList.html` で `<hr>` が `</form>` の内側から外側に移動 … **特に狙いはない**(見た目もほぼ変わらない)

---

## つまずきポイント・Q&Aログ

(まだなし)

---

## 次にやりたいこと

1. ソースノートで 7章 → 8章(i18n)の差分を読む。特に `MessageSource` と `Locale` がどこから来るか、`#{…}` の仕組み
2. `todolist8b` を起動し、ブラウザの言語設定を英語にして表示とエラーメッセージが切り替わるのを確かめる
3. 参考書の章に沿って、ソースを読み・写経する
