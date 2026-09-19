import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from web.collect import ROOT, collect, fetch_feed
from web.editor import draft, register, review


class Response:
    def __init__(self, body, headers=None, url="https://example.com/feed"):
        self.body, self.headers, self.url = body, headers or {}, url

    def read(self, limit):
        return self.body[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.article = json.loads((ROOT / "data/articles.json").read_text())[0]
        self.source = {"id": "test", "name": "テスト", "feed_url": "https://example.com/feed",
                       "category": "science", "terms_url": "https://example.com/terms",
                       "terms_checked_at": "2026-09-20", "usage_note": "テスト", "enabled": True}

    def test_conditional_fetch(self):
        with patch("web.collect.urlopen", side_effect=[
            Response(b"User-agent: *\nAllow: /"),
            Response(b"<rss/>", {"ETag": '"v2"'})
        ]) as fetch:
            body, validators = fetch_feed(self.source, {"etag": '"v1"'})
            self.assertEqual(body, b"<rss/>")
            self.assertEqual(validators["etag"], '"v2"')
            self.assertEqual(fetch.call_args_list[1].args[0].get_header("If-none-match"), '"v1"')

    def test_robots_denial_stops_before_feed(self):
        with patch("web.collect.urlopen", return_value=Response(b"User-agent: *\nDisallow: /")) as fetch:
            with self.assertRaises(ValueError):
                fetch_feed(self.source, {})
            self.assertEqual(fetch.call_count, 1)

    def test_robots_failure_does_not_fetch_feed(self):
        with patch("web.collect.urlopen", side_effect=HTTPError("https://example.com/robots.txt", 503, "unavailable", {}, None)) as fetch:
            with self.assertRaises(HTTPError):
                fetch_feed(self.source, {})
            self.assertEqual(fetch.call_count, 1)

    def test_304_keeps_last_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candidates.json"
            previous = '[{"source_url":"https://example.com/a","fetched_at":"2026-09-19"}]'
            path.write_text(previous)
            with patch("web.collect.fetch_feed", return_value=(None, {})):
                self.assertEqual(collect([self.source], temp, now=100), 0)
            self.assertEqual(path.read_text(), previous)
            self.assertEqual(json.loads((Path(temp) / "fetch-state.json").read_text())["test"]["status"], "unchanged")

    def test_304_response(self):
        with patch("web.collect.urlopen", side_effect=[Response(b"User-agent: *\nAllow: /"),
                   HTTPError("https://example.com/feed", 304, "unchanged", {}, None)]):
            body, validators = fetch_feed(self.source, {"etag": '"v1"'})
            self.assertIsNone(body)
            self.assertEqual(validators["etag"], '"v1"')

    def test_draft_does_not_invent_review_or_dates(self):
        for raw, expected in [(None, ""), ("invalid", ""),
                              ("Fri, 18 Sep 2026 18:02:53 +0000", "2026-09-18"),
                              ("2026-09-18T18:02:53Z", "2026-09-18")]:
            article = draft({"source_published_at": raw})
            self.assertEqual(article["published_at"], expected)
            self.assertEqual(article["checked_at"], "")
            self.assertEqual(article["status"], "pending")

    def test_register_preserves_existing_and_fails_atomically(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "articles.json"
            original = (ROOT / "data/articles.json").read_text()
            path.write_text(original)
            with self.assertRaises(ValueError):
                register(dict(self.article, status="pending"), path)
            self.assertEqual(path.read_text(), original)
            register(dict(self.article, reason="掲載理由を再確認しました。"), path)
            self.assertEqual(len(json.loads(path.read_text())), 2)

    def test_review_escapes_feed_markup(self):
        with tempfile.TemporaryDirectory() as temp:
            a = {"title": "<script>bad</script>", "source_name": "NASA", "status": "pending",
                 "source_published_at": None, "fetched_at": "2026-09-20",
                 "source_url": "https://example.com/article", "id": "candidate"}
            (Path(temp) / "candidates.json").write_text(json.dumps([a]))
            html = review(temp).read_text()
            self.assertNotIn("<script>", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertIn("noindex,nofollow", html)


if __name__ == "__main__":
    unittest.main()
