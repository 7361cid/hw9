import sys
import numpy as np
import time
import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup


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
        all_news = soup.find_all('tr', class_='athing')
        for news in all_news:
            # https://news.ycombinator.com/item?id=32624461  шаблон страницы с комментом
            news_title = news.text.replace("\n", "")
            url = news.contents[4].a['href']
            if "http" not in url:
                continue
            self.news[news_title] = {"news_url": url, "id": news['id'],
                                     "comment_url": f"https://news.ycombinator.com/item?id={news['id']}"}

    async def get_data(self):
        async with aiohttp.ClientSession() as session:
            self.find_news()
            tasks = []
            for news_title in list(self.news.keys())[:2]:  # TODO full list
                task = asyncio.create_task(self.download_news(news_title=news_title, session=session))
                tasks.append(task)
            await asyncio.gather(*tasks)

    async def download_news(self, session, news_title, retries=3):
        """
        Скачивание новости: контент новости, страница комментариев, ссылки в комментариях
        """
        news = self.news[news_title]
        while retries:
            try:
                async with session.get(url=news["news_url"], headers=self.headers) as news_page_response:
                    news["content"] = await news_page_response.text()
                    async with session.get(url=news["comment_url"], headers=self.headers) as news_comment_response:
                        news["comment_page_content"] = await news_comment_response.text()
                        soup = BeautifulSoup(news_comment_response.text, "html.parser")
                        all_tags_a_from_comments = soup.find_all('a')
                        all_links_from_comments = []
                        for tag in all_tags_a_from_comments:
                            href = tag["href"]
                            if "http" in href:
                                all_links_from_comments.append(href)
                        news_comment_links_data = []
                        for comment_link in all_links_from_comments:
                            if "http" in comment_link:
                                comment_link_response = requests.get(url=comment_link, headers=self.headers)
                            else:
                                comment_link_response = requests.get(url=f"https://news.ycombinator.com/{comment_link}",
                                                                     headers=self.headers)
                            news_comment_links_data.append({f"{comment_link}": comment_link_response.text})
                        news["news_comment_links_data"] = news_comment_links_data
                        self.news[news_title] = news

            except Exception as exc:   #aiohttp.client_exceptions.ClientConnectorError
                retries -= 1
            else:
                break

    def save_to_file(self):
        dictionary = {}
        for key in list(self.news.keys()):
            dictionary[key] = self.news[key]  # иначе TypeError: can't pickle multidict._multidict.CIMultiDictProxy objects
        np.save('my_file.npy', dictionary)

    def load_dict_from_file(self):
        return np.load('my_file.npy', allow_pickle='TRUE').item()



def main():
    parser = Parser(url="https://news.ycombinator.com/")
    asyncio.run(parser.get_data())
    parser.save_to_file()
    read_dictionary = parser.load_dict_from_file()
    print(f" SIZE {sys.getsizeof(read_dictionary)}")
    finish_time = time.time() - start_time
    print(f"Затраченное на работу скрипта время: {finish_time}")


if __name__ == '__main__':
    main()
