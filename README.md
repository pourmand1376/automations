# Automations

Scheduled Python jobs run through GitHub Actions.

## Website to Telegram

The workflows check both websites every hour and publish new posts to their configured Telegram channels:

- `amirpourmand.ir`, checked at minute 17
- `aprd.ir`, checked at minute 37

Create these repository secrets:

- `AMIRPOURMAND_IR_TELEGRAM_BOT_TOKEN`: bot token for `amirpourmand.ir`
- `AMIRPOURMAND_IR_TELEGRAM_CHANNEL_ID`: numeric channel ID for `amirpourmand.ir`
- `APRD_IR_TELEGRAM_BOT_TOKEN`: bot token for `aprd.ir`
- `APRD_IR_TELEGRAM_CHANNEL_ID`: numeric channel ID for `aprd.ir`

The bot must be an administrator of the target channel. The first run records existing feed entries; later runs publish new entries and commit their IDs to `state/amirpourmand_ir_to_telegram.json`.

To find a channel ID, add the bot to the channel and open:

```text
https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
```

Look for `channel_post.chat.id` in the response.

Run locally with:

```bash
AMIRPOURMAND_IR_TELEGRAM_BOT_TOKEN=... \
AMIRPOURMAND_IR_TELEGRAM_CHANNEL_ID=-1001234567890 \
python3 -m workflows.runner amirpourmand-ir
```
