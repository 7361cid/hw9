import json
import time
import requests
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
        print(f"Log  {soup}")
        all_news = soup.find_all('tr', class_='athing')
        for news in all_news:
            # https://news.ycombinator.com/item?id=32624461  шаблон страницы с комментом
            print(f"Log  news \n {news} \n id {news['id']}")
            print(f"Log  news2 \n {news.contents[4].a['href']}  {type(news.contents[4])} \n")
            news_title = news.text
            url = news.contents[4].a['href']
            self.news[news_title] = {"news_url": url, "id": news['id'],
                                     "comment_url": f"https://news.ycombinator.com/item?id={news['id']}"}
            print(self.news.keys())

    def download_news(self, news_title):
        """
        Скачивание новости: контент новости, страница комментариев, ссылки в комментариях
        """
        news = self.news[news_title]
        news_page_response = requests.get(url=news["news_url"], headers=self.headers)
        news["content"] = news_page_response.text
        news_comment_response = requests.get(url=news["comment_url"], headers=self.headers)
        news["comment_page_content"] = news_comment_response.text
        soup = BeautifulSoup(news_comment_response.text, "html.parser")
        all_tags_a_from_comments = soup.find_all('a')
        all_links_from_comments = []
        for tag in all_tags_a_from_comments:
            href = tag["href"]
            if "http" in href:
                all_links_from_comments.append(href)
        print(f"Log all_links_from_comments {all_links_from_comments}")

    def save_to_file(self):
        json.dump(self.news, open("dump.json", 'w'))


def main():
    parser = Parser(url="https://news.ycombinator.com/")
    parser.find_news()
    parser.download_news(news_title=list(parser.news.keys())[0])
    parser.save_to_file()
    finish_time = time.time() - start_time
    print(f"Затраченное на работу скрипта время: {finish_time}")


if __name__ == '__main__':
    main()
