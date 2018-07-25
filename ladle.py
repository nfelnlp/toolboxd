import os
import time
import pandas as pd
from urllib import request
from bs4 import BeautifulSoup


def save_html(df, min_rating=3.75, wait_secs=0):
    title = df["title"]

    if df["rating"] < min_rating:
        return

    if not os.path.exists('moviedata/{}'.format(title)):
        os.makedirs('moviedata/{}'.format(title))

        print("=> {}".format(title))
        with request.urlopen('http://letterboxd.com/film/{}/'.format(
                            title)) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')

            with open('moviedata/{}/{}.html'.format(title, title), 'w') as mdf:
                mdf.write(soup.prettify())

            if wait_secs > 0:
                time.sleep(wait_secs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--minr", help="minimum rating", default=3.75,
                        type=float, dest='minr')
    parser.add_argument("-f", "--file", help="csv file", default=None,
                        type=str, dest='f')
    parser.add_argument("-w", "--wait", help="sleep timer in seconds after "
                        "each request", default=0, type=int, dest='wait')
    args = parser.parse_args()

    if args.f:
        selected_file = args.f
    else:
        files = os.listdir('lists')
        selected_file = "lists/{}".format(sorted(
                        [f for f in files if f.endswith('.csv')
                         and f.startswith('all_')])[-1])
        print("Add *-f <path to file>* flag to specify which file to take.\n")

    print("Using {} ...".format(selected_file))

    df = pd.read_csv(selected_file, sep=r'\t',
                     names=["title", "rating", "num_logs"], engine='python')
    df.apply(save_html, min_rating=args.minr, wait_secs=args.wait, axis=1)
