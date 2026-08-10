import aiohttp
from .base import BaseParser
from config import USER_AGENT


class PrintablesParser(BaseParser):
    source_name = "Printables"
    API_URL = "https://api.printables.com/graphql"

    def __init__(self):
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def fetch_models(self, limit: int = 20) -> list[dict]:
        query = """
        query Search($limit: Int!) {
          prints(
            limit: $limit
            orderBy: {field: "likes_count", dir: DESC}
            hasDiscountedPrice: false
            isDownloadable: true
          ) {
            items {
              id
              name
              description
              slug
              images { filePath }
              user { userName }
              files { filePath name size }
              likeCount
              downloadCount
            }
          }
        }
        """

        models = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL,
                    json={"query": query, "variables": {"limit": limit}},
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        print(f"[Printables] HTTP {resp.status}")
                        return []

                    data = await resp.json()
                    if "errors" in data:
                        print(f"[Printables] API errors: {data['errors']}")
                        return []

                    items = (
                        data.get("data", {})
                        .get("prints", {})
                        .get("items", [])
                    )

                    for item in items:
                        try:
                            model_id = str(item["id"])
                            title = item.get("name", "Untitled")
                            desc = item.get("description") or ""
                            if len(desc) > 500:
                                desc = desc[:497] + "..."

                            slug = item.get("slug", "")
                            source_url = (
                                f"https://www.printables.com/model/"
                                f"{model_id}-{slug}"
                            )

                            images = item.get("images", [])
                            image_url = ""
                            if images:
                                fp = images[0].get("filePath", "")
                                if fp:
                                    image_url = f"https://media.printables.com/{fp}"

                            files = item.get("files", [])
                            file_url = ""
                            file_name = f"model_{model_id}.stl"
                            for f in files:
                                fname = f.get("name", "").lower()
                                if fname.endswith(
                                    (".stl", ".3mf", ".obj", ".step", ".stp")
                                ):
                                    fp = f.get("filePath", "")
                                    if fp:
                                        file_url = (
                                            f"https://media.printables.com/{fp}"
                                        )
                                        file_name = f.get("name", file_name)
                                        break

                            models.append(
                                {
                                    "id": model_id,
                                    "title": title,
                                    "description": desc or "Без описания",
                                    "image_url": image_url,
                                    "source_url": source_url,
                                    "file_url": file_url,
                                    "file_name": file_name,
                                    "source": self.source_name,
                                }
                            )
                        except Exception as e:
                            print(f"[Printables] parse error: {e}")
                            continue
        except Exception as e:
            print(f"[Printables] fetch error: {e}")
        return models
