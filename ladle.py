import os
import shutil
import time
import argparse
import pandas as pd

from datetime import datetime
from urllib import request
from bs4 import BeautifulSoup


def get_html(title, target_file, marker=""):
    print("=> {}\t{}".format(title, marker))
    with request.urlopen('http://letterboxd.com/film/{}/'.format(
                            title)) as response:
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')

        with open(target_file, 'w') as mdf:
            mdf.write(soup.prettify())


def save_html(df, min_rating=3.75, refresh=False, wait_secs=0):
    title = df["title"]

    if df["rating"] < min_rating:
        return

    target_dir = 'moviedata/{}'.format(title)
    target_file = '{}/{}.html'.format(target_dir, title)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

        get_html(title, target_file)
        if wait_secs > 0:
            time.sleep(wait_secs)

    else:
        # Re-download the html
        if refresh:
            last_mod = datetime.fromtimestamp(os.path.getmtime(
                target_file)).strftime("%Y-%m-%d")

            if last_mod < datetime.today().strftime('%Y-%m-%d'):
                # Create new sub directory for old html
                arch_dir = "{}/{}".format(target_dir, last_mod)
                os.makedirs(arch_dir, exist_ok=True)
                shutil.move(target_file, "{}/{}.html".format(arch_dir, title))
                get_html(title, target_file, marker="*")
            else:
                print("Already refreshed today!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--minr", help="minimum rating", default=3.75,
                        type=float, dest='minr')
    parser.add_argument("-f", "--file", help="csv file", default=None,
                        type=str, dest='f')
    parser.add_argument("-refresh", help="download again", default=False,
                        action="store_true", dest='refresh')
    parser.add_argument("-w", "--wait", help="sleep timer in seconds after "
                        "each request", default=0, type=int, dest='wait')
    parser.add_argument("-cols", help="columns in csv", nargs='+',
                        default=["title", "rating", "num_logs"], dest='cols')
    args = parser.parse_args()

    if args.f:
        selected_file = args.f
    else:
        files = os.listdir('lists')
        selected_file = "lists/{}".format(sorted(
                        [f for f in files if f.endswith('.csv')
                         and f.startswith('all_')])[-1])
        print("Add -f <path to file> to specify which file to take.\n")

    print("Using {} ...".format(selected_file))

    df = pd.read_csv(selected_file, sep=r'\t', names=args.cols,
                     engine='python')
    df.apply(save_html, min_rating=args.minr, refresh=args.refresh,
             wait_secs=args.wait, axis=1)
