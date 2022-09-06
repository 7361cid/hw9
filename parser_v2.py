import sys
import numpy as np
import time
import requests
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
        all_news = soup.find_all('tr', class_='athing')
        for news in all_news:
            news_title = news.text.replace("\n", "")
            url = news.contents[4].a['href']
            if "http" not in url:
                url = f"https://news.ycombinator.com/{url}"
            self.news[news_title] = {"news_url": url, "id": news['id'],
                                     "comment_url": f"https://news.ycombinator.com/item?id={news['id']}"}
            print(self.news.keys())

    def download_news_page_content(self, news_title, retries=3):
        update_news_data = self.news[news_title]
        while retries:
            try:
                response = requests.get(url=self.news[news_title]["news_url"], headers=self.headers)
            except Exception:
                print(f'Bad url {self.news[news_title]["news_url"]} retries left {retries}')
                retries -= 1
            else:
                update_news_data["content"] = response.text
                break
        return update_news_data

    def download_news_comment_page(self, news_title, retries=3):
        update_news_data = self.news[news_title]
        while retries:
            try:
                response = requests.get(url=self.news[news_title]["comment_url"], headers=self.headers)
            except Exception:
                print(f'Bad url {self.news[news_title]["comment_url"]} retries left {retries}')
                retries -= 1
            else:
                update_news_data["comment_page_content"] = response.text
                all_links_from_comments = self.parse_comment_page_links(response)
                if all_links_from_comments:
                    update_news_data["links_from_comments"] = all_links_from_comments
                break
        return update_news_data

    @staticmethod
    def parse_comment_page_links(response):
        soup = BeautifulSoup(response.text, "html.parser")
        all_tags_a_from_comments = soup.find_all('a')
        all_links_from_comments = []
        for tag in all_tags_a_from_comments:
            href = tag["href"]
            if "http" in href:
                all_links_from_comments.append(href)
        return all_links_from_comments

    async def download_news(self):
        """
        Скачивание новости: контент новости, страница комментариев, ссылки в комментариях
        """
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            for news_title in list(self.news.keys())[:2]:
                news_changed = await loop.run_in_executor(pool, self.download_news_page_content, news_title)
                self.news[news_title] = news_changed
                news_changed = await loop.run_in_executor(pool, self.download_news_comment_page, news_title)
                self.news[news_title] = news_changed

    def save_to_file(self):
        dictionary = {}
        for key in list(self.news.keys()):
            dictionary[key] = self.news[key]
        np.save('my_file.npy', dictionary)

    def load_dict_from_file(self):
        return np.load('my_file.npy', allow_pickle='TRUE').item()


def main():
    parser = Parser(url="https://news.ycombinator.com/")
    parser.find_news()
    asyncio.run(parser.download_news())
    parser.save_to_file()
    read_dictionary = parser.load_dict_from_file()
    print(f" SIZE {sys.getsizeof(read_dictionary)}")
    print(f'read_dictionary content {read_dictionary[list(read_dictionary.keys())[0]]["links_from_comments"]}')
    finish_time = time.time() - start_time
    print(f"Затраченное на работу скрипта время: {finish_time}")


if __name__ == '__main__':
    main()
