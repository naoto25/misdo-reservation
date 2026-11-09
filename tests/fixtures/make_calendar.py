"""本物の d_museum のマス（2026-11-09 の Actions ログに出たHTML）を元に、テスト用カレンダーを作る"""

def unit(start: str, end: str, full: bool) -> str:
    mod = " cal-schedule__grid__info--unavailable" if full else ""
    vacancy = '<i class="icon-times"></i>' if full else '<i class="icon-circle"></i>'
    return f'''
      <div class="cal-schedule__grid__unit">
        <div class="cal-schedule__grid__info{mod}">
          <div class="cal-schedule__grid__info__color"></div>
          <div class="cal-schedule__grid__info__time">
            <span>{start}</span>-<span>{end}</span>
          </div>
          <div class="cal-schedule__grid__info__menu">手づくり体験予約...</div>
          <div class="cal-schedule__grid__info__vacancy">{vacancy}</div>
          <div class="cal-schedule__grid__info__status"></div>
        </div>
      </div>'''


def calendar(open_14_on_23: bool) -> str:
    cells = ""
    for d in (22, 23, 24):
        open14 = open_14_on_23 and d == 23
        cells += (f'<td class=""><span>{d}</span>'
                  + unit("10:15", "11:45", True) + unit("14:00", "15:30", not open14) + "</td>")
    # 空き状況は後から描画されるので、本物と同じく遅れて差し込む
    return f'''<html><head><style>i[class^="icon-"]::before {{ font-family: sans-serif; }}
.icon-times::before {{ content: "\\2715"; }} .icon-circle::before {{ content: "\\25CB"; }}</style></head>
<body><table><tr id="row"></tr></table><script>
setTimeout(() => {{ document.getElementById("row").innerHTML = {cells!r}; }}, 1000);
</script></body></html>'''
