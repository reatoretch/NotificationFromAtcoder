# NotificationFromAtcoder
Atcoderの通知をgoogleカレンダーに自動登録します

# Usage
[参考サイト](https://developers.google.com/calendar/quickstart/python)  

上記のサイトを参考に`credential.json`をダウンロードし、同一フォルダ内に配置します。

```bash
python notification.py
```
で予定されているコンテストがgoogleカレンダーに登録されます。 

すでに公式のサンプルなどを実行して`token.pickle`が生成されている場合は削除してから実行して下さい。

同じ名前の予定がある場合は更新しないので適宜プログラムを修正してください。