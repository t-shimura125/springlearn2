"""ソースコードを1枚の HTML にまとめ、スマホ(claude.ai の Artifact)で読めるようにする。

使い方(プロジェクト直下で):  py tools\\build_mobile.py
出力:  公開用\\ソースコード.html

版(v0, v1, ...)ごとのソースを git のタグから読み込み、版どうしをファイル単位・行単位で比較する(差分学習)。
  - 版の一覧は tools/versions.json(タグ・フォルダ・日付・変更メモ)。改修を反映したら1行足す
  - ノートに入れるのは最新 MAX_VERSIONS 版だけ。古い版は git に残る
  - 差分は git diff(-w: 空白・インデント・改行コードの違いは無視)で取る
  - 同じ内容のファイルは、版をまたいで1つだけ埋め込む
手順と決まりは 改修反映ルール.md。
DB のパスワードは載せない(.example があればそれを、無ければ application.properties のパスワードを空にして載せる)。
ソースを直したら、これを実行して Artifact を同じ URL に再公開する(URL は CLAUDE.md)。
"""
import datetime
import difflib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / 'mobile_template.html'
VERSIONS_FILE = Path(__file__).resolve().parent / 'versions.json'
OUT = ROOT / '公開用' / 'ソースコード.html'
MAX_VERSIONS = 5
PROPS = 'src/main/resources/application.properties'
PAIR_RATIO = 0.5  # 削除行と追加行が隣り合っているとき、この似ている度合い以上なら「変更行」とみなす

EXT_LANG = {'.java': 'java', '.html': 'xml', '.css': 'css', '.js': 'javascript', '.sql': 'sql',
            '.gradle': 'groovy', '.properties': 'ini', '.example': 'ini', '.md': 'markdown'}
# パッケージ名(フォルダ名)から付ける役割の表示
ROLE = {'controller': 'Controller', 'service': 'Service', 'repository': 'Repository', 'dao': 'DAO',
        'entity': 'Entity', 'form': 'Form', 'common': '共通処理', 'templates': '画面(Thymeleaf)',
        'css': 'CSS', 'icons': '画像', 'sql': 'SQL', 'test': 'テスト', 'i18n': 'メッセージ', 'resources': '設定'}
MAIN_FILE = 'TodoListController.java'  # 最初に開くファイル

# 質問するときに Claude へ毎回渡す前提(CLAUDE.md の学習方針と同じ内容)
GUIDE = """あなたは Spring Boot を学習中の人の先生です。参考書のサンプルコード(下に全文あり)を読みながら、通勤中にスマホで質問しています。日本語で答えてください。

# 学習者
- Java Silver 取得済み(実務経験は浅い)。本番案件は Java(Spring Boot)+ TypeScript
- 前シーズンで Controller / Repository / Thymeleaf / JPA の基本、検索・ページングまで写経済み
- いまは参考書の章ごとの版(v0, v1, ...)を見比べて、何が変わったかを学んでいる

# 答え方
- コードを丸ごと書き直して見せるのではなく、まず「なぜそうなるか」を説明する
- 抽象的な仕組み(DI、プロキシ、セッションなど)は身近なたとえ話で噛み砕いてから、コードの該当行に戻って説明する
- コードに触れるときは「TodoListController.java の 40行目」のようにファイル名と行番号で示す(行番号は、いま表示している版のもの)
- 版の違いに関する質問なら、下の「差分」を使って、どこがどう変わったかを示す
- 1度に新しい概念を詰め込みすぎない。スマホで読むので、見出しと短い段落・箇条書きで簡潔に
- 下に載っているコードに無いことを推測で断定しない。分からないことは分からないと言う"""


def git(*args, binary=False):
    r = subprocess.run(['git', '-c', 'core.quotepath=false', *args], cwd=ROOT, capture_output=True)
    if r.returncode not in (0, 1):  # diff は差分ありで 1 を返す
        sys.exit(f'git {" ".join(args)} に失敗: {r.stderr.decode("utf-8", "replace")}')
    return r.stdout if binary else r.stdout.decode('utf-8')


def to_text(raw):
    """テキストなら改行を LF にそろえて返す。画像などのバイナリは None"""
    if b'\0' in raw:
        return None
    try:
        return raw.decode('utf-8').replace('\r\n', '\n').rstrip('\n')
    except UnicodeDecodeError:
        return None


def version_files(v):
    """版 v のファイルを {比較用キー: (ノート上のパス, 中身 or None)} で git のタグから読む"""
    out, props = {}, {}
    for entry in git('ls-tree', '-r', '-z', v['tag'], '--', v['dir'] + '/').split('\0'):
        if not entry:
            continue
        info, full = entry.split('\t', 1)
        oid = info.split()[2]
        rel = full[len(v['dir']) + 1:]
        if not (rel in ('build.gradle', 'settings.gradle') or rel.startswith(('sql/', 'src/'))):
            continue
        item = (full, to_text(git('cat-file', 'blob', oid, binary=True)), oid)
        if rel in (PROPS, PROPS + '.example'):
            props[rel] = item  # DB 設定は下で別に扱う
            continue
        out[rel.replace(v['token'], '{app}')] = item
    # DB 設定: .example があればそれを、無ければパスワードを空にしたものを載せる(比較上は同じファイル扱い)
    if PROPS + '.example' in props:
        out[PROPS] = props[PROPS + '.example']
    elif PROPS in props:
        full, text, oid = props[PROPS]
        out[PROPS] = (full, re.sub(r'(?m)^(spring\.datasource\.password\s*=).*$', r'\1', text or ''), oid)
    return out


def norm(line):
    """空白(タブ・インデント・行末・改行コード)の違いは無視する"""
    return ' '.join(line.split())


HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', re.M)


def git_hunks(a_text, b_text):
    """git diff(-w, 改行コード無視)の変更ブロックを [(元の開始, 元の行数, 新の開始, 新の行数)] で返す"""
    with tempfile.TemporaryDirectory() as d:
        pa, pb = Path(d) / 'a', Path(d) / 'b'
        pa.write_text(a_text + '\n', encoding='utf-8', newline='\n')
        pb.write_text(b_text + '\n', encoding='utf-8', newline='\n')
        out = git('diff', '--no-index', '--no-color', '-w', '--ignore-cr-at-eol', '-U0', str(pa), str(pb))
    return [(int(m[1]), 1 if m[2] is None else int(m[2]), int(m[3]), 1 if m[4] is None else int(m[4]))
            for m in HUNK.finditer(out)]


def pair_lines(olds, news):
    """隣り合った削除行と追加行のうち、置き換えと判断できる組を、順番を保って選ぶ(似ている度合いの合計が最大)"""
    n, m = len(olds), len(news)
    r = [[difflib.SequenceMatcher(None, norm(o), norm(x), autojunk=False).ratio() for x in news] for o in olds]
    best = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            take = best[i + 1][j + 1] + r[i][j] if r[i][j] >= PAIR_RATIO else -1
            best[i][j] = max(best[i + 1][j], best[i][j + 1], take)
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if r[i][j] >= PAIR_RATIO and best[i][j] == best[i + 1][j + 1] + r[i][j]:
            pairs.append((i, j)); i += 1; j += 1
        elif best[i][j] == best[i + 1][j]:
            i += 1
        else:
            j += 1
    return pairs


def diff(a_text, b_text, a_name, b_name):
    """比較元 a → 版 b の行単位の差分。
    ma: 比較元の {行番号: 'chg'|'del'}、mb: 版の {行番号: 'add'|'chg'}、da: 版の何行目の後ろで比較元の行が消えたか"""
    a, b = a_text.split('\n'), b_text.split('\n')
    ma, mb, da, hunks = {}, {}, set(), []
    for s1, c1, s2, c2 in git_hunks(a_text, b_text):
        olds = list(range(s1, s1 + c1))                    # 1始まりの行番号
        news = list(range(s2, s2 + c2))
        pairs = pair_lines([a[i - 1] for i in olds], [b[j - 1] for j in news])
        po, pn = {olds[i] for i, _ in pairs}, {news[j] for _, j in pairs}
        for i in olds:
            ma[i] = 'chg' if i in po else 'del'
        for j in news:
            mb[j] = 'chg' if j in pn else 'add'
        # 消えた行の位置(直前にある対応済みの行の後ろ。無ければブロックの直前)
        if c2 == 0:
            da.add(s2)                                      # git は「新の s2 行目の後ろ」で表す
        else:
            for k, i in enumerate(olds):
                if i not in po:
                    prev = [news[j] for oi, j in pairs if olds[oi] < i]
                    da.add(max(prev) if prev else s2 - 1)
        h = [f'@@ {a_name} {s1}〜{s1 + c1 - 1}行目 → {b_name} {s2}〜{s2 + c2 - 1}行目' if c1 and c2 else
             f'@@ {b_name} {s2}〜{s2 + c2 - 1}行目に追加' if c2 else f'@@ {a_name} {s1}〜{s1 + c1 - 1}行目を削除']
        h += [f'- {i}: {a[i - 1]}' for i in olds] + [f'+ {j}: {b[j - 1]}' for j in news]
        hunks.append('\n'.join(h))
    stat = {'add': sum(1 for x in mb.values() if x == 'add'), 'chg': sum(1 for x in mb.values() if x == 'chg'),
            'del': sum(1 for x in ma.values() if x == 'del'), 'chgOld': sum(1 for x in ma.values() if x == 'chg')}
    return {'ma': ma, 'mb': mb, 'da': sorted(da), 'stat': stat, 'diff': '\n\n'.join(hunks)}


def compare(fa, fb, a_name, b_name):
    """同じキーのファイル同士(どちらかが None なら追加/削除)の比較結果。変更なしなら None"""
    if not fa and not fb:
        return None
    if fa and fb:
        ta, tb = fa[1], fb[1]
        if fa[2] == fb[2]:
            return None
        if ta is None or tb is None:  # 画像など(中身は比べず、変わったことだけ)
            return {'st': 'mod', 'stat': {}, 'diff': '(画像ファイルが変わった)'}
        if [norm(x) for x in ta.split('\n')] == [norm(x) for x in tb.split('\n')]:
            return None
        d = diff(ta, tb, a_name, b_name)
        return dict(d, st='mod') if d['diff'] else None
    if fb:
        n = 0 if fb[1] is None else len(fb[1].split('\n'))
        return {'st': 'add', 'stat': {'add': n}, 'diff': f'{b_name} で新しく追加されたファイル'}
    n = 0 if fa[1] is None else len(fa[1].split('\n'))
    return {'st': 'del', 'stat': {'del': n}, 'diff': f'{b_name} で削除されたファイル'}


def collect():
    all_vers = json.loads(VERSIONS_FILE.read_text(encoding='utf-8'))
    for v in all_vers:
        if not git('tag', '-l', v['tag']).strip():
            sys.exit(f"タグ {v['tag']} がありません(先に改修後をコミットしてタグを付ける)")
    vers = all_vers[-MAX_VERSIONS:]
    before = all_vers[-MAX_VERSIONS - 1] if len(all_vers) > MAX_VERSIONS else None  # ノートから外れた、最古の版の1つ前
    side = {v['id']: version_files(v) for v in vers + ([before] if before else [])}

    # ファイルの並び: 最新版にある順 → 古い版にだけあるもの
    keys = []
    for v in reversed(vers):
        keys += [k for k in side[v['id']] if k not in keys]
    blobs, blob_ix = [], {}

    def blob(text):
        if text not in blob_ix:
            blob_ix[text] = len(blobs)
            blobs.append(text)
        return blob_ix[text]

    files = []
    for key in keys:
        at = {}
        for v in vers:
            s = side[v['id']].get(key)
            if s:
                full, text, _ = s
                at[v['id']] = {'path': full, 'name': Path(full).name, 'b': None if text is None else blob(text)}
        base = next(iter(at.values()))
        rel = key.replace('{app}', 'App')
        parts = rel.split('/')
        # 一覧では「src/main 配下(アプリ本体)」と「それ以外(Gradle設定・SQL・テストなど)」を分けて表示する
        is_main = rel.startswith('src/main/')
        files.append({'key': key, 'dir': '/'.join(parts[2:-1] if is_main else parts[:-1]),
                      'sec': 'main' if is_main else 'other',
                      'role': next((ROLE[x] for x in reversed(parts[:-1]) if x in ROLE), ''),
                      'lang': EXT_LANG.get(Path(base['name']).suffix, ''), 'main': base['name'] == MAIN_FILE,
                      'at': at})
    files.sort(key=lambda f: f['sec'] != 'main')  # src/main 配下を先に

    # 比較: ノートに入れた版どうし(古い → 新しい)のすべての組
    pairs = {}
    for i, va in enumerate(vers):
        for vb in vers[i + 1:]:
            res = {}
            for f in files:
                c = compare(side[va['id']].get(f['key']), side[vb['id']].get(f['key']), va['id'], vb['id'])
                if c:
                    res[f['key']] = c
            pairs[f"{va['id']}|{vb['id']}"] = res
    # ノートから外れた1つ前の版 → 最古の版 の差分は、差分の文字だけ持たせる(質問のときに Claude へ渡す。色は付けない)
    prev = {}
    if before:
        for f in files:
            c = compare(side[before['id']].get(f['key']), side[vers[0]['id']].get(f['key']), before['id'], vers[0]['id'])
            if c:
                prev[f['key']] = {'st': c['st'], 'diff': c['diff']}

    p = ROOT / 'HISTORY.md'
    if p.exists():
        b = blob(p.read_text(encoding='utf-8').replace('\r\n', '\n').rstrip('\n'))
        files.append({'key': 'HISTORY.md', 'dir': '学習メモ', 'sec': 'other', 'role': '進捗・Q&A', 'lang': 'markdown',
                      'main': False, 'doc': True,
                      'at': {v['id']: {'path': 'HISTORY.md', 'name': 'HISTORY.md', 'b': b} for v in vers}})
    meta = [{k: v[k] for k in ('id', 'tag', 'date', 'desc', 'memo', 'dir')} for v in vers]
    return {'versions': meta, 'before': before and {k: before[k] for k in ('id', 'date', 'desc', 'memo')},
            'files': files, 'blobs': blobs, 'pairs': pairs, 'prev': prev}, side


def check(data, side):
    """反映前の確かめ(改修反映ルール.md「差分の取り方」)。問題があれば終了する"""
    ok = True
    base = 'package a;\n\nclass A {\n    int x;\n}'
    d = diff(base, '// 先頭に追加\n' + base, 'a', 'b')
    if d['mb'] != {1: 'add'} or d['ma']:
        print('  NG 1: 先頭に1行追加したのに、その1行以外にも色が付く', d['mb'], d['ma']); ok = False
    d = diff(base, base.replace('\n', '\r\n').replace('    ', '\t'), 'a', 'b')
    if d['mb'] or d['ma']:
        print('  NG 2: 改行コード・インデントだけの違いに色が付く'); ok = False
    vers = data['versions']
    for key, res in data['pairs'].items():
        a, b = key.split('|')
        va, vb = next(v for v in vers if v['id'] == a), next(v for v in vers if v['id'] == b)
        same = [f['key'] for f in data['files'] if not f.get('doc') and f['key'] not in res and a in f['at'] and b in f['at']]
        # 3. 色の付いた行数と git diff --numstat(-w)の比較
        ins = dels = 0
        for r in res.values():
            s = r['stat']
            ins += s.get('add', 0) + s.get('chg', 0)
            dels += s.get('del', 0) + s.get('chgOld', 0)
        gi = gd = 0
        for line in git('diff', '--numstat', '-w', '--ignore-cr-at-eol', '-M', f"{va['tag']}:{va['dir']}",
                        f"{vb['tag']}:{vb['dir']}").splitlines():
            x, y, path = line.split('\t', 2)
            if x == '-' or not (path in ('build.gradle', 'settings.gradle') or path.startswith(('sql/', 'src/'))):
                continue  # 画像と、ノートに載せないファイル(.gitignore など)
            gi += int(x); gd += int(y)
        mark = 'OK' if abs(ins - gi) <= max(2, gi // 20) and abs(dels - gd) <= max(2, gd // 20) else 'ずれあり'
        if mark != 'OK':
            ok = False
        print(f'  {a}→{b}: 変更なし{len(same)}ファイルは色0行 / 色付き 追加側{ins}行・削除側{dels}行、git diff --numstat -w は +{gi} -{gd} … {mark}')
    if not ok:
        sys.exit('確かめで問題が見つかったため、反映を止めました')


def main():
    data, side = collect()
    check(data, side)
    data.update(built=datetime.datetime.now().strftime('%Y/%m/%d %H:%M'), guide=GUIDE)
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = TEMPLATE.read_text(encoding='utf-8').replace('/*__DATA__*/null', js)
    old_size = OUT.stat().st_size if OUT.exists() else 0
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding='utf-8')
    size = OUT.stat().st_size
    ids = [v['id'] for v in data['versions']]
    print(f'{OUT.relative_to(ROOT)}: 版 {", ".join(ids)} / {len(data["files"])}ファイル / 埋め込み{len(data["blobs"])}件 / '
          f'{size // 1024}KB(前回 {old_size // 1024}KB)')
    if old_size and size > old_size * 2:
        print('  !! ノートのサイズが前回の2倍を超えました')
    last = f'{ids[-2]}|{ids[-1]}' if len(ids) > 1 else None
    for f in data['files']:
        r = data['pairs'].get(last, {}).get(f['key'])
        if r:
            s = r['stat']
            print(f"  [{r['st']}] {f['key'].replace('{app}', 'App')}  +{s.get('add', 0)} ~{s.get('chg', 0)} -{s.get('del', 0)}")


if __name__ == '__main__':
    main()
