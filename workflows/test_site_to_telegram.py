import unittest

from workflows.site_to_telegram import format_message, parse_feed


class FeedTests(unittest.TestCase):
    def test_parses_rss(self):
        payload = b'<rss><channel><item><title>Hello</title><link>https://example.com/hello</link><guid>1</guid><description><![CDATA[<p>Text</p>]]></description></item></channel></rss>'
        self.assertEqual(parse_feed(payload)[0]["id"], "1")

    def test_parses_atom(self):
        payload = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>1</id><title>Hello</title><link href="https://example.com/hello"/><summary>Text</summary></entry></feed>'
        self.assertEqual(parse_feed(payload)[0]["link"], "https://example.com/hello")

    def test_formats_safe_telegram_html(self):
        message = format_message({"title": "A & B", "link": "https://example.com/?a=1&b=2", "summary": "<b>hello</b>"})
        self.assertIn("A &amp; B", message)
        self.assertNotIn("<b>hello</b>", message)


if __name__ == "__main__":
    unittest.main()
