import os
import pandas as pd
import time

from bs4 import BeautifulSoup


def apply_imdb_filter(df, service):
    print("Reading IMDb IDs from {} file...".format(service))

    # NETFLIX
    if service == "netflix":
        content = open('lists/netflix/flixable.txt', 'r').read()
        ids = set(content.split('\n'))

    # AMAZON PRIME
    elif service == "prime":
        ids = []
        read_dir = 'lists/prime/imdb_index'
        for idf in os.listdir(read_dir):
            ids += [line.rstrip('\n') for line in open(
                '{}/{}'.format(read_dir, idf))]

    # VDFKINO
    elif service == "vdf":
        csv_dir = 'lists/vdfkino/csvs'
        parts = []
        for cf in os.listdir(csv_dir):
            parts.append(pd.read_csv("{}/{}".format(csv_dir, cf),
                         usecols=["imdbID"], engine='python').dropna())
        ydf = pd.concat(parts, ignore_index=True)
        ids = ydf["imdbID"].tolist()

    return df.loc[df.apply(lambda x: x["imdbID"] in ids, axis=1)]
