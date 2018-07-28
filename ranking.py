import pandas as pd
import ast
import os
import datetime
import numpy as np
import argparse
from functools import reduce
from bs4 import BeautifulSoup
from urllib import request

from clone_list import clone
from metadata import apply_meta_filters
from sorting import apply_sorting


def collect_logs_from_users(changes_from):
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


def apply_filters(df, watched=None, keep_own=False, list_filter=None):
    default_user = open('your_username.txt', 'r').read()

    # Watched filter
    if watched == "y":
        df = df.loc[df[default_user].notnull()]
    elif watched == "n":
        df = df.loc[df[default_user].isnull()]

    # Leave out own rating
    if not keep_own:
        df = df.drop([default_user], axis=1)

    if list_filter:
        if list_filter.startswith('http'):
            print("Cloning list from Letterboxd...")
            list_csv = clone(list_filter, return_filename=True)
        else:
            list_csv = list_filter
        list_df = pd.read_csv(list_csv, sep=r'\t', usecols=["title"],
                              names=["title"], engine='python')
        df = pd.merge(df, list_df, on='title', how='right')
    return df


def calculate_avg(ratings, minimum=0, mean_total=0, mode="std"):
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


def summarize_ratings(df, min_rating=3.75,
                      rating_mode="bayesian", weighting=None):
    # Generate ratings lists and number of logs in network
    df["ratings"] = df.drop(["title"], axis=1).values.tolist()
    df["ratings"] = df["ratings"].apply(
        lambda y: [int(a) for a in y if pd.notnull(a)])
    df["nlogs"] = df["ratings"].apply(len)

    # Rating mode (average / bayesian)
    if rating_mode == "bayesian":
        if weighting:
            b_weighting = weighting
        else:
            b_weighting = 1/100 * len(df.drop(["title", "nlogs", "ratings"],
                                              axis=1).keys())
        df["avg"] = df["ratings"].apply(calculate_avg, minimum=b_weighting,
                                        mode=rating_mode)
        mean_total = df["avg"].mean()

        df["nrating"] = df["ratings"].apply(calculate_avg,
                                            minimum=b_weighting,
                                            mean_total=mean_total,
                                            mode=rating_mode)
    elif rating_mode == "std":
        df["nrating"] = df["ratings"].apply(calculate_avg,
                                            mode=rating_mode)
    else:
        raise ValueError("No valid rating mode")

    # Filter by rating
    df = df[df["nrating"] > min_rating]

    # Clean up: Remove duplicates, select columns
    df = df[["title", "nrating", "nlogs"]].drop_duplicates(subset=["title"])

    return df


def write_list_to_csv_or_txt(df, date, output_format=None):
    if output_format == 'net':
        filename = 'lists/network_{}.csv'.format(date)
        df[["title", "year", "nrating"]].to_csv(
            filename, sep=',', index=False)
        print("Created Letterboxd-importable file {}.".format(filename))
    elif output_format == 'csv':
        filename = 'lists/all_{}.csv'.format(date)
        df[["title", "nrating", "nlogs"]].to_csv(
            filename, sep='\t', index=False,
            header=False)
        print("Created csv file {}.".format(filename))
    else:
        print(df.to_string())


if __name__ == "__main__":
    today = datetime.date.today()

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--minr", help="minimum rating",
                        default=3.75, type=float, dest='minr')
    parser.add_argument("-w", "--watched", help="exclude films you watched (n)"
                        " | only consider films you watched (y)",
                        default=None, type=str, dest='watched')
    parser.add_argument("-keep_own", help="keep your own rating for averaging",
                        default=False, action='store_true', dest='keep_own')
    parser.add_argument("-list", help="filter by cloned or created list",
                        default=None, type=str, dest='lf')
    parser.add_argument("-mode", "--rating_mode",
                        help="average or bayesian average rating mode",
                        default="bayesian", type=str, dest='mode')
    parser.add_argument("-b", "--b_weighting",
                        help="bayesian average weighting",
                        default=None, type=float, dest='bw')
    parser.add_argument("-o", "--out", help="output format (csv/net),\
                        None prints to terminal (by default)",
                        default=None, type=str, dest='out')
    parser.add_argument("-d", "--date",
                        help="date (up to when ratings should be considered)",
                        default=today, type=str, dest='dt')

    # Metadata flags
    parser.add_argument("-m", "--meta", help="include metadata",
                        default=False, action='store_true', dest='meta')
    parser.add_argument('-lbr', "--min_lb_rating",
                        help="minimum rating on LB",
                        default=0, type=float, dest='lbr')
    parser.add_argument('-min_llogs', "--min_llogs",
                        help="minimum number of logs on LB",
                        default=0, type=int, dest='min_llogs')
    parser.add_argument('-max_llogs', "--max_llogs",
                        help="maximum number of logs on LB",
                        default=10000000, type=int, dest='max_llogs')
    parser.add_argument("-miny", "--min_year", help="earliest year",
                        default=1890, type=int, dest='miny')
    parser.add_argument("-maxy", "--max_year", help="latest year",
                        default=2020, type=int, dest='maxy')
    parser.add_argument("-mint", "--min_runtime", help="minimum runtime",
                        default=0, type=int, dest='mint')
    parser.add_argument("-maxt", "--max_runtime", help="maximum runtime",
                        default=10000, type=int, dest='maxt')

    parser.add_argument("-g", "--genre", help="filter by genre",
                        default=None, type=str, dest='gen')
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
    parser.add_argument("-sort", help="sorting the resulting list\n"
                        "Default: nrating (network rating), nlogs "
                        "(how many of your friends logged it)",
                        nargs='*', default=['nrating', 'nlogs'], dest='sorts')
    # Column selection flags
    parser.add_argument("-cols", help="selected columns to display in list\n"
                        "Default: [title, year]\n"
                        "Look up README.md for all options",
                        nargs='+', dest='cols')

    args = parser.parse_args()

    # Get ratings
    df = collect_logs_from_users(args.dt)
    df = apply_filters(df,
                       watched=args.watched, keep_own=args.keep_own,
                       list_filter=args.lf)

    # Calculate network ratings
    df = summarize_ratings(df,
                           min_rating=args.minr, rating_mode=args.mode,
                           weighting=args.bw)

    if args.meta:
        df = apply_meta_filters(df,
                                min_lrating=args.lbr,
                                min_llogs=args.min_llogs,
                                max_llogs=args.max_llogs,
                                min_year=args.miny, max_year=args.maxy,
                                min_runtime=args.mint, max_runtime=args.maxt,
                                genre=args.gen, actor=args.ac,
                                director=args.di, producer=args.pro,
                                writer=args.wr, editor=args.ed,
                                cinematography=args.ci, composer=args.com,
                                studio=args.stu, country=args.cou,
                                language=args.lang)

    df = apply_sorting(df, flags=args.sorts)

    # Select columns
    if args.meta and args.cols:
        selected_cols = ["title", "year"]
        selected_cols += list(args.cols)
        df = df[selected_cols]
    elif args.meta:
        # Default for enabled metadata
        df = df[["title", "year", "nrating", "nlogs"]]

    write_list_to_csv_or_txt(df, args.dt, output_format=args.out)
