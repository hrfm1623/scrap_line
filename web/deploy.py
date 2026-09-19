"""確認済みの本番設定でテスト・ビルド後、Cloudflare Pagesへ公開する。"""

import os
import re
import subprocess
import sys

from web.collect import ROOT


def main():
    for key in ("SITE_URL", "PUBLIC_OPERATOR", "PUBLIC_CONTACT_URL", "CLOUDFLARE_PAGES_PROJECT", "PRODUCTION_BRANCH"):
        if not os.getenv(key, "").strip():
            raise SystemExit(f"未設定: {key}")
    project = os.environ["CLOUDFLARE_PAGES_PROJECT"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,57}", project):
        raise SystemExit("Cloudflare Pagesプロジェクト名の形式が不正です")
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if branch != os.environ["PRODUCTION_BRANCH"]:
        raise SystemExit("本番ブランチではありません")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise SystemExit("公開履歴を残すため、変更を確認してコミットしてから実行してください")
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "-m", "web.build", "--production"],
        ["wrangler", "pages", "deploy", "dist", "--project-name", project, "--branch", branch],
        [sys.executable, "-m", "web.verify_live", os.environ["SITE_URL"]],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
