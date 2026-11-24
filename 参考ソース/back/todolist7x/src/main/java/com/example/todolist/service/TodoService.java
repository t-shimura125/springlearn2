package com.example.todolist.service;

import java.time.LocalDate;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;

import com.example.todolist.common.Utils;
import com.example.todolist.entity.Todo;
import com.example.todolist.form.TodoData;
import com.example.todolist.form.TodoQuery;
import com.example.todolist.repository.TodoRepository;

import lombok.AllArgsConstructor;

@Service
@AllArgsConstructor
public class TodoService {
    private final TodoRepository todoRepository;

    /**
     * ToDoの入力内容を検証する。
     * <p>
     * 以下のチェックを行い、違反があれば{@code result}に{@link FieldError}を追加する。
     * <ul>
     *   <li>件名が全角スペースだけで構成されていないこと</li>
     *   <li>期限が過去日付でないこと（{@code isCreate}が{@code true}の新規登録時のみチェック）</li>
     *   <li>期限がyyyy-MM-dd形式で入力されていること</li>
     * </ul>
     *
     * @param todoData 検証対象のToDo入力データ
     * @param result   検証エラーを格納するバインディング結果
     * @param isCreate 新規登録の場合は{@code true}、更新の場合は{@code false}
     *                 （過去日付チェックは新規登録時のみ行う）
     * @return すべての検証を満たす場合は{@code true}、いずれかに違反する場合は{@code false}
     */
    public boolean isValid(TodoData todoData, BindingResult result, boolean isCreate) {
        boolean ans = true;

        // 件名が全角スペースだけで構成されていたらエラー
        if (!Utils.isBlank(todoData.getTitle())) {
            if (Utils.isAllDoubleSpace(todoData.getTitle())) {
                FieldError fieldError = new FieldError(
                        result.getObjectName(),
                        "title",
                        "件名が全角スペースです");
                result.addError(fieldError);
                ans = false;
            }
        }

        // 期限が""ならチェックしない
        String deadline = todoData.getDeadline();
        if (!deadline.equals("")) {
            // yyyy-MM-dd形式チェック
            if (!Utils.isValidDateFormat(deadline)) {
                FieldError fieldError = new FieldError(
                        result.getObjectName(),
                        "deadline",
                        "期限を設定するときはyyyy-mm-dd形式で入力してください");
                result.addError(fieldError);
                ans = false;

            } else {
                // 過去日付チェックは新規登録の場合のみ
                if (isCreate) {
                    // 過去日付ならエラー
                    if (!Utils.isTodayOrFutureDate(deadline)) {
                        FieldError fieldError = new FieldError(
                                result.getObjectName(),
                                "deadline",
                                "期限を設定するときは今日以降にしてください");
                        result.addError(fieldError);
                        ans = false;
                    }
                }
            }
        }

        return ans;
    }

    /**
     * ToDo検索条件の入力内容を検証する。
     * <p>
     * 以下のチェックを行い、違反があれば{@code result}に{@link FieldError}を追加する。
     * <ul>
     *   <li>期限：開始がyyyy-MM-dd形式で入力されていること</li>
     *   <li>期限：終了がyyyy-MM-dd形式で入力されていること</li>
     * </ul>
     *
     * @param todoQuery 検証対象のToDo検索条件
     * @param result    検証エラーを格納するバインディング結果
     * @return すべての検証を満たす場合は{@code true}、いずれかに違反する場合は{@code false}
     */
    public boolean isValid(TodoQuery todoQuery, BindingResult result) {
        boolean ans = true;

        // 期限:開始の形式をチェック
        String date = todoQuery.getDeadlineFrom();
        if (!date.equals("") && !Utils.isValidDateFormat(date)) {
            FieldError fieldError = new FieldError(
                    result.getObjectName(),
                    "deadlineFrom",
                    "期限：開始を入力するときはyyyy-mm-dd形式で入力してください");
            result.addError(fieldError);
            ans = false;
        }

        // 期限:終了の形式をチェック
        date = todoQuery.getDeadlineTo();
        if (!date.equals("") && !Utils.isValidDateFormat(date)) {
            FieldError fieldError = new FieldError(
                    result.getObjectName(),
                    "deadlineTo",
                    "期限：終了を入力するときはyyyy-mm-dd形式で入力してください");
            result.addError(fieldError);
            ans = false;
        }
        return ans;

    }

    /**
     * 検索条件に応じてToDoを検索する。
     * <p>
     * 入力された検索条件を先頭から順に評価し、最初に該当した条件で検索を行う。
     * <ul>
     *   <li>タイトル（部分一致）</li>
     *   <li>重要度</li>
     *   <li>緊急度</li>
     *   <li>期限：開始のみ（開始日以降）</li>
     *   <li>期限：終了のみ（終了日以前）</li>
     *   <li>期限：開始～終了（範囲）</li>
     *   <li>完了状態</li>
     * </ul>
     * いずれの条件も指定されていない場合は全件を検索する。
     *
     * @param todoQuery 検索条件
     * @return 検索条件に一致するToDoのリスト
     */
    public List<Todo> doQuery(TodoQuery todoQuery) {
        List<Todo> todoList = null;
        if (todoQuery.getTitle().length() > 0) {
            // タイトルで検索
            todoList = todoRepository.findByTitleLike("%" + todoQuery.getTitle() + "%");

        } else if (todoQuery.getImportance() != null && todoQuery.getImportance() != -1) {
            // 重要度で検索
            todoList = todoRepository.findByImportance(todoQuery.getImportance());

        } else if (todoQuery.getUrgency() != null && todoQuery.getUrgency() != -1) {
            // 緊急度で検索
            todoList = todoRepository.findByUrgency(todoQuery.getUrgency());

        } else if (!todoQuery.getDeadlineFrom().equals("") &&
                todoQuery.getDeadlineTo().equals("")) {
            // 期限 開始～
            todoList = todoRepository
                    .findByDeadlineGreaterThanEqualOrderByDeadlineAsc(
                            Utils.str2date(todoQuery.getDeadlineFrom()));

        } else if (todoQuery.getDeadlineFrom().equals("") &&
                !todoQuery.getDeadlineTo().equals("")) {
            // 期限 ～終了
            todoList = todoRepository
                    .findByDeadlineLessThanEqualOrderByDeadlineAsc(
                            Utils.str2date(todoQuery.getDeadlineTo()));

        } else if (!todoQuery.getDeadlineFrom().equals("") &&
                !todoQuery.getDeadlineTo().equals("")) {
            // 期限 開始～終了
            todoList = todoRepository
                    .findByDeadlineBetweenOrderByDeadlineAsc(
                            Utils.str2date(todoQuery.getDeadlineFrom()),
                            Utils.str2date(todoQuery.getDeadlineTo()));

        } else if (todoQuery.getDone() != null && todoQuery.getDone().equals("Y")) {
            // 完了で検索
            todoList = todoRepository.findByDone("Y");

        } else {
            // 入力条件が無ければ全件検索
            todoList = todoRepository.findAll();
        }

        return todoList;
    }

    /**
     * Native Queryを使用してToDoを検索する。
     * <p>
     * 検索条件を複数同時に指定できる点が{@code doQuery}と異なる。<br>
     * 各条件は未入力（タイトル・完了状態は空文字、重要度・緊急度は{@code -1}、
     * 期限は空文字）の場合に{@code null}へ変換され、{@code null}の条件は
     * 検索で無視される。<br>
     * 検索結果は{@code pageable}に従いページング（分割）して返す。
     *
     * @param todoQuery 検索条件
     * @param pageable  ページング情報（ページ番号・ページサイズ・ソート順）
     * @return 検索条件に一致するToDoのページ
     */
    public Page<Todo> searchWithNativeQuery(TodoQuery todoQuery, Pageable pageable) {
        String title = todoQuery.getTitle().isEmpty()
                ? null
                : "%" + todoQuery.getTitle() + "%";
        Integer importance = todoQuery.getImportance() == -1
                ? null
                : todoQuery.getImportance();
        Integer urgency = todoQuery.getUrgency() == -1
                ? null
                : todoQuery.getUrgency();
        LocalDate deadlineFrom = todoQuery.getDeadlineFrom().isEmpty()
                ? null
                : Utils.str2date(todoQuery.getDeadlineFrom());
        LocalDate deadlineTo = todoQuery.getDeadlineTo().isEmpty()
                ? null
                : Utils.str2date(todoQuery.getDeadlineTo());
        String done = (todoQuery.getDone() == null || todoQuery.getDone().isEmpty())
                ? null
                : todoQuery.getDone();

        return todoRepository.searchByNativeQuery(
                title,
                importance,
                urgency,
                deadlineFrom,
                deadlineTo,
                done,
                pageable);
    }

}
