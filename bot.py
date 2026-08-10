lt, list) and result:
                ru_text = result[0].get("translation_text", en_text)
                print(f"🤖 Translated (RU): {ru_text[:100]}...")
                return ru_text

            return en_text

    except Exception as e:
        print(f"🤖 HF error: {e}")

    return None


# ── ModelPoster ───────────────────────────────────────────
class ModelPoster:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.db = Database()
        self.dp = Dispatcher()
        self._register_handlers()

    def _register_handlers(self):
        @self.dp.message(Command("post_now"))
        async def cmd_post_now(message: types.Message):
            await message.answer("🔍 Ищу новую модель для публикации...")
            success = await self.post_model()
            if success:
                await message.answer("✅ Модель опубликована в канале!")
            else:
                await message.answer(
                    "⚠️ Не удалось найти новую модель. "
                    "Возможно, все уже были опубликованы или источники недоступны."
                )

        @self.dp.message(Command("stats"))
        async def cmd_stats(message: types.Message):
            count = self.db.get_stats()
            ai_status = "✅ Включён (Hugging Face)" if HF_HEADERS else "❌ Выключен"
            await message.answer(
                f"📊 <b>Статистика бота:</b>\n"
                f"📦 Опубликовано моделей: <b>{count}</b>\n"
                f"🔍 Источников: <b>{len(PARSERS)}</b>\n"
                f"🤖 AI-описания: {ai_status}\n"
                f"📢 Канал: {CHANNEL_ID}",
                parse_mode="HTML",
            )

        @self.dp.message(Command("help"))
        async def cmd_help(message: types.Message):
            await message.answer(
                "🤖 <b>3D Print Bot — команды:</b>\n\n"
                "/post_now — немедленно опубликовать новую модель\n"
                "/stats — статистика бота\n"
                "/help — это сообщение",
                parse_mode="HTML",
            )

        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            await message.answer(
                "👋 Привет! Я бот, который публикует бесплатные "
                "3D-модели для печати в канале.\n\n"
                "/post_now — опубликовать модель сейчас\n"
                "/stats — посмотреть статистику\n"
                "/help — справка"
            )

    async def _download(self, url: str, path: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status != 200:
                        return False
                    with open(path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            f.write(chunk)
            return True
        except Exception as e:
            print(f"Download error: {e}")
            return False

    async def post_model(self) -> bool:
        all_models = []
        for parser in PARSERS:
            print(f"🔍 Fetching {parser.source_name}...")
            models = await parser.fetch_models(limit=30)
            print(f"   → {len(models)} models")
            all_models.extend(models)

        if not all_models:
            print("❌ Нет моделей")
            return False

        new_models = [
            m
            for m in all_models
            if not self.db.is_posted(m["source"], m["id"])
        ]
        print(
            f"📊 Всего: {len(all_models)}, "
            f"Новых: {len(new_models)}, "
            f"Отправлено ранее: {len(all_models) - len(new_models)}"
        )

        if not new_models:
            print("⚠️ Все модели уже были отправлены!")
            return False

        model = random.choice(new_models)

        description = model.get("description") or "Без описания"
        if USE_AI_DESCRIPTION and HF_HEADERS and model.get("image_url"):
            print("🤖 Генерирую AI-описание по фото...")
            ai_desc = await generate_description(model["image_url"])
            if ai_desc:
                description = ai_desc

        caption = (
            f"🖨️ <b>{model['title']}</b>\n\n"
            f"{description}\n\n"
            f"📌 <a href='{model['source_url']}'>"
            f"Источник: {model['source']}</a>"
        )
        if len(caption) > 1024:
            caption = caption[:1020] + "..."

        try:
            sent_photo = False
            if model.get("image_url"):
                try:
                    await self.bot.send_photo(
                        CHANNEL_ID,
                        photo=model["image_url"],
                        caption=caption,
                        parse_mode="HTML",
                    )
                    sent_photo = True
                except Exception as e:
                    print(f"Photo send failed: {e}")

            if not sent_photo:
                await self.bot.send_message(
                    CHANNEL_ID,
                    text=caption,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )

            file_url = model.get("file_url", "")
            file_name = model.get("file_name", "model.stl")

            if file_url and not file_url.endswith("/files"):
                with tempfile.NamedTemporaryFile(
                    suffix=f"_{file_name}", delete=False
                ) as tmp:
                    tmp_path = tmp.name

                print(f"⬇️ Downloading: {file_name}")
                success = await self._download(file_url, tmp_path)

                if success:
                    size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
                    if size_mb < 50:
                        await self.bot.send_document(
                            CHANNEL_ID,
                            document=FSInputFile(tmp_path, filename=file_name),
                            caption=f"📁 {file_name}",
                        )
                    else:
                        await self.bot.send_message(
                            CHANNEL_ID,
                            text=(
                                f"📁 Файл {size_mb:.1f}MB — "
                                f"<a href='{file_url}'>скачать напрямую</a>"
                            ),
                            parse_mode="HTML",
                        )
                    os.unlink(tmp_path)
                else:
                    await self.bot.send_message(
                        CHANNEL_ID,
                        text=f"📁 <a href='{file_url}'>Скачать {file_name}</a>",
                        parse_mode="HTML",
                    )
            else:
                await self.bot.send_message(
                    CHANNEL_ID,
                    text=(
                        f"📁 <a href='{model['source_url']}'>"
                        f"Скачать файлы на {model['source']}</a>"
                    ),
                    parse_mode="HTML",
                )

            self.db.mark_posted(model["source"], model["id"], model["title"])
            print(f"✅ Posted: {model['title']} ({model['source']})")
            return True

        except TelegramAPIError as e:
            print(f"Telegram API error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    async def close(self):
        await self.bot.session.close()
