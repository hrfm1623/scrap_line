"""現在のユーザーのsystemdに8時間ごとの候補収集を登録する。"""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    if args.install:
        check = subprocess.run(["systemctl", "--user", "show-environment"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if check.returncode:
            raise SystemExit("ユーザーsystemdに接続できません。通常のログイン端末から再実行してください。")
    root = str(ROOT).replace("%", "%%").replace('"', '\\"')
    service = f'''[Unit]
Description=Hare Dayori candidate collection
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory={root}
ExecStart=/usr/bin/python3 -m web.refresh
TimeoutStartSec=180
UMask=0077
'''
    timer = '''[Unit]
Description=Hare Dayori collection every eight hours

[Timer]
OnCalendar=*-*-* 00,08,16:17:00
RandomizedDelaySec=120
Persistent=true
Unit=hare-dayori-collect.service

[Install]
WantedBy=timers.target
'''
    directory = Path.home() / ".config/systemd/user" if args.install else ROOT / "build/systemd"
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in (("service", service), ("timer", timer)):
        path = directory / f"hare-dayori-collect.{name}"
        if args.install and path.exists() and path.read_text() != content:
            raise SystemExit(f"既存の異なる設定を検出しました。上書きせず中止します: {path}")
    for name, content in (("service", service), ("timer", timer)):
        (directory / f"hare-dayori-collect.{name}").write_text(content)
    if args.install:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "--now", "hare-dayori-collect.timer"], check=True)
    print(directory)


if __name__ == "__main__":
    main()
