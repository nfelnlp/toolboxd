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
    print(">>> {}".format(user))
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
        print("Found {} new logs..\n".format(new_num))
    else:
        print("No new logs.\n")


def check_ratings(user_folder, initial_retrieval_date):
    # Check if ratings have changed
    list_parts = []
    for user_csv in sorted(os.listdir('user/{}'.format(user_folder))):
        list_parts.append(pd.read_csv('user/{}/{}'.format(
            user_folder, user_csv), sep=r'\t', names=["title", user_folder],
            engine='python'))
        last_csv_date = user_csv.split('_')[-1].strip('.csv')
    db = pd.concat(list_parts, ignore_index=True).drop_duplicates(
        subset='title', keep='last').reset_index(drop=True)

    page_num = 1
    rating_time = '2018-04-30'
    while True:
        lb_url = 'http://letterboxd.com'
        with request.urlopen('{}/{}/films/ratings/page/{}'.format(
                lb_url, user_folder, page_num)) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')

            # Find all movie posters / links on this page
            movie_li = [lm for lm in soup.find_all(
                'li', class_='poster-container')]

            for mov in movie_li:
                # Retrieve metadata for each rating/movie
                rating_time = mov.find('time')['datetime'].split('T')[0]

                if rating_time < last_csv_date:
                    this_user_rating = mov.find(
                        'meta', itemprop='ratingValue')['content']
                    mov_str = mov.div['data-target-link'].split('/')[2]

                    # Check with database
                    try:
                        db_r = db[db['title'] == mov_str][user_folder].iloc[0]
                        if (
                                int(db_r) != int(this_user_rating)
                                and int(this_user_rating) != 0
                                and rating_time > initial_retrieval_date):
                            print("\tUpdated {} (Rating: {}), "
                                  "previous rating was {} in csv {}.".format(
                                    mov_str, this_user_rating, db_r,
                                    rating_time))
                            with open('user/{}/{}_{}.csv'.format(
                                    user_folder, user_folder, rating_time),
                                    'a+') as wcsv:
                                writer = csv.writer(wcsv, delimiter='\t',
                                                    quotechar='|',
                                                    quoting=csv.QUOTE_MINIMAL)
                                writer.writerow([mov_str, this_user_rating])

                    except IndexError:
                        print(mov_str)
                        print("\tDid not find this movie in the database. "
                              "Added with {} rating.".format(this_user_rating))
                        with open('user/{}/{}_{}.csv'.format(
                                user_folder, user_folder, rating_time),
                                'a+') as wcsv:
                            writer = csv.writer(wcsv, delimiter='\t',
                                                quotechar='|',
                                                quoting=csv.QUOTE_MINIMAL)
                            writer.writerow([mov_str, this_user_rating])

        page_num += 1
        if rating_time < initial_retrieval_date:
            break


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
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--from_user", help="your username",
                        default=None, type=str, dest='user')
    parser.add_argument("-c", "--check", help="double check existing ratings",
                        default=False, action="store_true", dest='check')
    args = parser.parse_args()

    date = datetime.date.today()
    ufile = 'your_username.txt'
    if os.path.isfile(ufile):
        user = open(ufile, 'r').read()

    if args.user is not None:
        user = args.user

    if not user:
        raise ValueError("No user specified.")
    else:
        print("Username: {}".format(user))

    network = traverse_network(user, date)

    for friend in reversed(network):
        print("")
        if not os.path.exists('user/{}'.format(friend)):
            os.makedirs('user/{}'.format(friend))
            print("Creating new folder and retrieving all ratings for\
                   {}...".format(friend))
            add_user_to_network(friend, 'films/by/date', date)

        else:
            update_user(friend, 'films/by/date', date)
            if args.check:
                # Get initial retrieval date
                ini_rd = sorted(list(os.listdir(
                    'user/{}'.format(
                        friend))))[0].strip('.csv').split('_')[-1]
                check_ratings(friend, ini_rd)
        print("___________")
