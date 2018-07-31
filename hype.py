import csv
import os
import argparse
import pandas as pd
from functools import reduce

from metadata import apply_meta_filters


def compare_csvs(old_csv, new_csv, flags):
    old_df = pd.read_csv(old_csv, sep=r'\t',
                         names=["title", "nrating", "nlogs"],
                         dtype={"nrating": float, "nlogs": int},
                         engine='python')
    new_df = pd.read_csv(new_csv, sep=r'\t',
                         names=["title", "nrating", "nlogs"],
                         dtype={"nrating": float, "nlogs": int},
                         engine='python')

    df = reduce(lambda left, right: pd.merge(left, right,
                on='title', how='left'), [old_df, new_df])

    # Add new columns for comparison
    df["cir"] = df["nrating_y"] - df["nrating_x"]
    df["plus_logs"] = df["nlogs_y"] - df["nlogs_x"]

    # Filter for "popular": 2 or more new logs
    if 'popular' in flags:
        df = df.loc[df["nlogs_y"] - df["nlogs_x"] >= 2]

    # Drop columns from old csv and rename those from new csv
    df = df.drop(['nrating_x', 'nlogs_x'], axis=1)
    df.columns = ['title', 'nrating', 'nlogs', 'cir', 'plus_logs']

    # Filter for "rising": Above 3.00 rating and +0.15 in rating
    if 'rising' in flags:
        df = df.loc[df["nrating"] > 3]
        df = df.loc[df["cir"] > 0.15]

    # Filter for "top": Sort by network rating and take top 20
    if 'top' in flags:
        df = df.sort_values("nrating", ascending=False)
        df = df.head(20)

    df = apply_meta_filters(df)
    # Select columns
    # TODO: Enable more columns from metadata?
    df = df[['title', 'year', 'nrating', 'nlogs', 'cir', 'plus_logs']]

    # Sorting for "rising": By change in rating, descending order
    if 'rising' in flags:
        df = df.sort_values("cir", ascending=False)
        print("Rising:\n")
        print(df.to_string())

    # Sorting for "popular": By number of new logs, descending order
    if 'popular' in flags:
        df = df.sort_values("plus_logs", ascending=False)
        print("Popular (multiple users have logged this movie since "
              "last time):\n")
        print(df.to_string())

    if 'top' in flags:
        print("Top 20 movies and their movement:\n")
        print(df.to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-old", help="old csv file",
                        default=None, type=str, dest='old')
    parser.add_argument("-new", help="new csv file",
                        default=None, type=str, dest='new')
    parser.add_argument("-flags", help="list selection\nOptions:\n"
                        "popular , rising , top",
                        nargs='*', default=['rising'], dest='flags')
    args = parser.parse_args()

    list_folder = 'lists'
    all_files = sorted([f for f in os.listdir(
        list_folder) if f.endswith('.csv')])
    if not args.old:
        old_csv = "{}/{}".format(list_folder, all_files[-2])
    else:
        old_csv = args.old
    if not args.new:
        new_csv = "{}/{}".format(list_folder, all_files[-1])
    else:
        new_csv = args.new
    print("Using {} and {} ...\n".format(old_csv, new_csv))
    compare_csvs(old_csv, new_csv, args.flags)
