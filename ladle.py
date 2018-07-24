import os
import pandas as pd
from urllib import request
from bs4 import BeautifulSoup


def save_html(df, min_rating=3.75):
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


if __name__ == "__main__":
    mdir = 'lists'
    files = os.listdir(mdir)
    latest = sorted([f for f in files if f.endswith('.csv')
                    and f.startswith('all_')])[-1]
    print("Using {}".format(latest))

    df = pd.read_csv("{}/{}".format(mdir, latest),
                     sep=r'\t', names=["title", "rating", "num_logs"],
                     engine='python')
    df.apply(save_html, axis=1)
