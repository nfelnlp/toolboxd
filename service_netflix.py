import argparse
import os
import time
from bs4 import BeautifulSoup
from urllib import request


nx_dir = 'lists/netflix'


def get_flixable(page_num=1):
    params = "?min-rating=0&min-year=1920&max-year=2018&order=date"

    while True:
        flixable_list = []
        with request.urlopen(
            'http://de.flixable.com/genre/filme/{}&page={}'.format(
                params, page_num)) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')

            links = soup.find_all('a')
            this_pages_movies = []
            for li in links:
                if li['href'].startswith('/title'):
                    this_pages_movies.append(li)

            for mov in set(this_pages_movies):
                imdb_id = get_imdb_id(mov['href'])
                if imdb_id:
                    if imdb_id != "":
                        flixable_list.append(imdb_id)
        flixable_list = set(flixable_list)

        if len(flixable_list) == 0:
            break

        with open('{}/flixable.txt'.format(nx_dir), 'a+') as wf:
            for mov in flixable_list:
                wf.write(str(mov) + '\n')
        time.sleep(1)
        print(page_num)
        page_num += 1


def get_imdb_id(mov):
    with request.urlopen("http://de.flixable.com{}".format(mov)) as response:
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')

        imdb_plg = soup.find('span', class_="imdbRatingPlugin")
        if imdb_plg:
            time.sleep(1)
            imdb_ref = imdb_plg.find('a')['href']
            return (imdb_ref.split('/title/')[1]).split('/?')[0]


########
# LEAVING
# UPDATE
########


if __name__ == "__main__":
    get_flixable()
