import aiohttp
from .base import BaseParser
from config import USER_AGENT


class ThingiverseParser(BaseParser):
    source_name = "Thingiverse"
    API_URL = "https://api.thingiverse.com/popular"

    def __init__(self):
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

    async def fetch_models(self, limit: int = 20) -> list[dict]:
        models = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.API_URL,
                    params={"page": 1, "per_page": limit, "type": "things"},
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        print(f"[Thingiverse] HTTP {resp.status}")
                        return []
                    data = await resp.json()

                    for item in data:
                        try:
                            model_id = str(item["id"])
                            title = item.get("name", "Untitled")
                            desc = item.get("description") or ""
                            if len(desc) > 500:
                                desc = desc[:497] + "..."

                            source_url = item.get(
                                "public_url",
                                f"https://www.thingiverse.com/thing:{model_id}",
                            )
                            image_url = item.get("thumbnail", "")

                            models.append(
                                {
                                    "id": model_id,
                                    "title": title,
                                    "description": desc or "Без описания",
                                    "image_url": image_url,
                                    "source_url": source_url,
                                    "file_url": f"{source_url}/files",
                                    "file_name": f"thing_{model_id}.stl",
                                    "source": self.source_name,
                                }
                            )
                        except Exception as e:
                            print(f"[Thingiverse] parse error: {e}")
                            continue
        except Exception as e:
            print(f"[Thingiverse] fetch error: {e}")
        return models
