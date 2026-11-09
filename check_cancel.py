"""RESERVA d_museum 11/23（10:15枠・14:00枠）キャンセル監視 → LINE通知"""
import hashlib, json, os, re, difflib
from datetime import datetime, timedelta, timezone
from pathlib import Path
import urllib.request

URL = "https://reserva.be/d_museum"
TARGET_DAY = "23"                      # 11月のカレンダー上の日付
TARGET_DATE = "2026-11-23"
FULL_MARKS = ("×", "✕", "✖", "満")     # この文字がある枠は満席、ない枠は空きとみなす
LOADED_MARKS = ("×", "✕", "✖", "満", "○", "◯", "〇", "⚪", "△")  # 空き状況の読み込み完了の目安
STATE = Path("state.json")
JST = timezone(timedelta(hours=9))

# 日付の数字「23」から親要素をたどり、時間枠を含み、かつ他の日付を含まない最小の要素＝その日のマス
FIND_CELL_JS = """
(day) => {
  const heads = [...document.querySelectorAll('body *')]
    .filter(e => e.children.length === 0 && e.textContent.trim() === day);
  for (const h of heads) {
    let el = h;
    while (el && el !== document.body) {
      const t = el.innerText || '';
      if (/\\d{1,2}:\\d{2}/.test(t)) {
        const days = t.split('\\n').map(s => s.trim()).filter(s => /^\\d{1,2}$/.test(s));
        if (days.length === 1) return t;
        break;
      }
      el = el.parentElement;
    }
  }
  return null;
}
"""


def push_line(text: str) -> None:
    body = json.dumps({"to": os.environ["LINE_USER_ID"],
                       "messages": [{"type": "text", "text": text[:4900]}]}).encode()
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/push", data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {os.environ['LINE_CHANNEL_TOKEN']}"})
    urllib.request.urlopen(req, timeout=20).read()


def fetch() -> tuple[str | None, str]:
    """(11/23のマスのテキスト or None, ページ全体のテキスト)"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(**p.devices["iPhone 13"], locale="ja-JP")  # スマホ表示に合わせる
        page = ctx.new_page()
        page.goto(URL, wait_until="load", timeout=60000)
        try:  # 空き状況は後から読み込まれるので、○や×が出るまで待つ（読み込み途中の誤報を防ぐ）
            page.wait_for_function(
                "(m) => m.some(k => document.body.innerText.includes(k))",
                arg=list(LOADED_MARKS), timeout=20000)
        except Exception:
            pass  # 出なくても続行する
        page.wait_for_timeout(1000)
        cell = page.evaluate(FIND_CELL_JS, TARGET_DAY)
        whole = f"URL: {page.url}\n" + page.inner_text("body")
        b.close()
    return cell, whole


def parse_slots(cell: str) -> dict[str, str]:
    """{'10:15-11:45': 'open'(×なし) / 'full'(×あり)}"""
    text = re.sub(r"\s+", " ", cell)
    times = list(re.finditer(r"(\d{1,2}:\d{2})\s*[-~〜～–—]\s*(\d{1,2}:\d{2})", text))
    slots = {}
    for i, m in enumerate(times):
        chunk = text[m.end(): times[i + 1].start() if i + 1 < len(times) else len(text)]
        full = any(k in chunk for k in FULL_MARKS)
        slots[f"{m.group(1)}-{m.group(2)}"] = "full" if full else "open"
    return slots


def normalize(prev_slots: dict) -> dict[str, str]:
    """旧形式（True/False）の状態ファイルも読めるようにする"""
    return {s: ("open" if v is True else "full" if v is False else v)
            for s, v in prev_slots.items()}


def newly_open(prev: dict, now: dict) -> list[str]:
    """前回は×（または初見）→今回×なし になった枠"""
    return [s for s, v in now.items() if v == "open" and prev.get(s) != "open"]


def looks_blocked(text: str) -> bool:
    return len(text) < 50 or any(w in text for w in
                                 ("Access Denied", "Forbidden", "captcha", "アクセスが拒否"))


LABEL = {"open": "空きあり（×なし）", "full": "×"}


def warn_once(state: dict, key: str, text: str) -> None:
    """同じ警告は1回だけ送る（正常に読めたら state['warned'] はリセットされる）"""
    if key not in state.setdefault("warned", []):
        push_line(text)
        state["warned"].append(key)


def main() -> None:
    if datetime.now(JST).date().isoformat() > TARGET_DATE:
        print("対象日を過ぎたので終了"); return
    prev = json.loads(STATE.read_text()) if STATE.exists() else {}
    state = {"started": prev.get("started", False), "warned": prev.get("warned", []),
             "slots": prev.get("slots", {})}
    try:
        run(prev, state)
    finally:
        STATE.write_text(json.dumps(state, ensure_ascii=False))


def run(prev: dict, state: dict) -> None:
    cell, whole = fetch()
    if looks_blocked(whole):
        print("ブロックされた可能性あり:\n", whole[:300])
        warn_once(state, "blocked", "⚠️ 予約サイトを読めませんでした（ブロックの可能性）。"
                  "読めない間は空きを検知できません。\n" + whole[:300])
        return

    if cell is None:
        # マスが特定できない場合はページ全体の差分で代用
        print("11/23のマスが見つからない。全体差分で判定")
        h = hashlib.sha256(whole.encode()).hexdigest()
        if not state["started"]:
            push_line("⚠️監視開始。ただし11/23のマスを特定できず、ページ全体の変化で通知します\n"
                      + whole[:3000])
            state["started"] = True
        elif prev.get("hash") and prev["hash"] != h:
            diff = [l for l in difflib.unified_diff(prev.get("whole", "").splitlines(),
                                                    whole.splitlines(), lineterm="", n=0)
                    if l[:1] in "+-" and l[:3] not in ("+++", "---")]
            push_line("👀 予約カレンダーに変化あり（11/23を確認！）\n"
                      + "\n".join(diff[:15]) + f"\n\n{URL}")
        state.update(hash=h, whole=whole)
        return

    slots = parse_slots(cell)
    status = "\n".join(f"{s}: {LABEL[v]}" for s, v in slots.items())
    print(status or cell)
    if not state["started"]:
        push_line("監視を開始しました（11/23）\n" + (status or "枠が読み取れません\n" + cell)
                  + "\n\n↑画面の表示と合っているか確認してください")
        state["started"] = True
    elif not slots:
        warn_once(state, "no_slots", "⚠️ 11/23のマスはあるのに時間枠を読み取れません\n" + cell[:500])
    else:
        state["warned"] = []  # 正常に読めたので警告をリセット

    opened = newly_open(normalize(prev.get("slots", {})), slots)
    if prev and opened:
        push_line("🎉 11/23 キャンセル空きが出ました！\n" + "\n".join(opened)
                  + f"\n\n読み取った内容:\n{cell[:300]}\n\n今すぐ予約👇\n{URL}")
    if slots:  # 読めなかった回で前回の状態を消さない
        state["slots"] = slots


if __name__ == "__main__":
    main()
