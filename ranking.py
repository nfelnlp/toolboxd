import pandas as pd
import ast
import os
import datetime
import numpy as np
import argparse
from functools import reduce
from bs4 import BeautifulSoup
from urllib import request

from meta_filters import apply_meta_filters, apply_sorting


def calculate_avg(ratings, minimum, mean_total=0, mode="std"):
    # Remove 0 ratings
    ratings = [x for x in ratings if x != 0]

    if len(ratings) == 0:
        return None
    else:
        votes = len(ratings)
        rating = sum(ratings)/votes
        if mode == "std":
            return rating/2

        elif mode == "bayesian":
            return round(((votes / (votes + minimum)) * rating
                         + (minimum / (votes + minimum))
                         * mean_total)/2, 2)


def collect_from_users(changes_from):
    try:
        changes_from = datetime.datetime.strptime(changes_from, '%Y-%m-%d')
    except TypeError:
        cf = changes_from
        changes_from = datetime.datetime(cf.year, cf.month, cf.day)

    network = os.listdir('user')
    network_dfs = []

    for user_folder in network:
        list_parts = []
        for user_csv in sorted(os.listdir('user/{}'.format(user_folder))):
            if datetime.datetime.strptime(
                    user_csv.strip('.csv').split('_')[-1],
                    '%Y-%m-%d') <= changes_from:
                list_parts.append(pd.read_csv(
                    'user/{}/{}'.format(user_folder, user_csv), sep=r'\t',
                    names=["title", user_folder], engine='python'))
        try:
            user_films = pd.concat(
                list_parts, ignore_index=True).drop_duplicates(
                subset='title', keep='last').reset_index(drop=True)
            network_dfs.append(user_films)
        except ValueError:
            print("No entries for {}".format(user_folder))

    return reduce(lambda left, right: pd.merge(left, right, on='title',
                                               how='outer'), network_dfs)


def write_list_to_csv_or_txt(df, date, output_format=None):
    if output_format == 'net':
        filename = 'lists/network_{}.csv'.format(date)
        df[["title", "year", "nw_rating"]].to_csv(
            filename, sep=',', index=False)
        print("Created Letterboxd-importable file {}.".format(filename))
    elif output_format == 'csv':
        filename = 'lists/all_{}.csv'.format(date)
        df[["title", "nw_rating", "nw_logs"]].to_csv(
            filename, sep='\t', index=False,
            header=False)
        print("Created csv file {}.".format(filename))
    else:
        print(df.to_string())


def add_rating_difference(df):
    df["diff"] = df.apply(lambda x: x["nw_rating"] - x["lb_rating"], axis=1)
    return df.sort_values("diff", ascending=False)


def summarize_ratings(df, weighting=None, min_rating=3.75, watched=None,
                      on_watchlist=None):
    default_user = open('your_username.txt', 'r').read()

    if watched == "y":
        df = df.loc[df[default_user].notnull()]
    elif watched == "n":
        df = df.loc[df[default_user].isnull()]

    #if on_watchlist == "y":
    #    df = df.loc[df["_WL_nfel"].notnull()]
    #elif on_watchlist == "n":
    #    df = df.loc[df["_WL_nfel"].isnull()]

    #df = df.drop(["_WL_nfel"], axis=1)  # Leave out watchlist
    df = df.drop([default_user], axis=1)  # Leave out own rating

    df["ratings"] = df.drop(["title"], axis=1).values.tolist()
    df["ratings"] = df["ratings"].apply(
        lambda y: [int(a) for a in y if pd.notnull(a)])
    df["nw_logs"] = df["ratings"].apply(len)

    if weighting:
        b_weighting = weighting
    else:
        b_weighting = 1/100 * len(df.drop(["title", "nw_logs", "ratings"],
                                          axis=1).keys())

    df["avg"] = df["ratings"].apply(calculate_avg, minimum=b_weighting,
                                    mode="bayesian")

    mean_total = df["avg"].mean()
    df["nw_rating"] = df["ratings"].apply(calculate_avg, minimum=b_weighting,
                                          mean_total=mean_total,
                                          mode="bayesian")
    # Tiebreaker for sorting
    df = df[["title", "nw_rating", "nw_logs"]].sort_values("nw_logs",
                                                           ascending=False)

    # Sort by rating of network
    df = df.sort_values("nw_rating", ascending=False)

    # Filter by rating
    df = df[df["nw_rating"] > min_rating]

    # Clean up
    df = df.drop_duplicates(subset=["title"])

    return df


if __name__ == "__main__":
    today = datetime.date.today()

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--b_weighting", help="bayesian weighting",
                        default=None, type=float, dest='bw')
    parser.add_argument("-r", "--minr", help="min_rating", default=3.75,
                        type=float, dest='minr')
    parser.add_argument("-w", "--watched", help="y/n", default=None,
                        type=str, dest='watched')
    parser.add_argument("-ow", "--on_watchlist", help="y/n", default=None,
                        type=str, dest='ow')
    parser.add_argument("-o", "--out", help="output format (csv/net),\
                        None prints to terminal (by default)", default=None,
                        type=str, dest='out')
    parser.add_argument("-d", "--date",
                        help="date (up to when ratings should be considered)",
                        default=today, type=str, dest='dt')

    # Metadata flags
    parser.add_argument("-m", "--meta", help="metadata", default=False,
                        action='store_true', dest='meta')
    parser.add_argument('-lbr', "--min_lb_rating",
                        help="minimum rating on LB", default=None,
                        type=float, dest='lbr')
    parser.add_argument('-minlbl', "--min_lb_logs",
                        help="minimum number of logs on LB", default=None,
                        type=int, dest='minlbl')
    parser.add_argument('-maxlbl', "--max_lb_logs",
                        help="maximum number of logs on LB", default=None,
                        type=int, dest='maxlbl')
    parser.add_argument("-miny", "--min_year", help="earliest year",
                        default=1890, type=int, dest='miny')
    parser.add_argument("-maxy", "--max_year", help="latest year",
                        default=2020, type=int, dest='maxy')
    parser.add_argument("-mint", "--min_runtime", help="minimum runtime",
                        default=None, type=int, dest='mint')
    parser.add_argument("-maxt", "--max_runtime", help="maximum runtime",
                        default=None, type=int, dest='maxt')
    parser.add_argument("-g", "--genre", help="filter by genre", default=None,
                        type=str, dest='gen')
    parser.add_argument("-ac", "--actor", help="filter by actor",
                        default=None, type=str, dest='ac')
    parser.add_argument("-di", "--director", help="filter by director",
                        default=None, type=str, dest='di')
    parser.add_argument("-pro", "--producer", help="filter by producer",
                        default=None, type=str, dest='pro')
    parser.add_argument("-wr", "--writer", help="filter by writer",
                        default=None, type=str, dest='wr')
    parser.add_argument("-ed", "--editor", help="filter by editor",
                        default=None, type=str, dest='ed')
    parser.add_argument("-ci", "--cinematography",
                        help="filter by cinematography",
                        default=None, type=str, dest='ci')
    parser.add_argument("-com", "--composer", help="filter by composer",
                        default=None, type=str, dest='com')
    parser.add_argument("-stu", "--studio", help="filter by studio",
                        default=None, type=str, dest='stu')
    parser.add_argument("-cou", "--country", help="filter by country",
                        default=None, type=str, dest='cou')
    parser.add_argument("-lang", "--language", help="filter by language",
                        default=None, type=str, dest='lang')

    # Sorting flags
    # TODO

    args = parser.parse_args()

    df = collect_from_users(args.dt)
    df = summarize_ratings(df, weighting=args.bw, min_rating=args.minr,
                           watched=args.watched, on_watchlist=args.ow)

    if args.meta:
        df = apply_meta_filters(df, min_lb_rating=args.lbr,
                                min_lb_logs=args.minlbl,
                                max_lb_logs=args.maxlbl,
                                min_year=args.miny, max_year=args.maxy,
                                min_runtime=args.mint, max_runtime=args.maxt,
                                genre=args.gen, actor=args.ac,
                                director=args.di, producer=args.pro,
                                writer=args.wr, editor=args.ed,
                                cinematography=args.ci, composer=args.com,
                                studio=args.stu, country=args.cou,
                                language=args.lang)
        # Select columns
        df = df[["title", "year", "nw_rating", "nw_logs", "lb_rating",
                 "lb_logs"]]
    else:
        df = df[["title", "nw_rating", "nw_logs"]]

    write_list_to_csv_or_txt(df, args.dt, output_format=args.out)
