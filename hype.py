import csv
import os
import argparse
import pandas as pd
from functools import reduce


def compare_csvs(old_csv, new_csv, folder='all'):
    if folder == 'all':
        old_df = pd.read_csv(old_csv, sep=r'\t',
                             names=["title", "nw_rating", "nw_logs"],
                             engine='python')
        new_df = pd.read_csv(new_csv, sep=r'\t',
                             names=["title", "nw_rating", "nw_logs"],
                             engine='python')

        changes_df = reduce(lambda left, right: pd.merge(left, right,
                            on='title', how='outer'), [old_df, new_df])
        changes_df["diff"] = (changes_df["nw_rating_y"]
                              - changes_df["nw_rating_x"])

        changes_df = changes_df.loc[changes_df["nw_rating_y"] > 3]

        changes_df = changes_df.sort_values(
            "diff", ascending=False).loc[changes_df["diff"] != 0.00]

        popular_df = (changes_df.loc[changes_df["nw_logs_y"]
                      - changes_df["nw_logs_x"] > 1])

        changes_df = changes_df.loc[abs(changes_df["diff"]) > 0.05]

        print("Biggest changes (diff) of more than 0.05 in either "
              "direction for movies above 3.00:\n")
        print(changes_df.to_string())
        print("\n________________________________________\n\n")
        print("Popular movies (multiple users have logged this movie since "
              "last time:\n")
        print(popular_df.to_string())

    elif folder == 'network':
        old_df = pd.read_csv(old_csv, sep=r',', engine='python')
        new_df = pd.read_csv(new_csv, sep=r',', engine='python')

        prev_top = old_df.head(20)

        changes_df = reduce(lambda left, right: pd.merge(left, right,
                            on=['title', 'year'], how='outer'),
                            [old_df, new_df])
        changes_df["diff"] = (changes_df["nw_rating_y"]
                              - changes_df["nw_rating_x"])
        changes_df = changes_df.sort_values("diff", ascending=False)

        rising_df = changes_df.loc[changes_df["diff"] >= 0.15]
        falling_df = changes_df.loc[changes_df["diff"] <= -0.1].sort_values(
            "diff", ascending=True)
        entries_df = changes_df.loc[(changes_df["nw_rating_x"].isnull())
                                    & (changes_df["nw_rating_y"] >= 3.6)]
        out_df = changes_df.loc[(changes_df["nw_rating_y"].isnull())
                                & (changes_df["nw_rating_x"] >= 3.75)]

        descr_file = "{}.txt".format(new_csv.split('/')[-1].strip('.csv'))
        print("Writing to {}".format(descr_file))
        with open('network/descr/{}'.format(descr_file), 'w') as ds:
            ds.write("Previous top 20:\n")
            ds.write(prev_top[["title", "year"]].to_string(index=False))
            ds.write("\n\nRising:\n")
            ds.write(rising_df[["title", "year"]].to_string(index=False))
            ds.write("\n\nFalling:\n")
            ds.write(falling_df[["title", "year"]].to_string(index=False))
            ds.write("\n\nNew entries:\n")
            ds.write(entries_df[["title", "year"]].to_string(index=False))
            ds.write("\n\nOut:\n")
            ds.write(out_df[["title", "year"]].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--folder", help="list folder",
                        default='lists', type=str, dest='lf')
    args = parser.parse_args()
    list_folder = args.lf
    all_files = sorted([f for f in os.listdir(
        list_folder) if f.endswith('.csv')])
    latest = "{}/{}".format(list_folder, all_files[-1])
    to_compare = "{}/{}".format(list_folder, all_files[-2])
    compare_csvs(to_compare, latest, folder='all')
