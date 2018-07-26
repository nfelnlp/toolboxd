import os
import argparse
import pandas as pd

from metadata import apply_meta_filters
from ratings import add_user_to_network


def clone(full_url):
    clones_dir = 'lists/cloned'
    if not os.path.exists(clones_dir):
        os.makedirs(clones_dir)

    if full_url.startswith('http'):
        full_url = full_url.split('.com/')[-1]
    user, list_str, url = full_url.split('/')
    add_user_to_network(user, "{}/{}".format(list_str, url),
                        save_dir=clones_dir, to_reverse=False)

    output_csv = "{}/{}.csv".format(clones_dir, url)
    print("Saved to {}".format(output_csv))
    return output_csv


def show(selected_file, cols, meta=False):
    df = pd.read_csv(selected_file, sep=r'\t', names=cols,
                     engine='python')
    if meta:
        df = apply_meta_filters(df)[["title", "year", "lrating", "llogs"]]
    print(df.to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-clone", help="clone a list from Letterboxd (URL as "
                        "argument)",
                        default=None, dest='clone')
    parser.add_argument("-f", "--file", help="csv file", default=None,
                        type=str, dest='f')
    parser.add_argument("-cols", help="columns in csv", nargs='+',
                        default=["title", "rating"], dest='cols')
    parser.add_argument("-m", "--meta", help="include metadata",
                        default=False, action='store_true', dest='meta')
    args = parser.parse_args()

    if args.clone:
        list_file = clone(args.clone)
    else:
        if args.f:
            list_file = args.f
        else:
            raise ValueError("No file specified.")
    show(list_file, args.cols, args.meta)
