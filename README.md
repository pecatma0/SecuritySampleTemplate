# Django セキュリティチェックのサンプル

`main` と `develop` 宛てのプルリクエストで、Djangoアプリを6種類のスキャナーで検査するGitHub Actionsのサンプルです。

| 検査 | ツール |
| --- | --- |
| Python・Djangoのコード | Semgrep、GitHub CodeQL |
| 依存ライブラリ・コンテナ・IaC | OWASP Dependency-Check、Trivy |
| 起動中のDjangoのHTTP通信 | ZAP（パッシブ検査） |
| PRに含まれるコミットのシークレット | Gitleaks |

**Lowは警告、中以上はマージ停止**です。Gitleaksのシークレット検出はすべてブロックします。スキャン未実行や実行エラーもマージを止めます。

PRの **Checks → Security checks** でツール別の結果を確認できます。最終判定は `security-gate` です。CodeQLの指摘は **Security → Code scanning** でも確認できます。

## サンプルアプリをローカルで起動

Python 3.11以上を使用します。

```bash
python -m pip install -r requirements.txt
python manage.py runserver
```

ブラウザーで `http://127.0.0.1:8000/` を開きます。`/healthz/` は正常時にHTTP 200を返します。

[実装詳細・GitHub Rulesetの設定・検証方法](docs/security-checks.md)
