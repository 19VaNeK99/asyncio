import requests
from bs4 import BeautifulSoup
import csv
import time
import asyncio

def b(s):
    s = list(s)
    while True:
        if s[0] != " " and s[0] != "\n" and s[0] != "\t":
            break
        del s[0]
    while True:
        if s[-1] != " " and s[-1] != "\n" and s[-1] != "\t":
            break
        del s[-1]

    str = ""
    for i in s:
        str+=i
    return str


def get_page(page):
    for i in range(3):
        try:
            return requests.get(f"https://www.banki.ru/services/responses/list/?page={page + 1}&isMobile=0")
        except (
                requests.ConnectionError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectTimeout,
        ) as e:
            print(i + 1, " попытка получить страницу провалилась, пытаюсь еще")
    print("ну не получилось, сорян")
    exit()

def get_review(link):
    for i in range(3):
        try:
            return requests.get("https://www.banki.ru" + link)
        except (
            requests.ConnectionError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout,
        ) as e:
            print(i + 1, " попытка получить отзыв провалилась, пытаюсь еще")
            print("проблема вот в этой ссылке:")
            print("https://www.banki.ru" + link)
    return None


async def get_all_lin_rev(r, rev_queue):
    soup = BeautifulSoup(r.text, 'lxml')
    body = soup.find_all("article", {"class": "responses__item"})
    for i in body:
        link = i.find("div", {"class": "responses__item__message"}).find("a")
        if not link:
            continue
        link = link['href']
        await rev_queue.put(get_review(link))


async def processing_rev(work_queue):
    while not work_queue.empty():
        review = await work_queue.get()
        if review is None:
            continue
        rev = BeautifulSoup(review.text, 'lxml')
        bank = b(rev.find("div", {"class": "header-h2 display-inline margin-right-x-small"}).text)
        title = b(list(rev.find("h0", {"class": "header-h0 response-page__title"}).text))
        score = rev.find("div", {
            "class": "flexbox flexbox--inline flexbox--row flexbox--gap_xsmall flexbox--align-items_baseline"})
        if score:
            score = score.find_all("span")
            if len(score) > 2:
                try:
                    score = int(score[1].text)
                except:
                    score = None
            else:
                score = None
        else:
            score = None
        text = b(rev.find("div", {
            "class": "article-text response-page__text markup-inside-small markup-inside-small--bullet"}).text)
        data = rev.find("time").text
        print(bank)
        s = [bank, title, str(score), text, data]
        with open("file.csv", "a", newline="", encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(s)

s = time.time()

with open("file.csv", "a", newline="",encoding='utf-8') as file:
    row = ["Банк", "Заголовок", "Оценка", "Текст","Дата"]
    writer = csv.writer(file, delimiter = ";")
    writer.writerow(row)


async def main():
    for page in range(2):
        r = get_page(page)

        rev_queue = asyncio.Queue()

        await asyncio.gather(
            asyncio.create_task(get_all_lin_rev(r, rev_queue)),
            asyncio.create_task(processing_rev(rev_queue)),
        )

        print(rev_queue)


if __name__ == "__main__":
    asyncio.run(main())

e = time.time()
print(e - s)

