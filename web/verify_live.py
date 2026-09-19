"""本番公開後のクロール設定と404を確認する。"""

import argparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from web.content import https_url


def verify(origin):
    origin = https_url(origin).rstrip("/")
    checks = []
    for path in ("/", "/robots.txt", "/sitemap.xml", "/hare-dayori-not-found-check"):
        try:
            with urlopen(Request(origin + path, headers={"User-Agent": "HareDayoriSiteCheck/1.0"}), timeout=15) as response:
                status, headers = response.status, response.headers
                text = response.read(2_000_000).decode("utf-8")
        except HTTPError as error:
            status, headers, text = error.code, error.headers, ""
        if path.endswith("not-found-check"):
            checks.append(("存在しないURLが404", status == 404))
            continue
        checks.append((path + " HTTP 200", status == 200))
        checks.append((path + " X-Robots-Tagにnoindexなし", "noindex" not in headers.get("X-Robots-Tag", "").lower()))
        if path == "/":
            checks.append(("本番canonical", f'href="{origin}/"' in text))
            checks.append(("HTMLにnoindexなし", "noindex" not in text.lower()))
        elif path == "/robots.txt":
            checks.append(("robotsのContent-Type", "text/plain" in headers.get("Content-Type", "")))
            checks.append(("本番サイトマップ指定", f"Sitemap: {origin}/sitemap.xml" in text))
        else:
            checks.append(("サイトマップの本番URL", f"<loc>{origin}/</loc>" in text))
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    args = parser.parse_args()
    checks = verify(args.url)
    for label, result in checks:
        print(f"{'OK' if result else 'NG'} {label}")
    raise SystemExit(0 if all(result for _, result in checks) else 1)


if __name__ == "__main__":
    main()
