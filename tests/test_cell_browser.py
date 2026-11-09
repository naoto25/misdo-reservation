"""本物と同じ構造のカレンダーをブラウザで開き、23日の枠の×を読めるか確かめる（Playwright が必要）"""
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

for open14, expect in [(False, {"10:15-11:45": "full", "14:00-15:30": "full"}),
                       (True, {"10:15-11:45": "full", "14:00-15:30": "open"})]:
    f = os.path.join(tempfile.mkdtemp(), "cal.html")
    open(f, "w").write(calendar(open14))
    cc.URL = "file://" + f
    cell, _ = cc.fetch()
    got = cc.parse_slots(cell) if cell else None
    print(("PASS" if got == expect else "FAIL"), "14:00が空き" if open14 else "両方×", "->", got)
    if got != expect:
        sys.exit(1)
print("all passed")
