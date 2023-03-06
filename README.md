[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test workflow](https://github.com/MishaVyb/bart-bot/actions/workflows/tests.yml/badge.svg)](https://github.com/MishaVyb/bart-bot/actions/workflows/tests.yml)
[![Test workflow](https://github.com/MishaVyb/bart-bot/actions/workflows/deploy.yml/badge.svg)](https://github.com/MishaVyb/bart-bot/actions/workflows/deploy.yml) ![](https://img.shields.io/badge/PTB-20.1-blue) ![](https://img.shields.io/badge/Pyrogram-2.0.1-blue) ![](https://img.shields.io/badge/Anyio-3.6.2-blue) ![](https://img.shields.io/badge/SQLAlchemy-2.0.4-blue)

# Bart Bot
🥛🍥🥟🍚🥓🍙🥖☕️🍣 <--- 🐈‍⬛
Telegram bot for handling your pet photos.

## Usage
Send any photo to bot chanel. Then feed your pet by emoji food. And wait for reply, you'll see one of pictures you've upload before.

## Features
- Uniq. Replying to every one by deferent pre-defined messages.
- Flexable. Has different starages for every participant. Storage could be shared by adding to Famely.
- Unpredictable. Chose a random image to reply after feeding.

> Bart Bot behaves like yor real pet...

## Implementation
- Fully asynchronous. Async `PTB`. Async `SQLAlchemy`. Async `Pyrogram`.
- Fully durable. Store all chats history in database.
- Custom middlewares support. Familiar to us by all web frameworks.
- Covered by tests. E2E tests launched at separate Telegram [environment](https://core.telegram.org/bots/features#testing-your-bot) with test [accounts](https://core.telegram.org/api/auth#test-accounts).

