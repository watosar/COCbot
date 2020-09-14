# CoC支援 Discord-Bot 
Discord上でのCoCセッション(6版準拠)を補助するためのBotツールです。


## 機能概要  

- ダイスロール
- webキャラクターシートを読み込んで成否判定
   - 対応済みサイト
       - [TRPGキャラシート アーカイブス](https://chara.revinx.net)
       - [キャラクター保管所](https://charasheet.vampire-blood.net)
- キャッシュされた値への一時的補正
- ニックネームでのHP/SAN表示


## 反応コマンド一覧  

※プレフィックスなしで動作します。  
以下`<...>`は適当な文字列を指します 
 
- `chara`  : キャラクターのステータス設定用のダイス  
- `set <URL>`  ：　キャラクターシートのデータのロード  
- `$<ステータス/技能名>`  : ステータス/技能値表示  
- `<式>`  : \<n\>d\<m\>形式のダイス式を含む場合について計算を行います。
- `<式>？` :  ？以前の式について`>=1d100`をつけて成否判定を行います。  
- `<式>？？` :  シークレット成否判定用のコマンドです。結果がコマンド実行者のDMに届きます  
- `$<ステータス/技能名> [-+]?= <式>`  : 右辺の式の計算結果で一時補正を保存します

## コマンドについて補足
- アルファベットの大/小文字の区別はされず、+-？$()の全角半角の区別もされません
- 式には`$<>`表記で技能値を埋め込むことが可能です。
- 式では`->`を演算子として対抗成功率計算が可能です。`A->B`は`50+A*5-B*5`と可変です。

## Requirements
- Python 3.6.9
