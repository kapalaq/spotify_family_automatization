from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from datetime import datetime
from config import TelegramConfig


ADMIN_ID = TelegramConfig().admin_id
scheduler = AsyncIOScheduler()

def setup_scheduler(bot: Bot):

    async def send_custom_messages():
        today = datetime.now().day
        groups = await get_groups()
        for group_id, custom_day in groups:
            if custom_day == today:
                await bot.send_message(group_id, "Please upload your monthly payment PDF.")

    async def report_defaulters():
        today = datetime.now().day
        defaulters = await get_defaulters(today)
        if defaulters:
            msg = "🚨 Users who didn't send PDF within 3 days:\n"
            for group_id, user_id in defaulters:
                msg += f"Group {group_id} — User {user_id}\n"
            await bot.send_message(ADMIN_ID, msg)

    scheduler.add_job(send_custom_messages, "cron", hour=9, minute=0)
    scheduler.add_job(report_defaulters, "cron", hour=9, minute=5)

    scheduler.start()
