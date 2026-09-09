import unittest

from workflows.site_to_telegram import _media_filename, format_media_caption, format_message, parse_feed


class FeedTests(unittest.TestCase):
    def test_parses_rss(self):
        payload = b'<rss><channel><item><title>Hello</title><guid>1</guid><description><![CDATA[<p>Text</p>]]></description><enclosure url="https://cdn.example.com/hello.mp3" type="audio/mpeg"/></item></channel></rss>'
        post = parse_feed(payload)[0]
        self.assertEqual(post["id"], "1")
        self.assertEqual(post["link"], "https://cdn.example.com/hello.mp3")
        self.assertEqual(post["audio_url"], "https://cdn.example.com/hello.mp3")
        self.assertEqual(post["audio_type"], "audio/mpeg")

    def test_parses_atom(self):
        payload = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>1</id><title>Hello</title><link href="https://example.com/hello"/><summary>Text</summary></entry></feed>'
        self.assertEqual(parse_feed(payload)[0]["link"], "https://example.com/hello")
        self.assertEqual(parse_feed(payload)[0]["audio_url"], "")

    def test_formats_safe_telegram_html(self):
        message = format_message({"title": "A & B", "link": "https://example.com/?a=1&b=2", "summary": "<b>hello</b>"})
        self.assertIn("A &amp; B", message)
        self.assertIn("https://example.com/?a=1&amp;b=2", message)
        self.assertNotIn("Read the post", message)
        self.assertNotIn("<b>hello</b>", message)

    def test_preserves_description_spacing_and_headings(self):
        description = "<h3 id=\"graph\">گراف درس‌های متمم</h3> <p>پاراگراف اول.</p> <p><a href=\"https://example.com/graph\">گراف متمم</a></p>"
        message = format_message({"title": "متمم", "link": "https://example.com/post", "summary": description})
        self.assertIn("<b>گراف درس‌های متمم</b>", message)
        self.assertIn("پاراگراف اول.\n\n<a href=\"https://example.com/graph\">گراف متمم</a>", message)

    def test_media_caption_omits_enclosure_url(self):
        caption = format_media_caption({
            "title": "E02",
            "link": "https://cdn.example.com/episode.mp3",
            "summary": "<p>شرح قسمت.</p>",
        })
        self.assertEqual(caption, "<b>E02</b>\n\nشرح قسمت.")
        self.assertNotIn("episode.mp3", caption)

    def test_media_filename_uses_episode_title(self):
        filename = _media_filename({"title": "E02 / یک قسمت خوب"}, "audio/mp3")
        self.assertEqual(filename, "E02 - یک قسمت خوب.mp3")


if __name__ == "__main__":
    unittest.main()
