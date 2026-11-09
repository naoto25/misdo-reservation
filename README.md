# misdo-reservation

RESERVA の d_museum（ https://reserva.be/d_museum ）で、11/23 の 10:15 枠・14:00 枠のキャンセルを見張り、空いたら LINE に通知する。

## 仕組み

- 外部の cron サービス（cron-job.org）が5分おきに GitHub API を呼び、ワークフローを起動する。GitHub の定期実行は 2026-11-09 時点でこのリポジトリでは一度も動かなかったため。定期実行の設定も予備として残している。
- スマホ表示でトップページを開き、カレンダーの「23」のマスを探す。
- 枠ごとに「×」があるかを見て、×が消えた瞬間だけ LINE に通知する。
- 前回の結果は `state.json` に保存し、Actions のキャッシュで次の実行に引き継ぐ。
- 11/23 を過ぎたら何もしない。

## 必要な設定

リポジトリの Settings → Secrets and variables → Actions に次の2つを登録する。

| 名前 | 中身 |
|---|---|
| `LINE_CHANNEL_TOKEN` | LINE Messaging API のチャネルアクセストークン |
| `LINE_USER_ID` | 通知を受け取る LINE のユーザー ID |

## 動作確認

Actions タブで `watch-reserva` を選び、Run workflow で手動実行する。LINE に「監視を開始しました（11/23）」が届き、両方の枠が「×」なら正常。

手動実行で「debug」にチェックしたときだけ、23日のマスの HTML をログに出し、画面のスクリーンショットを成果物（screenshot）として保存する。

## 外部 cron からの起動

cron-job.org に、5分おきに次のリクエストを送るジョブを登録している。トークンは misdo-reservation の Actions だけに「Read and write」権限を持つ fine-grained personal access token。

```
POST https://api.github.com/repos/naoto25/misdo-reservation/actions/workflows/watch.yml/dispatches
Authorization: Bearer <トークン>
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json

{"ref":"main"}
```

成功すると GitHub は 204 No Content を返す。

テストは次のコマンドで実行できる（LINE には送らない）。2つ目は Playwright のブラウザが必要。

```
python tests/test_flow.py          # 通知の流れ
python tests/test_cell_browser.py  # 本物と同じ構造のカレンダーで×を読めるか
```

## 予約サイトの×の描き方

×は文字ではなく、`<i class="icon-times">` というアイコンで描かれている。`check_cancel.py` はアイコンのクラス名を「×」に置き換えてから判定する。

×が消えても、次の表示に変わった枠は空きとみなさない。サイトの文言一覧にあり、誤報の原因になるため。

- キャンセル待ち（「待」、または `icon_wait.png` の画像）
- 受付終了（「終了」）
- 締切（「締切」）
