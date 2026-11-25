# CLAUDE.md (springlearn2)

Spring Boot学習(シーズン2)用フォルダ `springlearn_season2/` で作業するときのガイドライン。
前シーズン(`C:\localhost\learn\springlearn`)の方針を引き継ぐ。ここには変わりにくい「方針」だけを書き、進捗・つまずき・Q&Aは @HISTORY.md に書く。

**作業を始めるときは、まず `HISTORY.md`(特に「次にやりたいこと」)を読む。**

## プロジェクトの目的

参考書のサンプルコードを読み・写経しながら、分からない点をClaude Codeに質問してSpring Bootを学習する。
通勤中はスマホの claude.ai でソースを読み、質問できるようにしている(下の「スマホ用ページ」)。

## 学習者の背景

- Java Silver取得済み(実務経験は浅い)
- 本番案件はJava(Spring Boot)+ TypeScript
- 前シーズンで game / demo / todolist_ver1(一覧・登録・更新・削除・検索3パターン・ページング)まで実施済み

## 学習の進め方(重要)

- **コードを先に出さず、まず説明してから**進める。理解を優先し、「なぜそうなるか」を大事にする
- 抽象的な仕組み(DI、プロキシなど)は、身近なたとえ話で噛み砕いてから、コードに戻って説明する
- 1度に大量の新概念を詰め込まず、1トピックずつ進める
- 本人が実装した機能を解説してほしいと言われたときは、**`git diff`の変更箇所を中心に**説明する

## フォルダ構成

| パス | 役割 | 扱い |
|---|---|---|
| `参考ソース/Todolist9/` など | 参考書から取得した最新章のサンプル(Eclipse/STSのプロジェクト) | 原本。変更しない。git対象外 |
| `参考ソース/back/` | 前の章の原本(`todolist7x/`, `Todolist8b/`) | 読み取り専用。変更しない |
| `todolist9/` | `参考ソース/Todolist9` から src・sql・Gradle設定をコピーしたアプリ(Spring Boot 4.0.1 / Java 21 / Gradle 9.2.1 / Thymeleaf / JPA / PostgreSQL / Lombok)。最新の版(v2) | 写経・改造する本体 |
| (前の版) | 作業フォルダには置かない。正本は git のタグ(v0 = タグ `v0` の `todolist7x/`、v1 = タグ `v1` の `todolist8b/`)。見るときは `git show v1:todolist8b/…` | 変更しない |
| `.vscode/` | VSCodeの起動設定(`launch.json`)。F5 で `Todolist9Application` が起動する。`参考ソース/` はJavaの読み込み対象外 | |
| `tools/build_mobile.py`(+ `mobile_template.html`, `versions.json`) | git のタグから各版を読み、版どうしを比較してスマホ用ページを作る。版の一覧は `versions.json` | ソースを直したら実行 |
| `公開用/ソースコード.html` | Artifactで公開するファイル(自動生成) | 手で直さない |
| `指示書.txt` | プロジェクト作成時の依頼文 | 参考 |

## 実行環境

- JDK 21(`C:\Program Files\Java\jdk-21`。Gradleのtoolchainが自動で使う。PATHの`java`は25)
- DB: PostgreSQL 18、DB `tododb` / ユーザー `todouser`(前シーズンの todolist_ver1 と共用。`todo`テーブル)
- `application.properties` はパスワードを含むため、どのフォルダのものも git対象外(ルートの `.gitignore`)。代わりに `application.properties.example` をコミットしている
- コマンドで起動する場合: `cd todolist9` → `.\gradlew.bat bootRun` → http://localhost:8080/todo
- 新しい章のサンプルを動かすときは、同じ手順で src・sql・Gradle設定(`gradle/`, `gradlew*`, `build.gradle`, `settings.gradle`)と `.gitignore` `.gitattributes` をルート直下の新しいフォルダにコピーし、`application.properties.example`(パスワード空)を作り、`launch.json` を書き換える。そのあとは @改修反映ルール.md の手順(コミット → タグ → `versions.json` → ノート再生成)

## スマホ用ページ(claude.ai の Artifact)

| ページ | URL | 公開するファイル |
|---|---|---|
| ソースノート | https://claude.ai/artifact/Fz11HjhDUs6TsNBXdkV6bg | `公開用/ソースコード.html` |

- ソースや `HISTORY.md` を直したら `py tools\build_mobile.py` を実行し、上の URL に再公開する(新しい URL を作らない。別の会話からは `url` を指定する)
- 版(最新5版まで)と比較元を選んで表示でき、版の側では追加行(緑)・変更行(青)、比較元の側では変更前(青)・削除行(赤)に色が付く。ファイル一覧では変更のあるファイルを先頭にまとめて印を付け、版ごとの日付と変更メモも見られる
- 質問には表示中の版のコードが渡り、質問ログ(`qa`)には `ver`(質問した版)と `cmp`(比較元→版)が残る。比較機能を入れる前のログの `ver: old/new` は v0 / v1 として扱う
- ページ内で行を選んで Claude に質問でき、質問と回答はページのDB(コレクション `qa`)に残る。PCで作業するときは `ArtifactData` で `qa` を読み、大事なものは `HISTORY.md` のQ&Aログに転記する
- 非公開(本人のみ)

## 改修の反映ルール

改修ソースをソースノートに反映するとき(版の管理・タグ付け・差分の取り方・ノートの表示要件)は、@改修反映ルール.md に従う。

## 運用ルール

- 新しい概念でつまずいたら、`HISTORY.md`の「つまずきポイント・Q&Aログ」に日付付きで追記する
- アプリの実装が進んだら、`HISTORY.md`の「演習アプリ別ログ」を更新する
- GitHub(`t-shimura125/springlearn2`)にpushして、他の端末からも参照できるようにする
