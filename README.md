# Codex作業用ディレクトリ: Selective Next Path + Mixed-Tree

このディレクトリは、`marokiki/pqc-rpki-lab` に次の研究実装を追加するための作業仕様です。

- Next Trust AnchorをCurrent Suite危殆化前に受理する
- Next TAからRIR/NIR・主要Delegated CAまでを事前構築する
- Hosted CAは事前生成せず、Next親CAから必要時に生成する
- RFC 6489型stagingとMixed-TreeのCA単位移行を用いる
- Current Suite危殆化後はCurrent署名で新しいNext鍵を導入しない
- activation後はCurrentへfallbackしない
- CCRを必須要素にしない

## 使用方法

1. このディレクトリをリポジトリ内の `codex/selective-next-path/` に置く。
2. Codexをリポジトリルートで起動する。
3. 最初に `prompts/00-master.md` を渡し、実装計画を確認する。
4. その後、`prompts/01-model.md` から順番に実行する。
5. 各phaseでテストとmachine-readable resultsを確認してから次へ進む。

一度に全phaseを実装させず、各promptを独立したIssue相当の作業単位として扱う。

## 推奨する最初の作業

最初は実暗号やKrill改修へ進まず、Phase 1の純Pythonモデルだけを実装する。

```sh
make selective-next-path
make selective-next-path-test
```

期待する主な出力:

```text
results/selective-next-path/
├── topology.json
├── scenario-results.json
├── cost-model.json
└── report.md
```

## ファイル構成

- `AGENTS.md`: Codexへ継続的に与えるリポジトリ規則
- `TASKS.md`: 全体バックログ
- `docs/`: 設計、脅威モデル、状態機械、テスト、出力仕様
- `prompts/`: phaseごとのCodex prompt
- `reference/`: 人間向け研究設計資料

## 実装上の境界

この研究コードは実験用であり、production RPKI validator、RRDP、rsync、暗号アルゴリズム自体を新規実装しない。既存のOpenSSL provider、Krill、Routinator、rpki-client等を利用する。

公開可能なコード・fixture・集計結果だけをcommitする。秘密鍵、外部checkout、build tree、raw logs、AI作業メモは既存方針に従い `local/` 以下へ置く。
