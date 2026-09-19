"""定期収集後、成功・失敗いずれも編集画面を更新する。"""

import subprocess
import sys

from web.collect import ROOT
from web.editor import review


def main():
    result = subprocess.run([sys.executable, "-m", "web.collect"], cwd=ROOT, check=False)
    print(review(ROOT / ".news-cache"))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
