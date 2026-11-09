"""check_cancel.py の通知の流れを、偽のページと偽のLINE送信で確かめる"""
import sys, os, json, importlib, tempfile
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.update(LINE_USER_ID="u", LINE_CHANNEL_TOKEN="t")
os.chdir(tempfile.mkdtemp())
cc = importlib.import_module("check_cancel")
sent = []; fail = {"on": False}
def fake_push(t):
    if fail["on"]: raise RuntimeError("LINE down")
    sent.append(t)
cc.push_line = fake_push
WHOLE = "URL: x\n" + "カレンダー " * 20
def page(c10, c14, sep="-"):
    return f"23\n10:15{sep}11:45\n{c10}\n14:00{sep}15:30\n{c14}"
def run(cell, whole=WHOLE):
    cc.fetch = lambda: (cell, whole); sent.clear()
    try: cc.main()
    except Exception as e: sent.append(f"EXC:{e}")
    return list(sent)
def check(name, got, expect):
    ok = expect(got); print(("PASS" if ok else "FAIL"), name, "->", [g[:40].replace("\n"," | ") for g in got])
    if not ok: sys.exit(1)

check("初回: 両方×で開始メッセージ", run(page("×","×")), lambda g: len(g)==1 and "監視を開始" in g[0] and "空きあり" not in g[0])
check("2回目: 変化なし", run(page("×","×")), lambda g: g==[])
check("14:00の×が消える", run(page("×","")), lambda g: len(g)==1 and "14:00-15:30" in g[0] and "10:15" not in g[0].split("読み取った")[0])
check("空きが続く: 再通知なし", run(page("×","")), lambda g: g==[])
check("また×に戻る", run(page("×","×")), lambda g: g==[])
check("再び○: 再通知", run(page("×","○")), lambda g: len(g)==1 and "14:00" in g[0])
check("区切りが〜でも読める", run(page("","×", sep="〜")), lambda g: len(g)==1 and "10:15-11:45" in g[0])
fail["on"]=True; run(page("×","×")); 
check("LINE失敗時", run(page("","×")), lambda g: len(g)==1 and g[0].startswith("EXC"))
fail["on"]=False
check("LINE失敗の次の回で再送", run(page("","×")), lambda g: len(g)==1 and "10:15" in g[0])
check("ブロック: 警告1回", run(page("×","×"), whole="Forbidden"), lambda g: len(g)==1 and "ブロック" in g[0])
check("ブロック継続: 再警告なし", run(page("×","×"), whole="Forbidden"), lambda g: g==[])
check("ブロック中に状態が消えない", run(page("","×")), lambda g: g==[])  # 10:15は前回から空きのまま
check("時間枠が読めない: 警告1回", run("23\n満員御礼"), lambda g: len(g)==1 and "時間枠を読み取れません" in g[0])
check("時間枠が読めない継続: 再警告なし", run("23\n満員御礼"), lambda g: g==[])
json.dump({"slots": {"10:15-11:45": False, "14:00-15:30": False}}, open("state.json","w"))
check("旧形式の状態: 開始メッセージのみ", run(page("×","×")), lambda g: len(g)==1 and "監視を開始" in g[0])
cc.datetime = type("D", (), {"now": staticmethod(lambda tz=None: datetime(2026,11,24,0,1,tzinfo=tz))})
check("11/24以降は何もしない", run(page("","")), lambda g: g==[])
print("all passed")
