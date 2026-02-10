import html

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import Settings
from app.metrics import collect_system_stats


class BotRuntime:
    def __init__(self) -> None:
        self.application: Application | None = None

    @property
    def is_ready(self) -> bool:
        return self.application is not None

    @staticmethod
    def _chat_allowed(chat_id: int) -> bool:
        if not Settings.chat_ids:
            return True
        return chat_id in Settings.chat_ids

    @staticmethod
    async def _reject_unknown_chat(update: Update) -> bool:
        chat = update.effective_chat
        if not chat:
            return True

        if BotRuntime._chat_allowed(chat.id):
            return False

        await update.effective_message.reply_text("Чат не разрешен для управления ботом.")
        return True

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await self._reject_unknown_chat(update):
            return

        chat = update.effective_chat
        await update.effective_message.reply_text(
            "Бот готов.\n"
            f"Chat ID: {chat.id}\n"
            "Доступные команды: /help, /status, /disk"
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await self._reject_unknown_chat(update):
            return

        await update.effective_message.reply_text(
            "/status - нагрузка CPU/RAM и uptime\n"
            "/disk - заполнение хранилища\n"
            "/help - список команд"
        )

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await self._reject_unknown_chat(update):
            return

        stats = collect_system_stats(Settings.metrics_disk_path)
        text = (
            "<b>Состояние сервера</b>\n"
            f"Источник метрик: <b>{stats['metrics_scope']}</b>\n"
            f"CPU: <b>{stats['cpu_percent']}</b>\n"
            f"Load avg (1/5/15): <b>{stats['load_average']}</b>\n"
            f"RAM: <b>{stats['memory_percent']}</b> ({stats['memory_used']} / {stats['memory_total']})\n"
            f"Boot: <b>{stats['boot_at']}</b>"
        )
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

    async def _cmd_disk(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await self._reject_unknown_chat(update):
            return

        stats = collect_system_stats(Settings.metrics_disk_path)
        text = (
            "<b>Хранилище</b>\n"
            f"Путь: <code>{html.escape(stats['disk_path'])}</code>\n"
            f"Занято: <b>{stats['disk_percent']}</b> ({stats['disk_used']} / {stats['disk_total']})\n"
            f"Свободно: <b>{stats['disk_free']}</b>"
        )
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

    async def start(self) -> None:
        if not Settings.bot_token:
            return

        self.application = Application.builder().token(Settings.bot_token).build()
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("disk", self._cmd_disk))

        await self.application.initialize()
        await self.application.start()
        if self.application.updater:
            await self.application.updater.start_polling()

    async def stop(self) -> None:
        if not self.application:
            return

        if self.application.updater:
            await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        self.application = None

    async def broadcast_html(self, text: str) -> list[int]:
        if not self.application:
            raise RuntimeError("Telegram bot is not started")

        if not Settings.chat_ids:
            raise RuntimeError("No TELEGRAM_CHAT_IDS configured")

        delivered_to: list[int] = []
        for chat_id in Settings.chat_ids:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            delivered_to.append(chat_id)

        return delivered_to
