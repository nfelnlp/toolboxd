import sys
import csv
import datetime
import os
import argparse
import pandas as pd
from bs4 import BeautifulSoup
from urllib import request


def add_user_to_network(user, list_type, date, user_path=None):
    with request.urlopen('http://letterboxd.com/{}/{}/'.format(
            user, list_type)) as response:
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        # How many pages has the watchlist
        try:
            last_page_num = soup.find_all(class_='paginate-page')[-1].text
        except IndexError:
            last_page_num = 1

    if not user_path:
        user_path = 'user/{}'.format(user)
    with open('{}/{}_{}.csv'.format(user_path, user, date), 'a+') as wcsv:
        writer = csv.writer(wcsv, delimiter='\t', quotechar='|',
                            quoting=csv.QUOTE_MINIMAL)
        for page in range(1, int(last_page_num)+1):
            with request.urlopen('http://letterboxd.com/{}/{}/page/{}/'.format(
                    user, list_type, page)) as response:
                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')

                # Find all movie posters / links on this page
                movie_li = [lm for lm in soup.find_all(
                    'li', class_='poster-container')]

                for mov in movie_li:
                    this_user_rating = mov['data-owner-rating']

                    # Retrieve metadata for each movie
                    mov_str = mov.div['data-target-link'].split('/')[2]

                    writer.writerow([mov_str, this_user_rating])

            print("\tPage {} : {} movies".format(page, len(movie_li)))

    # Reverse csv
    print("Reversing order of movies in csv...\n")
    files = os.listdir(user_path)

    filename = "{}/{}".format(user_path, files[0])
    os.rename(filename, "{}.temp".format(filename))

    old_csv = "{}/{}".format(user_path, (os.listdir(user_path))[0])

    with open(filename, 'w') as wf:
        with open(old_csv, 'r') as cf:
            lines = [x for x in cf]
            for line in lines[::-1]:
                wf.write(line)
    os.remove(old_csv)


def update_user(user, list_type, date):
    files = sorted(os.listdir('user/{}/'.format(user)), reverse=True)
    recent_csv = 'user/{}/{}'.format(user, files[0])

    # Find out which movie was added with the last update
    with open(recent_csv, 'r') as rcsv:
        reader = csv.reader(rcsv, delimiter='\t', quotechar='|',
                            quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            last_addition = row[0]

    new_csv = 'user/{}/{}_{}.csv'.format(user, user, date)
    with open(new_csv, 'a+') as wcsv:
        writer = csv.writer(wcsv, delimiter='\t', quotechar='|',
                            quoting=csv.QUOTE_MINIMAL)

        with request.urlopen('http://letterboxd.com/{}/{}/'.format(
                user, list_type)) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')

            # Find all movie posters / links on this page
            movie_li = [lm for lm in soup.find_all(
                'li', class_='poster-container')]

            new_num = 0
            new_additions = []
            for mov in movie_li:
                # Retrieve metadata for each movie
                this_user_rating = mov['data-owner-rating']
                mov_str = mov.div['data-target-link'].split('/')[2]

                # If the current movie is already in the csv, cancel here
                if last_addition == mov_str:
                    break

                new_additions.append((mov_str, this_user_rating))
                print("\tAdded {} (Rating: {}).".format(
                    mov_str, this_user_rating))
                new_num += 1

            for upd in reversed(new_additions):
                writer.writerow([upd[0], upd[1]])

    # Delete file if empty
    if os.stat(new_csv).st_size == 0:
        os.remove(new_csv)

    if new_num > 0:
        print("Found {} new movies for {}.\n".format(new_num, user))
        # os.rename(recent_csv, 'user/{}/{}_{}.csv'.format(user, user, date))
    else:
        print("Checked {}. No changes.\n".format(user))


def traverse_network(from_user, date, start=None):
    # Get a list of all users in network
    friends = [from_user]
    page_num = 1
    while True:
        if start is not None:
            page_num = start
        with request.urlopen(
                'http://letterboxd.com/{}/following/page/{}/'.format(
                    from_user, page_num)) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')

            friends += [lm['href'].strip('/') for lm in soup.find_all(
                'a', class_='avatar -a40')]
            if not soup.find('a', class_='next'):
                break
        page_num += 1
    return friends


if __name__ == "__main__":
    date = datetime.date.today()

    ufile = 'your_username.txt'
    if not os.path.isfile(ufile):
        parser = argparse.ArgumentParser()
        parser.add_argument("-u", "--from_user", help="your username",
                            required=True, type=str, dest='user')
        args = parser.parse_args()
        network = traverse_network(args.user, date)
    else:
        network = traverse_network(open(ufile, 'r').read(), date)

    for friend in reversed(network):
        if not os.path.exists('user/{}'.format(friend)):
            os.makedirs('user/{}'.format(friend))
            print("Creating new folder and retrieving all ratings for\
                   {}...".format(friend))
            add_user_to_network(friend, 'films/by/date', date)

        else:
            update_user(friend, 'films/by/date', date)
