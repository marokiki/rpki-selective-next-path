# Selective Next Path + Mixed-Tree

> EXPERIMENTAL / NOT FOR PRODUCTION

Selective Next-path RPKI移行を検討するための、決定論的でprotocol-neutralなPython状態機械です。
Current Suiteの危殆化前にNext Trust Anchorと上位経路を準備し、危殆化後に権威的なHosted operatorがHosted CAを生成して移行できるかを合成fixtureで検証します。

実証明書、暗号アルゴリズム、RRDP、rsync、Krill、Routinator、rpki-client、production validatorは実装しません。

## Requirements

- Python 3.11以降
- GNU Makeまたは互換make
- 通常の生成とテストにはネットワークアクセスもsubmoduleも不要

## Run

```sh
make selective-next-path
make selective-next-path-test
make test
```

`make selective-next-path` は次の決定論的な成果物を生成します。

```text
results/selective-next-path/
├── topology.json
├── scenario-results.json
├── cost-model.json
└── report.md
```

JSONが一次成果物であり、`report.md`は同じデータから生成する表示用ビューです。
すべての公開出力に `EXPERIMENTAL / NOT FOR PRODUCTION` を含めます。

## Model

Phase 1は次をモデル化します。

- Current Suiteの `secure`、`compromised`、`retired`
- Next TAの `absent`、`observed`、`accepted`
- TA、RIR/NIR、Hosted、DelegatedのCA role
- prebuilt Next pathとon-demand Hosted CA
- staging、dual publication、semantic comparison、activation、retirement
- scopeごとのmonotonic transition sequenceとanti-rollback
- activation後のNext障害に対するno-fallback

Semantic comparisonは設定されたscopeに従い、正規化したresource set、VRP、ASPA、child delegationを比較します。
DER、URI、SIA、AIA、validityの完全一致は要求しません。

## Repository layout

```text
src/selective_next_path/        状態機械、意味比較、cost model、result I/O
tools/                          fixture生成と参照境界検査
tests/                          T01–T20を含むunit tests
testdata/selective-next-path/   公開可能な合成入力
results/selective-next-path/    決定論的な生成結果
docs/                           研究設計と非目標
prompts/                        後続phaseの作業単位
reference/pqc-rpki-lab/         読み取り専用の任意submodule
```

## RPKI lab reference

`reference/pqc-rpki-lab` は参考実装を固定commitで参照するGit submoduleです。
Phase 1 codeはこのsubmoduleをimportせず、package、build、test discoveryにも含めません。

新規clone時に参照も取得する場合は、次のコマンドを実行します。

```sh
git clone --recurse-submodules REPOSITORY_URL
```

既存cloneで後から取得する場合は、次のコマンドを実行します。

```sh
git submodule update --init
make check-reference
```

submoduleを取得していない場合、`make check-reference` はskipします。
取得済みの場合は、指定commitのdetached HEADかつcleanな状態でなければ失敗します。

## Boundaries

- 秘密鍵、外部checkout、build tree、raw operational input、scratch noteはignored `local/` 以下に置きます。
- 通常targetはネットワークアクセスを行いません。
- CCRは必須要素またはprotocol dependencyではありません。
- Phase 1のcost modelは合成された個数とcoverageであり、byte-size、RRDP、repository、HSM、timingの実測値ではありません。
- 本リポジトリの結果からproduction互換性や標準準拠を主張しません。
