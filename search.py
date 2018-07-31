# Search of a movie
# Get all metadata

import argparse
import pandas as pd

from metadata import get_movie_info


def search_db(query):
    ser = pd.Series()
    ser["title"] = query
    df = get_movie_info(ser)
    print(df.to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", help="query",
                        type=str, dest='q')
    args = parser.parse_args()

    search_db(args.q)
