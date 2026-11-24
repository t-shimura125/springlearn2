"""ソースコードを1枚の HTML にまとめ、スマホ(claude.ai の Artifact)で読めるようにする。

使い方(プロジェクト直下で):  py tools\\build_mobile.py
出力:  公開用\\ソースコード.html

「元」と「改修後」の2つのアプリを読み込み、ファイル単位・行単位で比較する(差分学習)。
  - ノート上で 元 / 改修後 を切り替えて読める
  - 差分は行単位(追加・変更・削除)。空白(インデント・タブ)だけの違いは差分にしない
比較する2つのフォルダは下の VERSIONS で指定する。章が進んだらここを書き換える。
DB のパスワードは載せない(.example があればそれを、無ければ application.properties のパスワードを空にして載せる)。
ソースを直したら、これを実行して Artifact を同じ URL に再公開する(URL は CLAUDE.md)。
"""
import datetime
import difflib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / 'mobile_template.html'
OUT = ROOT / '公開用' / 'ソースコード.html'

# 比較する2つの版。key は 'old'(元)と 'new'(改修後)で固定。
#   dir:   アプリのフォルダ(build.gradle がある所)
#   name:  ノート上でのパスの先頭(質問ログに残る。元は以前と同じ 'todolist7x' にして、過去の質問ログを開けるようにする)
#   token: クラス名などに入るアプリ名。比較では同じものとみなす(Todolist7xApplication ↔ Todolist8bApplication)
VERSIONS = {
    'old': {'dir': ROOT / '参考ソース' / 'back' / 'todolist7x', 'name': 'todolist7x', 'token': 'Todolist7x',
            'label': '元', 'desc': '7章 todolist7x'},
    'new': {'dir': ROOT / 'todolist8b', 'name': 'todolist8b', 'token': 'Todolist8b',
            'label': '改修後', 'desc': '8章 todolist8b'},
}
PROPS = 'src/main/resources/application.properties'
CHANGE_NAMES = {'replace': '変更', 'delete': '削除', 'insert': '追加'}

EXT_LANG = {'.java': 'java', '.html': 'xml', '.css': 'css', '.js': 'javascript', '.sql': 'sql',
            '.gradle': 'groovy', '.properties': 'ini', '.example': 'ini', '.md': 'markdown'}
# パッケージ名(フォルダ名)から付ける役割の表示
ROLE = {'controller': 'Controller', 'service': 'Service', 'repository': 'Repository', 'dao': 'DAO',
        'entity': 'Entity', 'form': 'Form', 'common': '共通処理', 'templates': '画面(Thymeleaf)',
        'css': 'CSS', 'sql': 'SQL', 'test': 'テスト', 'i18n': 'メッセージ', 'resources': '設定'}
MAIN_FILE = 'TodoListController.java'  # 最初に開くファイル

# 質問するときに Claude へ毎回渡す前提(CLAUDE.md の学習方針と同じ内容)
GUIDE = """あなたは Spring Boot を学習中の人の先生です。参考書のサンプルコード(下に全文あり)を読みながら、通勤中にスマホで質問しています。日本語で答えてください。

# 学習者
- Java Silver 取得済み(実務経験は浅い)。本番案件は Java(Spring Boot)+ TypeScript
- 前シーズンで Controller / Repository / Thymeleaf / JPA の基本、検索・ページングまで写経済み
- いまは参考書の「元」の版(7章 todolist7x)と「改修後」の版(8章 todolist8b)を見比べて、何が変わったかを学んでいる

# 答え方
- コードを丸ごと書き直して見せるのではなく、まず「なぜそうなるか」を説明する
- 抽象的な仕組み(DI、プロキシ、セッションなど)は身近なたとえ話で噛み砕いてから、コードの該当行に戻って説明する
- コードに触れるときは「TodoListController.java の 40行目」のようにファイル名と行番号で示す(行番号は、いま表示している版のもの)
- 元と改修後の違いに関する質問なら、下の「元からの差分」を使って、どこがどう変わったかを示す
- 1度に新しい概念を詰め込みすぎない。スマホで読むので、見出しと短い段落・箇条書きで簡潔に
- 下に載っているコードに無いことを推測で断定しない。分からないことは分からないと言う"""


def read(p):
    return p.read_text(encoding='utf-8').replace('\r\n', '\n').rstrip('\n')


def app_files(v):
    """版 v のファイルを {比較用キー: (ノート上のパス, 中身)} で返す"""
    conf = VERSIONS[v]
    app = conf['dir']
    paths = [app / 'build.gradle', app / 'settings.gradle']
    paths += sorted((app / 'sql').glob('*')) if (app / 'sql').exists() else []
    paths += sorted(p for p in (app / 'src').rglob('*') if p.is_file())
    out = {}
    for p in paths:
        if not p.exists():
            continue
        rel = p.relative_to(app).as_posix()
        if rel in (PROPS, PROPS + '.example'):
            continue  # DB 設定は下で別に扱う
        out[rel.replace(conf['token'], '{app}')] = (f"{conf['name']}/{rel}", read(p))
    # DB 設定: .example があればそれを、無ければ本物のパスワードを空にしたものを載せる(比較上は同じファイル扱い)
    ex, real = app / (PROPS + '.example'), app / PROPS
    if ex.exists():
        out[PROPS] = (f"{conf['name']}/{PROPS}.example", read(ex))
    elif real.exists():
        text = re.sub(r'(?m)^(spring\.datasource\.password\s*=).*$', r'\1', read(real))
        out[PROPS] = (f"{conf['name']}/{PROPS}", text)
    return out


def norm(line):
    """比較用: 空白(タブ・インデント・行末)の違いは無視する"""
    return ' '.join(line.split())


def diff(old_text, new_text):
    """行単位の差分。marks は 版ごとの {行番号(1始まり): 'add'|'chg'|'del'}"""
    a, b = old_text.split('\n'), new_text.split('\n')
    sm = difflib.SequenceMatcher(None, [norm(x) for x in a], [norm(x) for x in b], autojunk=False)
    old_marks, new_marks, del_after, hunks = {}, {}, [], []
    stat = {'add': 0, 'chg': 0, 'del': 0}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        if tag == 'replace':
            for i in range(i1, i2):
                old_marks[i + 1] = 'chg'
            for j in range(j1, j2):
                new_marks[j + 1] = 'chg'
            stat['chg'] += j2 - j1
        elif tag == 'delete':
            for i in range(i1, i2):
                old_marks[i + 1] = 'del'
            del_after.append(j1)  # 改修後の j1 行目の後ろで消えた(0 なら先頭)
            stat['del'] += i2 - i1
        elif tag == 'insert':
            for j in range(j1, j2):
                new_marks[j + 1] = 'add'
            stat['add'] += j2 - j1
        # 質問時に Claude へ渡す差分(行番号つき)
        h = [f'@@ 元 {i1 + 1}〜{i2}行目 → 改修後 {j1 + 1}〜{j2}行目({CHANGE_NAMES[tag]})']
        h += [f'- {i + 1}: {a[i]}' for i in range(i1, i2)]
        h += [f'+ {j + 1}: {b[j]}' for j in range(j1, j2)]
        hunks.append('\n'.join(h))
    return {'old': old_marks, 'new': new_marks}, del_after, stat, '\n\n'.join(hunks)


def collect():
    sides = {v: app_files(v) for v in VERSIONS}
    keys = list(sides['old']) + [k for k in sides['new'] if k not in sides['old']]
    files = []
    for key in keys:
        o, n = sides['old'].get(key), sides['new'].get(key)
        base = o or n
        rel = key.replace('{app}', VERSIONS['old' if o else 'new']['token'])
        parts = rel.split('/')
        # 一覧では「src/main 配下(アプリ本体)」と「それ以外(Gradle設定・SQL・テストなど)」を分けて表示する
        is_main = rel.startswith('src/main/')
        d = '/'.join(parts[2:-1] if is_main else parts[:-1])
        role = next((ROLE[x] for x in reversed(parts[:-1]) if x in ROLE), '')
        f = {'id': base[0],  # 質問ログに残る識別子(元にあるファイルは以前と同じパス)
             'dir': d, 'sec': 'main' if is_main else 'other', 'role': role,
             'lang': EXT_LANG.get(Path(base[0]).suffix, ''), 'main': Path(base[0]).name == MAIN_FILE}
        for v, s in (('old', o), ('new', n)):
            f[v] = {'path': s[0], 'name': Path(s[0]).name, 'text': s[1]} if s else None
        if o and n:
            marks, del_after, stat, hunks = diff(o[1], n[1])
            f['status'] = 'mod' if hunks else 'same'
        else:
            cnt = len(base[1].split('\n'))
            every = {i + 1: ('del' if o else 'add') for i in range(cnt)}
            marks = {'old': every, 'new': {}} if o else {'old': {}, 'new': every}
            del_after, hunks = [], ''
            stat = {'add': 0 if o else cnt, 'chg': 0, 'del': cnt if o else 0}
            f['status'] = 'del' if o else 'add'
        f.update(marks=marks, delAfter=del_after, stat=stat, diff=hunks)
        files.append(f)
    p = ROOT / 'HISTORY.md'
    if p.exists():
        doc = {'path': 'HISTORY.md', 'name': 'HISTORY.md', 'text': read(p)}
        files.append({'id': 'HISTORY.md', 'dir': '学習メモ', 'sec': 'other', 'role': '進捗・Q&A', 'lang': 'markdown',
                      'main': False, 'old': doc, 'new': doc, 'status': 'same', 'doc': True,
                      'marks': {'old': {}, 'new': {}}, 'delAfter': [], 'stat': {'add': 0, 'chg': 0, 'del': 0}, 'diff': ''})
    # src/main 配下を先に並べる(同じ区分の中は元の順番のまま)
    files.sort(key=lambda f: f['sec'] != 'main')
    return files


def main():
    files = collect()
    vers = {v: {'label': c['label'], 'desc': c['desc']} for v, c in VERSIONS.items()}
    data = {'built': datetime.datetime.now().strftime('%Y/%m/%d %H:%M'), 'guide': GUIDE, 'versions': vers, 'files': files}
    js = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    html = TEMPLATE.read_text(encoding='utf-8').replace('/*__DATA__*/null', js)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding='utf-8')
    count = {}
    for f in files:
        count[f['status']] = count.get(f['status'], 0) + 1
    print(f'{OUT.relative_to(ROOT)}: {len(files)}ファイル, {len(html) // 1024}KB  ' + ', '.join(f'{k}={v}' for k, v in count.items()))
    for f in files:
        if f['status'] != 'same':
            s = f['stat']
            print(f"  [{f['status']}] {(f['new'] or f['old'])['path']}  +{s['add']} ~{s['chg']} -{s['del']}")


if __name__ == '__main__':
    main()
