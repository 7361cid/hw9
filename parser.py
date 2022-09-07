import schedule
import os
import datetime
import numpy as np
import time
import requests
import asyncio
import concurrent.futures

from bs4 import BeautifulSoup
from optparse import OptionParser


class Parser:
    def __init__(self, url, retries):
        self.url = url
        self.retries = retries
        if os.path.exists("news_dump.npy"):
            self.news = self.load_dict_from_file()
        else:
            self.news = {}
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
                      "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.106 Safari/537.36"
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
            if news_title not in list(self.news.keys()):
                url = news.contents[4].a['href']
                if "http" not in url:
                    url = f"https://news.ycombinator.com/{url}"
                self.news[news_title] = {"news_url": url, "id": news['id'],
                                         "comment_url": f"https://news.ycombinator.com/item?id={news['id']}"}

    def download_news_page_content(self, news_title):
        update_news_data = self.news[news_title]
        retries = self.retries
        while retries:
            try:
                response = requests.get(url=self.news[news_title]["news_url"], headers=self.headers)
            except Exception as exc:
                retries -= 1
                print(f"exc {exc}")
            else:
                update_news_data["content"] = response.text
                break
        return update_news_data

    def download_news_comment_page(self, news_title):
        update_news_data = self.news[news_title]
        retries = self.retries
        while retries:
            try:
                response = requests.get(url=self.news[news_title]["comment_url"], headers=self.headers)
            except Exception as exc:
                print(f"exc {exc}")
                retries -= 1
            else:
                update_news_data["comment_page_content"] = response.text
                all_links_from_comments = self.parse_comment_page_links(response)
                if all_links_from_comments:
                    update_news_data["links_from_comments"] = list(set(all_links_from_comments))
                break
        return update_news_data

    def download_comments_url_content(self, news_title):
        update_news_data = self.news[news_title]
        update_news_data["content_from_comment_urls"] = {}
        for url in update_news_data["links_from_comments"]:
            url_retries = self.retries
            while url_retries:
                try:
                    response = requests.get(url=url, headers=self.headers)
                except Exception as exc:
                    url_retries -= 1
                    print(f"exc {exc}")
                else:
                    update_news_data["content_from_comment_urls"][url] = response.text
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
                if "downloaded" not in list(self.news[news_title].keys()):
                    news_changed = await loop.run_in_executor(pool, self.download_news_page_content, news_title)
                    self.news[news_title] = news_changed
                    news_changed = await loop.run_in_executor(pool, self.download_news_comment_page, news_title)
                    self.news[news_title] = news_changed
                    if self.news[news_title]["links_from_comments"]:
                        news_changed = await loop.run_in_executor(pool, self.download_comments_url_content, news_title)
                        self.news[news_title] = news_changed
                    self.news[news_title]["downloaded"] = True
                else:
                    print(f"Log news already downloaded {news_title}")

    def save_to_file(self):
        dictionary = {}
        for key in list(self.news.keys()):
            dictionary[key] = self.news[key]
        np.save('news_dump.npy', dictionary)

    def load_dict_from_file(self):
        return np.load('news_dump.npy', allow_pickle='TRUE').item()


def main(opts):
    start_time = time.time()
    parser = Parser(url="https://news.ycombinator.com/", retries=opts.retries)
    parser.find_news()
    asyncio.run(parser.download_news())
    parser.save_to_file()
    finish_time = time.time() - start_time
    print(f"Затраченное на работу скрипта время: {finish_time} \n время завершения {datetime.datetime.now()}")


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-r", "--retries", default=3)
    op.add_option("-m", "--minutes", default=10)
    (opts, args) = op.parse_args()
    schedule.every(int(opts.minutes)).minutes.do(main, opts)

    while True:
        schedule.run_pending()
        time.sleep(1)
