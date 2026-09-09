# Automations

Scheduled Python jobs run through GitHub Actions.

## Website to Telegram

`.github/workflows/site-to-telegram.yml` runs every six hours and publishes new posts from `https://amirpourmand.ir/index.xml` to Telegram.

Create these repository secrets:

- `TELEGRAM_BOT_TOKEN`: token from [@BotFather](https://t.me/BotFather)
- `TELEGRAM_CHANNEL_ID`: channel ID, such as `@my_channel` or `-100...`

The bot must be an administrator of the target channel. The first run records existing feed entries; later runs publish new entries and commit their IDs to `state/telegram-site-posts.json`.

Run locally with:

```bash
TELEGRAM_BOT_TOKEN=... TELEGRAM_CHANNEL_ID=@my_channel \
python3 -m workflows.runner site-to-telegram
```
