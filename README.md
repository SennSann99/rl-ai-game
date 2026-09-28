# AI Treasure Dash

AIが試行錯誤しながら、宝石集めや城への道順を学ぶ強化学習（Q学習）のデモです。GPUや外部サービスは不要です。

## 起動方法

Python 3.13を推奨します（3.14ではpygameのインストールが失敗する場合があります）。ターミナルで、このREADMEがあるフォルダーを開いて実行してください。

初回（macOS / Linux）：

`python3.13` がない場合は先にインストールしてください。macOSでHomebrewを使う場合は `brew install python@3.13` です。

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python quest_main.py
```

2回目以降：

```bash
source .venv/bin/activate
python quest_main.py
```

Windows（PowerShell）では、初回に `py -3.13 -m venv .venv` で仮想環境を作成し、有効化コマンドを `.venv\Scripts\Activate.ps1` に置き換えてください。

**`.venv/bin/python` が見つからない場合：** 仮想環境が未作成か、別のフォルダーにいます。READMEがあるフォルダーで、初回の手順を上から実行してください。

## ゲームの種類

仮想環境を有効にした状態で、遊びたい版を起動します。設定ファイルは起動前に編集してください。

| 種類 | 起動コマンド | 設定ファイル |
| --- | --- | --- |
| 城への冒険 | `python quest_main.py` | `config_quest.json` |
| 宝石集め | `python main.py` | `config.json` |
| 視界・壁ありの宝石集め | `python advanced_main.py` | `config_advanced.json` |

## 城への冒険の遊び方

1. 開始前に、左上のボタンでモードを選びます。**設定者モード**は全体マップを表示し、敵の有無や報酬などを変更できます。**体験者モード**は探索済みの範囲だけを表示します。
2. **学習を開始**または `Space` を押します。AIは毎回同じ場所から出発し、城を目指します。
3. 学習は200回、各回は最大200ステップです。開始後は環境設定が固定され、表示速度は調整できます。

コインは各回に復活する中間報酬です。AIはコインの位置を直接観測せず、探索で道順を学びます。敵は初期位置の周辺をランダムに移動します。

## 基本操作

画面のボタンでも操作できます。ウィンドウの大きさは変更できます。

| キー | 操作 |
| --- | --- |
| `Space` | 開始・一時停止・再開 |
| `[` / `]` | 速度を下げる・上げる |
| `R` | 学習をリセット |
| `Esc` | 終了 |

学習結果は終了すると失われます。得点にはばらつきがあるため、学習の進み具合はグラフの傾向で確認してください。
