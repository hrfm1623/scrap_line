import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from web.build import ROOT, build
from web.collect import collect, parse_feed
from web.content import validate_articles


class NewsTests(unittest.TestCase):
    def setUp(self):
        self.articles = json.loads((ROOT / "tests/fixtures/articles.json").read_text())
        self.article = copy.deepcopy(self.articles[0])
        self.article["is_demo"] = False
        self.article["review_method"] = "ai_assisted"
        self.article["human_checked_at"] = None
        self.source = {"id": "test", "name": "テスト", "feed_url": "https://example.com/feed",
                       "terms_url": "https://example.com/terms", "terms_checked_at": "2026-09-20",
                       "usage_note": "テスト専用", "enabled": True, "category": "science"}
        self.rss = b'<rss><channel><item><title>Discovery</title><link>https://example.com/a</link></item></channel></rss>'

    def test_demo_and_public_are_separate(self):
        self.assertEqual(len(validate_articles(self.articles, demo=True)), 6)
        with self.assertRaises(ValueError):
            validate_articles(self.articles)

    def test_draft_is_rejected(self):
        self.article["status"] = "pending"
        with self.assertRaises(ValueError):
            validate_articles([self.article])

    def test_required_fields_categories_dates_and_urls(self):
        for field, value in [("reviewer", ""), ("reason", ""), ("category", "unknown"),
                             ("published_at", "2099-01-01"), ("checked_at", "2026-09-01"),
                             ("source_url", "javascript:alert(1)"),
                             ("terms_url", "https://user:password@example.com")]:
            with self.subTest(field=field):
                article = dict(self.article, **{field: value})
                with self.assertRaises(ValueError):
                    validate_articles([article])

    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            validate_articles([self.article, self.article])
        with self.assertRaises(ValueError):
            validate_articles([self.article, dict(self.article, id="another-id")])

    def test_tragedy_overrides_positive_words(self):
        self.article["title"] = "災害から救助成功、喜びの声"
        with self.assertRaises(ValueError):
            validate_articles([self.article])

    def test_preview_escapes_html_and_is_noindex(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "articles.json"
            self.article["title"] = '<script>alert("x")</script>'
            data.write_text(json.dumps([self.article]))
            output = Path(temp) / "site"
            build(data, output)
            html = (output / "index.html").read_text()
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn('<script>alert', html)
            self.assertIn('content="noindex, nofollow"', html)
            self.assertIn('X-Robots-Tag: noindex', (output / "_headers").read_text())
            self.assertNotIn('<loc>', (output / "sitemap.xml").read_text())

    def test_production_requires_origin_and_real_content(self):
        with tempfile.TemporaryDirectory() as temp:
            demo = ROOT / "tests/fixtures/articles.json"
            for origin, is_demo in [("", True), ("https://example.com", True)]:
                with self.assertRaises(ValueError):
                    build(demo, temp, origin, production=True, demo=is_demo)
            empty = Path(temp) / "empty.json"
            empty.write_text("[]")
            with self.assertRaises(ValueError):
                build(empty, temp, "https://example.com", production=True)

    def test_live_editorial_data(self):
        self.assertEqual(len(validate_articles(json.loads((ROOT / "data/articles.json").read_text()))), 2)

    def test_ai_check_is_not_human_check(self):
        self.article["human_checked_at"] = "2026-09-20"
        with self.assertRaises(ValueError):
            validate_articles([self.article])

    def test_production_seo_and_preview_rebuild(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "data.json"
            data.write_text(json.dumps([self.article]))
            output = Path(temp) / "site"
            build(data, output, "https://news.example.com", production=True)
            self.assertIn('href="https://news.example.com/"', (output / "index.html").read_text())
            self.assertNotIn('noindex', (output / "index.html").read_text())
            self.assertIn('Sitemap: https://news.example.com/sitemap.xml', (output / "robots.txt").read_text())
            self.assertIn('<loc>https://news.example.com/</loc>', (output / "sitemap.xml").read_text())
            build(data, output)
            self.assertNotIn('news.example.com', (output / "sitemap.xml").read_text())

    def test_invalid_build_preserves_last_page(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "data.json"
            output = Path(temp) / "site"
            data.write_text(json.dumps([self.article]))
            build(data, output)
            previous = (output / "index.html").read_bytes()
            data.write_text('[{}]')
            with self.assertRaises(ValueError):
                build(data, output)
            self.assertEqual(previous, (output / "index.html").read_bytes())

    def test_rss_and_atom_stay_pending(self):
        for feed in [self.rss, b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Discovery</title><link rel="self" href="https://example.com/feed"/><link href="https://example.com/a"/></entry></feed>']:
            article = parse_feed(feed, self.source)[0]
            self.assertEqual(article["status"], "pending")
            self.assertEqual(article["source_url"], "https://example.com/a")
            self.assertIsNone(article["source_published_at"])
            self.assertNotIn("checked_at", article)

    def test_empty_malformed_and_dtd_rejected(self):
        for raw in [b'<rss><channel/></rss>', b'<rss>', b'<!DOCTYPE rss><rss/>', b'<html/>']:
            with self.assertRaises(Exception):
                parse_feed(raw, self.source)

    def test_failed_fetch_preserves_cache_and_records_error(self):
        with tempfile.TemporaryDirectory() as temp:
            collect([self.source], temp, fetch=lambda _: self.rss, now=100)
            previous = (Path(temp) / "candidates.json").read_bytes()
            with self.assertLogs(level="ERROR"):
                result = collect([self.source], temp, fetch=Mock(side_effect=OSError("offline")), now=22000)
            self.assertEqual(result, 1)
            self.assertEqual(previous, (Path(temp) / "candidates.json").read_bytes())
            self.assertEqual(json.loads((Path(temp) / "fetch-state.json").read_text())["test"]["status"], "error")

    def test_fetch_interval_and_deduplication(self):
        with tempfile.TemporaryDirectory() as temp:
            fetch = Mock(return_value=self.rss)
            collect([self.source], temp, fetch=fetch, now=100)
            collect([self.source], temp, fetch=fetch, now=200)
            self.assertEqual(fetch.call_count, 1)
            collect([self.source], temp, fetch=fetch, now=22000)
            self.assertEqual(fetch.call_count, 2)
            self.assertEqual(len(json.loads((Path(temp) / "candidates.json").read_text())), 1)

    def test_unreviewed_feed_not_fetched(self):
        with tempfile.TemporaryDirectory() as temp:
            fetch = Mock()
            self.source["terms_checked_at"] = ""
            with self.assertRaises(ValueError):
                collect([self.source], temp, fetch=fetch)
            fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
