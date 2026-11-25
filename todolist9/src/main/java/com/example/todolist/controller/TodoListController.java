package com.example.todolist.controller;

import java.util.Locale;

import jakarta.servlet.http.HttpSession;

import org.springframework.context.MessageSource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.servlet.ModelAndView;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import com.example.todolist.common.OpMsg;
import com.example.todolist.dao.TodoDao;
import com.example.todolist.entity.Todo;
import com.example.todolist.form.TodoData;
import com.example.todolist.form.TodoQuery;
import com.example.todolist.repository.TodoRepository;
import com.example.todolist.service.TodoService;

import lombok.RequiredArgsConstructor;

@Controller
@RequiredArgsConstructor
public class TodoListController {
	private final TodoRepository todoRepository;
	private final TodoService todoService;
	private final HttpSession session;
	private final TodoDao todoDao;
	private final MessageSource messageSource;

	//  Todo一覧表示
	@GetMapping("/todo")
	public ModelAndView showTodoList(ModelAndView mv,
			@PageableDefault(page = 0, size = 5, sort = "id") Pageable pageable) {
		//sessionから前回の検索条件を取得
		TodoQuery todoQuery = (TodoQuery) session.getAttribute("todoQuery");
		if (todoQuery == null) {
			//なければ初期値を使う
			todoQuery = new TodoQuery();
			//セッションへ保存
			session.setAttribute("todoQuery", todoQuery);
		}

		//sessionから前回のpageableを取得
		Pageable prevPageable = (Pageable) session.getAttribute("prevPageable");
		if (prevPageable == null) {
			//なければ@PageableDefaultを使う
			prevPageable = pageable;
			//セッションへ保存
			session.setAttribute("prevPageable", prevPageable);
		}
		mv.setViewName("todoList");
		Page<Todo> todoPage = todoDao.findByCriteria(todoQuery, prevPageable);
		mv.addObject("todoQuery", todoQuery);
		mv.addObject("todoPage", todoPage);
		mv.addObject("todoList", todoPage.getContent());
		return mv;
	}

	//  ToDo一覧画面(todoList.html)で[検索]ボタンが押された時の処理
	@GetMapping("/todo/query")
	public ModelAndView queryTodo(
			@ModelAttribute TodoQuery todoQuery,
			BindingResult result,
			@PageableDefault(page = 0, size = 5) Pageable pageable,
			ModelAndView mv,
			Locale locale) {
		mv.setViewName("todoList");

		if (todoService.isValid(todoQuery, result, locale)) {
			// エラーがなければ検索
			Page<Todo> todoPage = todoService.searchWithNativeQuery(todoQuery, pageable);

			// 入力された検索条件をsessionに保存
			session.setAttribute("todoQuery", todoQuery);

			mv.addObject("todoPage", todoPage);
			mv.addObject("todoList", todoPage.getContent());
			
            // 該当なかったらメッセージを表示
            if (todoPage.getContent().size() == 0) {
                String msg = messageSource.getMessage("msg.w.todo_not_found", null, locale);
                mv.addObject("msg", new OpMsg("W", msg));
            }

		} else {
            // 検索条件エラーあり -> エラーメッセージをセット
            String msg = messageSource.getMessage("msg.e.input_something_wrong", null, locale);
            mv.addObject("msg", new OpMsg("E", msg));

			mv.addObject("todoPage", null);
			mv.addObject("todoList", null);
		}

		return mv;
	}

	//  ToDo一覧画面(todoList.html)でページリンクがクリックされたときの処理
	@GetMapping("/todo/query2")
	public ModelAndView queryTodo(@PageableDefault(page = 0, size = 5) Pageable pageable,
			ModelAndView mv) {
		//現在のページ位置を保存
		session.setAttribute("prevPageable", pageable);
		mv.setViewName("todoList");

		// sessionに保存されている条件で検索
		TodoQuery todoQuery = (TodoQuery) session.getAttribute("todoQuery");
		//Page<Todo> todoPage = todoDao.findByCriteria(todoQuery, pageable); 
		//  ↓
		Page<Todo> todoPage = todoService.searchWithNativeQuery(todoQuery, pageable);

		mv.addObject("todoQuery", todoQuery); // 検索条件表示用
		mv.addObject("todoPage", todoPage); // page情報
		mv.addObject("todoList", todoPage.getContent()); // 検索結果

		return mv;
	}

	//  ToDo一覧画面(todoList.html)でTodoの件名がクリックされた時の処理
	@GetMapping("/todo/{id}")
	public ModelAndView todoById(@PathVariable(name = "id") int id, ModelAndView mv) {
		mv.setViewName("todoForm");
		Todo todo = todoRepository.findById(id).get();
		mv.addObject("todoData", todo);
		session.setAttribute("mode", "update");
		return mv;
	}

	//  ToDo一覧画面(todoList.html)で[新規追加]ボタンがクリックされた時の処理
	@GetMapping("/todo/create/form")
	public ModelAndView createTodo(ModelAndView mv) {
		mv.setViewName("todoForm");
		mv.addObject("todoData", new TodoData());
		session.setAttribute("mode", "create");
		return mv;
	}

	//  ToDo入力画面(todoForm.html)で[登録]ボタンがクリックされた時の処理
	@PostMapping("/todo/create/do")
	public ModelAndView createTodo(
			@ModelAttribute @Validated TodoData todoData,
			BindingResult result,
			ModelAndView mv,
			RedirectAttributes redirectAttributes,
			Locale locale) {

		// エラーチェック
		boolean isValid = todoService.isValid(todoData, result, true, locale);
		if (!result.hasErrors() && isValid) {
			// エラーなし
			Todo todo = todoData.toEntity();
			todoRepository.saveAndFlush(todo);
			
            // 追加完了メッセージをセットしてリダイレクト
            String msg = messageSource.getMessage("msg.i.todo_created", null, locale);
            redirectAttributes.addFlashAttribute("msg", new OpMsg("I", msg));

			mv.setViewName("redirect:/todo");

		} else {
			// エラーあり -> エラーメッセージをセット
            mv.setViewName("todoForm");
            String msg = messageSource.getMessage("msg.e.input_something_wrong", null, locale);
            mv.addObject("msg", new OpMsg("E", msg));

		}
		
		return mv;
	}

	//  ToDo入力画面(todoForm.html)で[更新]ボタンがクリックされた時の処理
	@PostMapping("/todo/update")
	public String updateTodo(
			@ModelAttribute @Validated TodoData todoData,
			BindingResult result,
			Model model,
			RedirectAttributes redirectAttributes,
			Locale locale) {
		
		// エラーチェック
		boolean isValid = todoService.isValid(todoData, result, false, locale);
		if (!result.hasErrors() && isValid) {
			// エラーなし-> 更新
			Todo todo = todoData.toEntity();
			todoRepository.saveAndFlush(todo);
			
	        // 更新完了メッセージをセットしてリダイレクト
            String msg = messageSource.getMessage("msg.i.todo_updated", null, locale);
            redirectAttributes.addFlashAttribute("msg", new OpMsg("I", msg)); 
			return "redirect:/todo";

		} else {
	        // エラーあり -> エラーメッセージをセット
            String msg = messageSource.getMessage("msg.e.input_something_wrong", null, locale);
            model.addAttribute("msg", new OpMsg("E", msg));
            return "todoForm";
		}
	}

	//  ToDo入力画面(todoForm.html)で[削除]ボタンがクリックされた時の処理
	@PostMapping("/todo/delete")
	public String deleteTodo(
			@ModelAttribute TodoData todoData,
			RedirectAttributes redirectAttributes, 
            Locale locale) {
		// 削除
		todoRepository.deleteById(todoData.getId());
		
        // 削除完了メッセージをセットしてリダイレクト
        String msg = messageSource.getMessage("msg.i.todo_deleted", null, locale);
        redirectAttributes.addFlashAttribute("msg", new OpMsg("I", msg));

		return "redirect:/todo";
	}

	//  ToDo入力画面(todoForm.html)で[キャンセル]ボタンがクリックされた時の処理
	@PostMapping("/todo/cancel")
	public String cancel() {
		return "redirect:/todo";
	}

}
