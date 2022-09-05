import json
import time
import requests
import aiohttp
import asyncio

from bs4 import BeautifulSoup
import concurrent.futures

start_time = time.time()


class Parser:
    def __init__(self, url):
        self.url = url
        self.news = {}
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36"
        }

    def find_news(self):
        """
        Поиск новостей на галвной странице
        """
        response = requests.get(url=self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, "html.parser")
        print(f"Log  {soup}")
        all_news = soup.find_all('tr', class_='athing')
        for news in all_news:
            # https://news.ycombinator.com/item?id=32624461  шаблон страницы с комментом
            print(f"Log  news \n {news} \n id {news['id']}")
            print(f"Log  news2 \n {news.contents[4].a['href']}  {type(news.contents[4])} \n")
            news_title = news.text
            url = news.contents[4].a['href']
            if "http" not in url:
                url = f"https://news.ycombinator.com/{url}"
            self.news[news_title] = {"news_url": url, "id": news['id'],
                                     "comment_url": f"https://news.ycombinator.com/item?id={news['id']}"}
            print(self.news.keys())

    def load(self, url):
        try:
            response = requests.get(url=url, headers=self.headers)
            return response.text
        except Exception:
            print(f"Log bad url {url}")

    async def download_news(self):
        """
        Скачивание новости: контент новости, страница комментариев, ссылки в комментариях
        """
        loop = asyncio.get_running_loop()
        all_news_data = []
        with concurrent.futures.ProcessPoolExecutor() as pool:
            for key in list(self.news.keys()):
                print(f"Log key {key}")
                news_data = await loop.run_in_executor(pool, self.load, self.news[key]["news_url"])
                all_news_data.append(news_data)
        return all_news_data
       # async with aiohttp.ClientSession() as session:
       #     tasks = []
       #     for key in list(self.news.keys()):
       #         tasks.append(asyncio.create_task(session.get(self.news[key]["news_url"])))

       #     responses = await asyncio.gather(*tasks)
       #     return [await r.text() for r in responses]

    def save_to_file(self):
        json.dump(self.news, open("dump.json", 'w'))


def main():
    parser = Parser(url="https://news.ycombinator.com/")
    parser.find_news()
    data = asyncio.run(parser.download_news())
    print(f"Log data {type(data)} --- {len(data)}")
    finish_time = time.time() - start_time
    print(f"Затраченное на работу скрипта время: {finish_time}")


if __name__ == '__main__':
    main()
