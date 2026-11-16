"""各アプリのソースコードを1枚の HTML にまとめ、スマホ(claude.ai の Artifact)で読めるようにする。

使い方(プロジェクト直下で):  py tools\\build_mobile.py
出力:  公開用\\ソースコード.html

build.gradle がある直下のフォルダをアプリとみなし、src・sql・Gradle 設定を取り込む。
DB のパスワードを含む application.properties は取り込まない(代わりに .example を載せる)。
ソースを直したら、これを実行して Artifact を同じ URL に再公開する(URL は CLAUDE.md)。
"""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / 'mobile_template.html'
OUT = ROOT / '公開用' / 'ソースコード.html'

EXT_LANG = {'.java': 'java', '.html': 'xml', '.css': 'css', '.js': 'javascript', '.sql': 'sql',
            '.gradle': 'groovy', '.properties': 'ini', '.example': 'ini', '.md': 'markdown'}
SKIP_NAMES = {'application.properties'}
# パッケージ名(フォルダ名)から付ける役割の表示
ROLE = {'controller': 'Controller', 'service': 'Service', 'repository': 'Repository', 'dao': 'DAO',
        'entity': 'Entity', 'form': 'Form', 'common': '共通処理', 'templates': '画面(Thymeleaf)',
        'css': 'CSS', 'sql': 'SQL', 'test': 'テスト'}
MAIN_FILE = 'TodoListController.java'  # 最初に開くファイル

# 質問するときに Claude へ毎回渡す前提(CLAUDE.md の学習方針と同じ内容)
GUIDE = """あなたは Spring Boot を学習中の人の先生です。参考書のサンプルコード(下に全文あり)を読みながら、通勤中にスマホで質問しています。日本語で答えてください。

# 学習者
- Java Silver 取得済み(実務経験は浅い)。本番案件は Java(Spring Boot)+ TypeScript
- 前シーズンで Controller / Repository / Thymeleaf / JPA の基本、検索・ページングまで写経済み

# 答え方
- コードを丸ごと書き直して見せるのではなく、まず「なぜそうなるか」を説明する
- 抽象的な仕組み(DI、プロキシ、セッションなど)は身近なたとえ話で噛み砕いてから、コードの該当行に戻って説明する
- コードに触れるときは「TodoListController.java の 40行目」のようにファイル名と行番号で示す
- 1度に新しい概念を詰め込みすぎない。スマホで読むので、見出しと短い段落・箇条書きで簡潔に
- 下に載っているコードに無いことを推測で断定しない。分からないことは分からないと言う"""


def collect():
    files = []
    for app in sorted(p for p in ROOT.iterdir() if (p / 'build.gradle').exists() and p.name != 'sampleSource'):
        paths = [app / 'build.gradle', app / 'settings.gradle']
        paths += sorted((app / 'sql').glob('*')) if (app / 'sql').exists() else []
        paths += sorted(p for p in (app / 'src').rglob('*') if p.is_file())
        for p in paths:
            if not p.exists() or p.name in SKIP_NAMES:
                continue
            rel = p.relative_to(ROOT).as_posix()
            # Java のパッケージは長いので一覧の見出しでは src/main/java/com/example/... を縮める
            d = p.parent.relative_to(ROOT).as_posix()
            parts = rel.split('/')
            role = next((ROLE[x] for x in reversed(parts[:-1]) if x in ROLE), '')
            lang = EXT_LANG.get(p.suffix, '')
            files.append({'path': rel, 'dir': d, 'name': p.name, 'role': role, 'lang': lang,
                          'text': p.read_text(encoding='utf-8').replace('\r\n', '\n').rstrip('\n'),
                          'main': p.name == MAIN_FILE,
                          # 質問時に「他のファイル」として渡すもの(Gradle の生成物などは無いので全部渡す)
                          'ctx': True})
    for name in ('HISTORY.md',):
        p = ROOT / name
        if p.exists():
            files.append({'path': name, 'dir': '学習メモ', 'name': name, 'role': '進捗・Q&A', 'lang': 'markdown',
                          'text': p.read_text(encoding='utf-8').replace('\r\n', '\n').rstrip('\n'),
                          'main': False, 'ctx': True})
    return files


def main():
    files = collect()
    data = {'built': datetime.datetime.now().strftime('%Y/%m/%d %H:%M'), 'guide': GUIDE, 'files': files}
    js = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    html = TEMPLATE.read_text(encoding='utf-8').replace('/*__DATA__*/null', js)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding='utf-8')
    print(f'{OUT.relative_to(ROOT)}: {len(files)}ファイル, {len(html) // 1024}KB')


if __name__ == '__main__':
    main()
