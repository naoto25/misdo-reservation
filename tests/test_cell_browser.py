"""本物と同じ構造の11月のカレンダーをブラウザで開き、23日の枠を正しく読めるか確かめる（Playwright が必要）"""
import os, sys, tempfile, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, os.path.join(HERE, "fixtures"))
os.environ.update(LINE_USER_ID="u", LINE_CHANNEL_TOKEN="t")
if os.environ.get("CHROMIUM_PATH"):  # 手元のブラウザを使うとき
    from playwright.sync_api._generated import BrowserType
    _launch = BrowserType.launch
    BrowserType.launch = lambda self, **kw: _launch(self, executable_path=os.environ["CHROMIUM_PATH"], **kw)
cc = importlib.import_module("check_cancel")
from make_calendar import calendar

# (10:15枠の表示, 14:00枠の表示) → 14:00枠の期待する判定（10:15枠は常に×で full）
CASES = [
    ("両方×", "times", "times", "full"),
    ("14:00が○", "times", "circle", "open"),
    ("14:00が残1", "times", "rest", "open"),
    ("14:00の×が消えて空欄", "times", "blank", "open"),
    ("14:00がキャンセル待ち", "times", "wait", "full"),
    ("14:00が受付終了", "times", "ended", "full"),
    ("14:00が締切", "times", "closed", "full"),
]
failed = False
for name, v10, v14, expect14 in CASES:
    f = os.path.join(tempfile.mkdtemp(), "cal.html")
    open(f, "w").write(calendar(v10, v14))
    cc.URL = "file://" + f
    cell, _ = cc.fetch()
    got = cc.parse_slots(cell) if cell else None
    ok = got == {"10:15-11:45": "full", "14:00-15:30": expect14}
    failed |= not ok
    print("PASS" if ok else "FAIL", name, "->", got)
sys.exit(1 if failed else 0)
