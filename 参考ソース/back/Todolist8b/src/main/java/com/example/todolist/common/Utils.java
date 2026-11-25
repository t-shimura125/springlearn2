package com.example.todolist.common;

import java.time.DateTimeException;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

public class Utils {

    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    /**
     * 文字列をyyyy-MM-dd型の日付としてjava.time.LocalDateオブジェクトへ変換する。<br>
     * 
     * @param s 変換対象
     * @return 変換結果(引数がnull, "", yyyy-MM-dd形式でなければnullを返す)
     */
    public static LocalDate str2date(String s) {
        if (s == null || s.equals("")) {
            return null;
        }
        try {
            return LocalDate.parse(s, FORMATTER);
        } catch (DateTimeException e) {
            e.printStackTrace();
            return null;
        }
    }

    /**
     * 文字列をyyyy-MM-dd型の日付としてjava.time.LocalDateオブジェクトへ変換する。<br>
     * 
     * @param s 変換対象
     * @return 変換結果(変換できなければnullを返す)
     */
    public static LocalDate str2dateOrNull(String s) {
        if (s == null || s.equals("")) {
            return null;
        }

        try {
            return LocalDate.parse(s, FORMATTER);
        } catch (DateTimeException e) {
            // 変換できなかった場合は null を返す
            return null;
        }
    }

    /**
     * 引数が全角SPACEだけで構成されていればtrueを返す
     * 
     * @param s チェック対象
     * @return true:全角SPACEのみ, "", null false:左記以外
     */
    public static boolean isAllDoubleSpace(String s) {
        if (s == null || s.equals("")) {
            return true;
        }

        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) != '　') { // 全角SPACE
                return false;
            }
        }
        return true;
    }

    /**
     * 引数が"" or 半角SPACE/TABだけで構成されているならtrueを返す
     * 
     * @param s チェック対象
     * @return true:半角SPACE/TABのみ or "", null, false:左記以外
     */
    public static boolean isBlank(String s) {
        if (s == null || s.equals("")) {
            return true;
        }

        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) != ' ' && s.charAt(i) != '\t') {// 半角SPACE
                return false;
            }
        }
        return true;
    }

    /**
     * 引数がyyyy-MM-ddと解釈できればtrueを返す
     * 
     * @param str チェック対象
     * @return true:yyyy-MM-ddと解釈できる、false:解釈できない or 引数がnull or ""
     */
    public static boolean isValidDateFormat(String str) {
        if (str == null || str.equals("")) {
            return false;
        }

        try {
            // parseできればyyyy-mm-dd形式とみなす
            LocalDate.parse(str);
            return true;

        } catch (DateTimeException e) {
            // yyyy-mm-dd形式以外
            return false;
        }
    }

    /**
     * 引数が今日以降の日付を表す文字列(yyyy-MM-dd形式)ならtrueを返す
     * 
     * @param str チェック対象
     * @return true:今日以降、false:昨日以前、引数がyyyy-MM-dd形式でない or null or ""
     */
    public static boolean isTodayOrFutureDate(String s) {
        if (s == null || s.equals("")) {
            return false;
        }

        LocalDate today = LocalDate.now();
        LocalDate deadlineDate = null;
        try {
            // "yyyy-mm-dd" -> LocalDate
            deadlineDate = LocalDate.parse(s);
            if (deadlineDate.isBefore(today)) {
                // 過去日付なのでfalse
                return false;

            } else {
                return true;
            }

        } catch (DateTimeException e) {
            e.printStackTrace();
            return false;
        }
    }

    /**
     * LocalDateオブジェクトをyyyy-MM-dd形式の文字列へ変換する。<br>
     * 
     * @param date 変換対象
     * @return 変換結果(引数がnullなら""を返す)
     */
    public static String date2str(LocalDate date) {
        String s = "";
        if (date != null) {
            s = date.format(FORMATTER);
        }
        return s;
    }
}
