import pandas as pd
import ast
import os
import datetime
import numpy as np
import argparse
from functools import reduce
from bs4 import BeautifulSoup
from urllib import request

from moviedata import get_movie_info


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
                      on_watchlist=None, metadata=True, min_year=None,
                      max_year=None, genre=None, nx_filter=False):
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

    if metadata:
        # Retrieve all the metadata
        df = df.apply(get_movie_info, axis=1)

        # Remove NaN-year entries
        df = df.dropna(subset=['year'], how='any')
        df["year"] = df["year"].apply(int)

        # Filter by year
        if min_year or max_year:
            df = df.loc[(df["year"] >= min_year) & (df["year"] <= max_year)]

        # Filter by genre
        if genre:
            df = df.loc[df["genres"].apply(lambda x: genre in x)]

        # Sort/Filter by LB avg/logs
        # df = df.loc[df["lb_rating"] > 3.3]
        # df = df.loc[(df["lb_logs"] < 10000) & (df["lb_logs"] > 1000)]
        # df = df.sort_values("lb_logs")

        if nx_filter:
            flixable_list = list(filter(None,
                                 set(open('netflix/flixable_all.txt',
                                          'r').read().split('\n'))))
            df = df.loc[df["IMDb_ID"].isin(flixable_list)]

        # Select columns
        df = df[["title", "year", "nw_rating", "nw_logs", "lb_rating",
                 "lb_logs", "genres"]]

    else:
        df = df[["title", "nw_rating", "nw_logs"]]

    return df


if __name__ == "__main__":
    today = datetime.date.today()

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--b_weighting", help="bayesian weighting",
                        default=None, type=float, dest='bw')
    parser.add_argument("-m", "--meta", help="metadata", default=False,
                        action='store_true', dest='meta')
    parser.add_argument("-r", "--minr", help="min_rating", default=3.75,
                        type=float, dest='minr')
    parser.add_argument("-w", "--watched", help="y/n", default=None,
                        type=str, dest='watched')
    #parser.add_argument("-ow", "--on_watchlist", help="y/n", default=None,
    #                    type=str, dest='ow')
    parser.add_argument("-miny", "--min_year", help="min_year", default=1890,
                        type=int, dest='miny')
    parser.add_argument("-maxy", "--max_year", help="max_year", default=2020,
                        type=int, dest='maxy')
    parser.add_argument("-g", "--genre", help="genre", default=None,
                        type=str, dest='genre')
    parser.add_argument("-o", "--out", help="output format (csv/net),\
                        None prints to terminal (by default)", default=None,
                        type=str, dest='out')
    parser.add_argument("-d", "--date",
                        help="date (up to when ratings should be considered)",
                        default=today, type=str, dest='dt')
    #parser.add_argument("-nx", "--netflix_filter", default=False,
    #                    action='store_true', dest='nx')
    # TODO
    # min_logs, max_logs, min_lbr

    args = parser.parse_args()

    if (args.out == 'net') or (args.genre):
        args.meta = True
    if args.minr < 3.3:
        args.meta = False

    df = collect_from_users(args.dt)
    df = summarize_ratings(df, weighting=args.bw, min_rating=args.minr,
                           watched=args.watched, on_watchlist=args.ow,
                           metadata=args.meta, min_year=args.miny,
                           max_year=args.maxy, genre=args.genre,
                           nx_filter=args.nx)

    write_list_to_csv_or_txt(df, args.dt, output_format=args.out)
