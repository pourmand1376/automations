# Automations

Scheduled Python jobs run through GitHub Actions.

## Website to Telegram

`.github/workflows/site-to-telegram.yml` runs once per day at 00:17 UTC and publishes new posts from `https://amirpourmand.ir/index.xml` to Telegram.

Create these repository secrets:

- `TELEGRAM_BOT_TOKEN`: token from [@BotFather](https://t.me/BotFather)

The configured channel is `@pourmand_amir`. The bot must be an administrator of that channel. The first run records existing feed entries; later runs publish new entries and commit their IDs to `state/amirpourmand_ir_to_telegram.json`.

Run locally with:

```bash
TELEGRAM_BOT_TOKEN=... \
python3 -m workflows.runner site-to-telegram
```
