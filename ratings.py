import sys
import csv
import datetime
import os
import time
import argparse
import pandas as pd
import urllib

from bs4 import BeautifulSoup
from urllib import request


def get_all_movies_from_page(user, list_title, save_dir='lists',
                             output_name=None, with_ratings=True,
                             to_reverse=True, create_meta_file=False,
                             return_path=False):
    if not output_name:
        output_name = list_title.replace('/', '_')

    full_path = '{}/{}/{}'.format(save_dir, user, output_name)
    with open("{}.csv".format(full_path), 'a+') as wcsv:
        writer = csv.writer(wcsv, delimiter='\t', quotechar='|',
                            quoting=csv.QUOTE_MINIMAL)
        page = 1
        while True:
            with request.urlopen('http://letterboxd.com/{}/{}/page/{}/'.format(
                    user, list_title, page)) as response:
                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')

                if create_meta_file:
                    with open('{}_META.html'.format(
                            full_path), 'w') as lmf:
                        lmf.write(soup.prettify())
                    create_meta_file = False

                # Find all movie posters / links on this page
                movie_li = [lm for lm in soup.find_all(
                    'li', class_='poster-container')]

                for mov in movie_li:
                    write_stuff = []

                    # Retrieve title
                    write_stuff.append(mov.div['data-target-link'].split(
                        '/')[2])

                    # Retrieve rating
                    if with_ratings:
                        write_stuff.append(mov['data-owner-rating'])

                    writer.writerow(write_stuff)

            print("\tPage {} : {} movies".format(page, len(movie_li)))
            try:
                last_page = soup.find_all(class_='paginate-page')[-1].text
                if page >= int(last_page):
                    break
                page += 1
                time.sleep(5)
            except IndexError:
                break

    if to_reverse:
        # Reverse csv
        print("\tReversing order of movies in csv...\n")
        filename = "{}.csv".format(full_path)
        temp_file = "{}.temp".format(filename)
        os.rename(filename, temp_file)

        with open(filename, 'w') as wf:
            with open(temp_file, 'r') as cf:
                lines = [x for x in cf]
                for line in lines[::-1]:
                    wf.write(line)
        os.remove(temp_file)

    if return_path:
        return full_path


def update_user(user, list_type, date):
    print(">> {}\n".format(user))
    files = sorted(os.listdir('user/{}/'.format(user)), reverse=True)
    recent_csv = 'user/{}/{}'.format(user, files[0])

    # Find out which movie was added with the last update
    with open(recent_csv, 'r') as rcsv:
        reader = csv.reader(rcsv, delimiter='\t', quotechar='|',
                            quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            last_addition = row[0]
            if str(last_addition).startswith('film:'):
                with request.urlopen('http://letterboxd.com/film/{}/'.format(
                        last_addition)) as response:
                    print("Retrieving new title for {} ...".format(
                        last_addition))
                    html = response.read()
                    soup = BeautifulSoup(html, 'html.parser')
                last_addition = soup.find(
                    'meta', property='og:url')['content'].split('/')[-2]

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
                time.sleep(1)

            for upd in reversed(new_additions):
                writer.writerow([upd[0], upd[1]])

    # Delete file if empty
    if os.stat(new_csv).st_size == 0:
        os.remove(new_csv)
    print("")


def check_ratings(user_folder, initial_retrieval_date):
    # Check if ratings have changed
    list_parts = []
    first_csv_date = None
    for user_csv in sorted(os.listdir('user/{}'.format(user_folder))):
        list_parts.append(pd.read_csv('user/{}/{}'.format(
            user_folder, user_csv), sep=r'\t', names=["title", user_folder],
            engine='python'))
        current_csv_date = user_csv.split('_')[-1].strip('.csv')
        if first_csv_date is None:
            first_csv_date = current_csv_date
        last_csv_date = current_csv_date
    db = pd.concat(list_parts, ignore_index=True).drop_duplicates(
        subset='title', keep='last').reset_index(drop=True)

    page_num = 1
    rating_time = first_csv_date
    while True:
        lb_url = 'http://letterboxd.com'
        with request.urlopen('{}/{}/films/ratings/page/{}'.format(
                lb_url, user_folder, page_num)) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')

            # Find all movie posters / links on this page
            movie_li = [lm for lm in soup.find_all(
                'li', class_='poster-container')]
            if len(movie_li) == 0:
                break

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
                            time.sleep(1)
                            print("\tUpdated {} (Rating: {}, "
                                  "previously: {}) in csv {}.".format(
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
                        time.sleep(1)
                        print("\tAdded {} (Rating: {}).".format(
                            mov_str, this_user_rating))
                        with open('user/{}/{}_{}.csv'.format(
                                user_folder, user_folder, rating_time),
                                'a+') as wcsv:
                            writer = csv.writer(wcsv, delimiter='\t',
                                                quotechar='|',
                                                quoting=csv.QUOTE_MINIMAL)
                            writer.writerow([mov_str, this_user_rating])

        page_num += 1
        if rating_time <= initial_retrieval_date:
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


def main(args):
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
        if args.contu:
            if friend != args.contu:
                continue
            else:
                args.contu = False
        if args.wait:
            time.sleep(int(args.wait))
        try:
            if not os.path.exists('user/{}'.format(friend)):
                print("_________________________\n")
                os.makedirs('user/{}'.format(friend))
                print("Creating new folder and retrieving all ratings for "
                      "{} ...".format(friend))
                get_all_movies_from_page(user=friend,
                                         list_title='films/by/date',
                                         save_dir='user',
                                         output_name="{}_{}".format(
                                            friend, date))

            else:
                if not args.new:
                    print("_________________________\n")
                    update_user(friend, 'films/by/date', date)
                    if args.check:
                        # Get initial retrieval date
                        ini_rd = sorted(list(os.listdir(
                            'user/{}'.format(
                                friend))))[0].strip('.csv').split('_')[-1]
                        check_ratings(friend, ini_rd)
        except urllib.error.HTTPError as err:
            print("TIMEOUT. The Letterboxd server can't handle that many "
                  "requests. Setting sleep timer inbetween users to 20s.\n")
            args.wait = 10
            last_folder = 'user/{}'.format(friend)
            last_folder_contents = os.listdir(last_folder)
            os.remove('{}/{}'.format(last_folder,
                                     sorted(list(last_folder_contents))[-1]))
            print("Removed unfinished file.")
            if len(last_folder_contents) == 0:
                os.rmdir(last_folder_contents)
                print("Removed empty user folder.")
            print("\nRestarting...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", help="your username",
                        default=None, type=str, dest='user')
    parser.add_argument("-c", help="double check existing ratings",
                        default=False, action="store_true", dest='check')
    parser.add_argument("-new", help="only retrieve new users",
                        default=False, action="store_true", dest='new')
    parser.add_argument("-w", help="sleep timer in seconds after each request",
                        default=1, type=int, dest='wait')
    parser.add_argument("-cont", help="continue at this user if code ran into "
                        "an error",
                        default=None, type=str, dest='contu')
    main(parser.parse_args())
