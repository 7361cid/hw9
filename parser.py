import json
import time
import requests
from bs4 import BeautifulSoup
import datetime
import csv


start_time = time.time()


def get_data():
    cur_time = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M")

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36"
    }

    url = "https://news.ycombinator.com/"

    response = requests.get(url=url, headers=headers)
    print(f"Log  {response} --- \n {response.text}")
    soup = BeautifulSoup(response.text, "html.parser")
    print(f"Log  {soup}")
    allNews = soup.find_all('tr', class_='athing')
    print(f"Log  allNews \n {allNews}")
    for news in allNews:
        # https://news.ycombinator.com/item?id=32624461  шаблон страницы с комментом
        print(f"Log  news \n {news} \n id {news['id']}")
  #  links = soup.find_all("a", class_="titlelink")
  #  print(f"Log  links \n {links}  \n {len(links)}")




def main():
    get_data()
    finish_time = time.time() - start_time
    print(f"Затраченное на работу скрипта время: {finish_time}")


if __name__ == '__main__':
    main()