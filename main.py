import asyncio
import threading
from datetime import datetime
import pytz
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, CHANNEL_ID, PORT, TIMEZONE, POST_HOURS
from bot import ModelPoster


poster: ModelPoster = None


async def health(request):
    return web.Response(text="OK", status=200)


async def root(request):
    count = poster.db.get_stats() if poster else 0
    hours = ", ".join(f"{h}:00" for h in POST_HOURS)
    return web.Response(
        text=(
            f"🤖 3D Print Bot — RUNNING\n"
            f"📢 Канал: {CHANNEL_ID}\n"
            f"📦 Опубликовано моделей: {count}\n"
            f"🕐 Посты в: {hours} ({TIMEZONE})\n"
            f"⏰ Сейчас: {datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')}"
        ),
        status=200,
    )


async def post_job():
    global poster
    tz = pytz.timezone(TIMEZONE)
    print(f"\n{'='*50}")
    print(f"🕐 Пост в {datetime.now(tz).strftime('%H:%M:%S')}")
    await poster.post_model()
    print(f"{'='*50}\n")


def run_polling():
    global poster
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_polling():
        print("🤖 Бот запущен, слушаю команды...")
        await poster.dp.start_polling(poster.bot)

    loop.run_until_complete(start_polling())


async def on_startup(app):
    global poster
    print("🚀 Запуск 3D Print Bot...")
    print(f"📢 Канал: {CHANNEL_ID}")
    print(f"🕐 Часы постинга: {POST_HOURS}")
    print(f"🌍 Часовой пояс: {TIMEZONE}")

    poster = ModelPoster()

    scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
    for hour in POST_HOURS:
        scheduler.add_job(
            post_job,
            "cron",
            hour=hour,
            minute=0,
            id=f"post_{hour}",
            replace_existing=True,
        )
    scheduler.start()
    app["scheduler"] = scheduler
    print(f"✅ Планировщик запущен. Постов в день: {len(POST_HOURS)}")

    polling_thread = threading.Thread(target=run_polling, daemon=True)
    polling_thread.start()
    print("✅ Polling запущен в фоне")

    print(f"🌐 Health check: http://0.0.0.0:{PORT}/health")


async def on_shutdown(app):
    global poster
    print("🛑 Завершение работы...")
    app["scheduler"].shutdown(wait=False)
    if poster:
        await poster.close()


app = web.Application()
app.router.add_get("/", root)
app.router.add_get("/health", health)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Установи BOT_TOKEN в переменных окружения!")
        exit(1)
    if not CHANNEL_ID:
        print("❌ Установи CHANNEL_ID!")
        exit(1)

    print(f"🌐 Веб-сервер на порту {PORT}...")
    web.run_app(app, host="0.0.0.0", port=PORT)
