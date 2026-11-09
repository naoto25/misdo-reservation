"""本物の d_museum のトップページ（2026-11-09 時点のHTML）と同じ構造の、11月のカレンダーを作る。

1〜9日は過去日、16・24・30日は枠なし、それ以外の日は 10:15 と 14:00 の2枠で、すべて×（満席）。
23日の各枠の表示だけを、引数で差し替えられる。
"""

VACANCY = {
    "times": '<i class="icon-times"></i>',                               # 満席（本物）
    "circle": '<i class="icon-circle"></i>',                             # 空き（○のアイコン）
    "rest": "<span>残1</span>",                                          # 空き（残数の表示）
    "blank": "",                                                         # 空き（何も出ない）
    "wait": '<img src="/reserva/images/icon_wait.png?v=v2026-11-09-01" alt="">',  # キャンセル待ち
    "ended": "<span>終了</span>",                                        # 受付終了
    "closed": "<span>締切</span>",                                       # 締切
}
NOT_OPEN = {"times", "wait", "ended", "closed"}


def unit(start: str, end: str, vacancy: str) -> str:
    mod = " cal-schedule__grid__info--unavailable" if vacancy in NOT_OPEN else ""
    return f'''
      <div class="cal-schedule__grid__unit">
        <div class="cal-schedule__grid__info{mod}">
          <div class="cal-schedule__grid__info__color"></div>
          <div class="cal-schedule__grid__info__time">
            <span>{start}</span>-<span>{end}</span>
          </div>
          <div class="cal-schedule__grid__info__menu">手づくり体験予約...</div>
          <div class="cal-schedule__grid__info__vacancy">{VACANCY[vacancy]}</div>
          <div class="cal-schedule__grid__info__status"></div>
        </div>
      </div>'''


def calendar(v10_23: str = "times", v14_23: str = "times") -> str:
    rows, row = [], []
    for d in range(1, 31):
        if d <= 9:
            row.append(f'<td class="is-past"><span>{d}</span></td>')
        elif d in (16, 24, 30):
            row.append(f'<td class=""><span>{d}</span></td>')
        else:
            a, b = (v10_23, v14_23) if d == 23 else ("times", "times")
            row.append(f'<td class=""><span>{d}</span>'
                       + unit("10:15", "11:45", a) + unit("14:00", "15:30", b) + "</td>")
        if len(row) == 7:
            rows.append(row); row = []
    rows.append(row + ["<td></td>"] * (7 - len(row)))
    body = "".join("<tr>" + "".join(r) + "</tr>" for r in rows)
    table = f'<table class="cal-schedule__grid__body"><tbody>{body}</tbody></table>'
    # 本物にある紛らわしい要素（お知らせの日付、閉じるボタンの icon-times-circle）も入れておく
    extra = ('<div class="notice">次回のエントリーは11月16日14時～11月18日24時（3日間）です'
             '<time>2026年11月08日</time></div><span class="modal__close"><i class="icon-times-circle"></i></span>')
    return f'''<html><head><style>.icon-times::before {{ content: "\\2715"; }}
.icon-circle::before {{ content: "\\25CB"; }}</style></head>
<body>{extra}<div class="cal__title">2026年11月</div><div id="cal"></div><script>
setTimeout(() => {{ document.getElementById("cal").innerHTML = {table!r}; }}, 1000);
</script></body></html>'''
