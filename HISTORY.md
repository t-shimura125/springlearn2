# HISTORY.md (springlearn2)

学習の履歴ログ。演習アプリの進捗、つまずいたポイント・Q&A、次にやりたいことを都度追記していく。
方針は`CLAUDE.md`を参照。

## 演習アプリ別ログ

### todolist7x(ToDoアプリ、参考書のサンプル)

- 2026-11-16: 参考書のサンプル(`sampleSource/`)を`todolist7x/`にコピーしてプロジェクト作成。ビルド・起動(`GET /todo`)・DB接続(`tododb`)を確認済み
- 構成: `controller/TodoListController` → `service/TodoService` → `repository/TodoRepository`(JpaRepository) / `dao/TodoDaoImpl`(EntityManager で条件検索+ページング)。`form/TodoData`(入力フォーム)、`form/TodoQuery`(検索条件)、`entity/Todo`、`common/Utils`
- 前シーズンの todolist_ver1 との違い(ざっと見た範囲): Spring Boot 4.0.1 / Java 21、`@RequiredArgsConstructor`でのコンストラクタインジェクション、`hibernate-processor`(JPAメタモデル生成)の追加

---

## つまずきポイント・Q&Aログ

(まだなし)

---

## 次にやりたいこと

1. `todolist7x` を起動して画面を一通り触り、前シーズンの todolist_ver1 との違いを確認する
2. 参考書の章に沿って、ソースを読み・写経する
