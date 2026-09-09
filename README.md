# Automations

Scheduled Python jobs run through GitHub Actions.

## Website to Telegram

`.github/workflows/site-to-telegram.yml` runs once per day at 00:17 UTC and publishes new posts from `https://amirpourmand.ir/index.xml` to Telegram.

Create these repository secrets:

- `TELEGRAM_BOT_TOKEN`: token from [@BotFather](https://t.me/BotFather)
- `TELEGRAM_CHANNEL_ID`: numeric ID of the channel, usually in the form `-1001234567890`

The bot must be an administrator of the target channel. The first run records existing feed entries; later runs publish new entries and commit their IDs to `state/amirpourmand_ir_to_telegram.json`.

To find a channel ID, add the bot to the channel, publish a test message, then open:

```text
https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
```

Look for `channel_post.chat.id` in the response.

Run locally with:

```bash
TELEGRAM_BOT_TOKEN=... TELEGRAM_CHANNEL_ID=-1001234567890 \
python3 -m workflows.runner site-to-telegram
```
