# セキュリティチェックの実装詳細

## 実行とマージ判定

- GitHub.comの公開リポジトリを対象とする。GitHub-hostedのLinuxランナーで `main`、`develop` 宛てのPRを検査する。両ブランチのpushと既定ブランチの定期実行でも検査する。
- 6ツールを並行で実行する。6ジョブすべての結果が `success` のときだけ `security-gate` が成功する。失敗、キャンセル、スキップは通過扱いにしない。
- PRではGitHubが作るマージ候補を検査する。GitleaksはPRのbase/head SHAからコミット範囲を取得する。
- CodeQLのSARIFをCI内でも評価し、PR差分外を含む、解析結果中の中以上のセキュリティ指摘を止める。GitHub RulesetのCode scanning判定も併用する。
- ZAPはジョブ内だけのDjangoに対するパッシブ検査。実運用の環境や顧客データは使用しない。

## 重要度の扱い

| ツール | 警告 | マージ停止 |
| --- | --- | --- |
| Semgrep | Low相当（旧形式のINFOを含む） | Medium以上（旧形式のWARNINGとERRORを含む） |
| Dependency-Check | CVSS 4.0未満の検出はレポートで確認 | CVSS 4.0以上。スコア未確定で重要度が分からない検出は要確認として停止 |
| ZAP | Lowはレポートで確認 | Medium／High |
| Gitleaks | CLIには共通の重要度がない | 検出されたすべてのシークレット |
| Trivy | LOWとUNKNOWNは警告として記録 | MEDIUM／HIGH／CRITICAL |
| CodeQL | `security-severity` が4.0未満 | `security-severity` が4.0以上、またはセキュリティ指摘の重要度が欠落 |

ジョブのサマリーやレポートから、ツール名・対象・重要度を確認する。Gitleaksはマスクしたログのみを残す。CodeQLの判定対象はセキュリティクエリの結果。

## GitHub Ruleset

`.github/security/ruleset.json` をリポジトリの **Settings → Rulesets** からインポートするか、リポジトリのRulesets APIで作成する。対象は `refs/heads/main` と `refs/heads/develop`。適用状態は `active` で、通常のバイパスは設定しない。

1. 両ブランチを作成し、少なくとも一度CIを実行する。
2. PR経由の変更、`security-gate` の成功、最新のベースブランチでの検査を必須にする。
3. Code scanningの必須ツールに `CodeQL` を登録し、Security alertsを **Medium or higher** に設定する。
4. CODEOWNERS対象の設定ファイルを変更する場合は、作者とは別のコードオーナーがレビューする。複数の担当者がいる場合は、担当チームをCODEOWNERSに登録する。

## スキャナーとレポート

- **Semgrep** は固定した上流のPython・Djangoセキュリティルールを使用する。JSONでスキャン対象と結果を確認する。ローカルルールが必要な場合は `.github/security/semgrep/` に置く。
- **Dependency-Check** はバージョン固定済みの `requirements.txt` に実験的なPipアナライザーを適用する。公開NVDミラーの更新時刻を確認し、既存のNVD DBキャッシュは復元後に更新する。スキャン対象の依存が検出されていることも確認する。
- **ZAP** はDjangoを専用のDockerネットワークに起動し、HTTP 200を確認してから公開ページを巡回する。巡回とパッシブ検査の完了を確認し、HTMLとJSONのレポートを保存する。
- **Gitleaks** はCLIでコミットを走査する。定期実行・pushではリポジトリの履歴を走査する。検出された実際の資格情報は失効・ローテーションする。
- **Trivy** はロック済み依存／IaCと、CIでビルドした同じDockerfileのアプリイメージを検査する。未修正の既知脆弱性も重要度に従って判定する。イメージをビルドするときにAlpineのパッケージを更新し、インストール完了後は実行に不要なpipと同梱のブートストラップ用wheelsを削除する。
- **CodeQL** はAdvanced setupでPythonを解析する。`security-extended` クエリを使用し、SARIFの出力先はジョブ専用の一時ディレクトリにする。結果はGitHub Code scanningにもアップロードする。

PRのワークフローは `pull_request_target` を使用せず、NVD APIキー、GitleaksのActionライセンス、外部サービスのトークンを要求しない。リポジトリに書き込める権限はスキャンに渡さず、CodeQL結果の送信に必要な権限だけ該当ジョブに付与する。

## 検証

1. ローカルで `python -m unittest discover -s tests` と `python manage.py check` を実行する。
2. `develop` 宛ての検証用PRで、無害なSemgrepのテストルールとマーカーにより、Lowの警告が出てもゲートが通ることを確認する。
3. 同じマーカーをMediumとして扱うルールに変更し、Semgrepとゲートが失敗してマージが停止することを確認する。
4. 検証用マーカーとルールを除去して再実行し、`develop` と `main` 宛ての正常なPRで6ツールとゲートが成功することを確認する。

## 関連資料

- [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [Code scanningのマージ保護](https://docs.github.com/en/code-security/concepts/code-scanning/merge-protection)
- [Semgrep CLI](https://docs.semgrep.dev/cli-reference)
- [Dependency-Check CLI](https://dependency-check.github.io/DependencyCheck/dependency-check-cli/arguments.html)
- [ZAP Automation Framework](https://www.zaproxy.org/docs/desktop/addons/automation-framework/)
- [Gitleaks CLI](https://github.com/gitleaks/gitleaks)
- [TrivyのPython対応](https://trivy.dev/docs/latest/guide/coverage/language/python/)
