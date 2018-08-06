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


def collect_logs_from_users(changes_from, subset=None, user_sim=False):
    try:
        changes_from = datetime.datetime.strptime(changes_from, '%Y-%m-%d')
    except TypeError:
        cf = changes_from
        changes_from = datetime.datetime(cf.year, cf.month, cf.day)

    network = os.listdir('user')
    network_dfs = []
    if subset:
        network = subset
        print("Only considering the following users:\n{}".format(network))

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

            print("\t{}\t".format(user_folder), end='\r')
            if user_sim:
                comp_t = pd.read_csv("stats/{}".format(
                    list(sorted(os.listdir('stats')))[-1]), sep=',')
                w_adjust = ((len(comp_t) - comp_t["total"].sum()-2)
                            / (len(comp_t)-1))

                sim_w = (comp_t["total"].loc[comp_t['user2'] == user_folder]
                         + w_adjust)
                print(round(float(sim_w), 2), end='\r')
                user_films[user_folder] = user_films[user_folder].apply(
                    lambda x: x * sim_w)
            print("")
            network_dfs.append(user_films)
        except ValueError:
            print("No entries for {}".format(user_folder))

    print("")
    return reduce(lambda left, right: pd.merge(left, right, on='title',
                                               how='outer'), network_dfs)


def apply_filters(df, watched=None, keep_own=False, list_filter=None,
                  target_user=None):
    if not target_user:
        target_user = open('your_username.txt', 'r').read()

    # Watched filter
    try:
        if watched == "y":
            df = df.loc[df[target_user].notnull()]
        elif watched == "n":
            df = df.loc[df[target_user].isnull()]
    except KeyError:
        raise KeyError("You can't use the -w flag if the target/default user "
                       "is not in the network or the selected users!")

    # Leave out own rating
    if not keep_own:
        if target_user in list(df):
            df = df.drop([target_user], axis=1)

    if list_filter:
        neg = None
        if len(list_filter) == 2:
            list_filter, neg = list_filter[0], list_filter[1]
        else:
            list_filter = list_filter[0]

        if list_filter.startswith('http'):
            print("Cloning list from Letterboxd...")
            list_csv = clone(list_filter, return_filename=True)
        else:
            list_csv = list_filter

        list_df = pd.read_csv(list_csv, sep=r'\t', usecols=["title"],
                              names=["title"], engine='python')
        if neg:
            df = df[~df['title'].isin(list_df['title'])]
        else:
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


def summarize_ratings(df, min_rating=3.75, rating_mode="bayesian", bw=None):
    # Generate ratings lists and number of logs in network
    df["ratings"] = df.drop(["title"], axis=1).values.tolist()
    df["ratings"] = df["ratings"].apply(
        lambda y: [int(a) for a in y if pd.notnull(a)])
    df["nlogs"] = df["ratings"].apply(len)

    # Rating mode (average / bayesian)
    if rating_mode == "bayesian":
        if bw:
            b_weighting = bw
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
        file_id = input("\nPlease provide a filename: ")
        filename = 'lists/{}.csv'.format(file_id)
        df[["title", "year", "imdbID"]].to_csv(
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
        dec = input("\nDo you want to save this table as a .txt file?\n")
        if dec == "y" or dec == "yes":
            file_id = input("Please provide a filename: ")
            with open('lists/{}.txt'.format(file_id), 'w') as lof:
                lof.write(df.to_string())


def main(args):
    print("Collecting ratings...")
    df = collect_logs_from_users(args.dt, subset=args.usub,
                                 user_sim=args.user_sim)
    print("Applying rating filters...")
    df = apply_filters(df,
                       watched=args.watched, keep_own=args.keep_own,
                       list_filter=args.lf, target_user=args.target)

    if not args.ignet:
        print("Calculating network ratings...")
        df = summarize_ratings(df,
                               min_rating=args.minr, rating_mode=args.mode,
                               bw=args.bw)

    if args.meta:
        print("Applying metadata filters...")
        df = apply_meta_filters(df,
                                min_lrating=args.lbr,
                                min_llogs=args.min_llogs,
                                max_llogs=args.max_llogs,
                                min_year=args.miny, max_year=args.maxy,
                                min_runtime=args.mint, max_runtime=args.maxt,
                                genre=args.gen, actor=args.ac,
                                director=args.di, producer=args.pro,
                                writer=args.wr, editor=args.ed,
                                cinematography=args.ci,
                                visual_effects=args.vfx, composer=args.com,
                                sound=args.snd, production_design=args.pdes,
                                costumes=args.cstm,
                                studio=args.stu, country=args.cou,
                                language=args.lang)

    print("Sorting...")
    df = apply_sorting(df, flags=args.sorts)

    print("Selecting columns...")
    if args.meta and args.cols:
        selected_cols = ["title", "year"]
        selected_cols += list(args.cols)
        df = df[selected_cols]
    elif args.meta:
        # Default for enabled metadata
        if args.out != "net":
            df = df[["title", "year", "nrating", "nlogs"]]

    print("Finished.")
    write_list_to_csv_or_txt(df, args.dt, output_format=args.out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", help="minimum rating",
                        default=3.75, type=float, dest='minr')
    parser.add_argument("-w", help="exclude films you watched (n)"
                        " | only consider films you watched (y)",
                        default=None, type=str, dest='watched')
    parser.add_argument("-target", help="set target user other than default",
                        default=None, type=str, dest='target')
    parser.add_argument("-keep_own", help="keep your own rating for averaging",
                        default=False, action='store_true', dest='keep_own')
    parser.add_argument("-list", help="filter by cloned or created list,"
                        "add ^ behind path or URL to negate",
                        default=None, nargs='*', dest='lf')
    parser.add_argument("-ignore_net", help="consider all movies (not only "
                        "those known to your network). This disables nrating "
                        "and nlogs columns",
                        default=False, action='store_true', dest='ignet')
    parser.add_argument("-mode", help="average or bayesian rating mode",
                        default="bayesian", type=str, dest='mode')
    parser.add_argument("-b", help="bayesian average weighting",
                        default=None, type=float, dest='bw')
    parser.add_argument("-o", help="output format (csv/net), "
                        "None prints to terminal (by default)",
                        default=None, type=str, dest='out')
    parser.add_argument("-d",
                        help="date (up to when ratings should be considered)",
                        default=datetime.date.today(), dest='dt')
    parser.add_argument("-usub", help="collect logs only from a subset of "
                        "users",
                        default=None, nargs='*', dest='usub')
    parser.add_argument("-user_sim", help="weight ratings by user similarity",
                        default=False, action='store_true', dest='user_sim')

    # Metadata flags
    parser.add_argument("-m", help="include metadata",
                        default=False, action='store_true', dest='meta')
    parser.add_argument('-lbr', help="minimum rating on LB",
                        default=0, type=float, dest='lbr')
    parser.add_argument('-min_llogs', help="minimum number of logs on LB",
                        default=0, type=int, dest='min_llogs')
    parser.add_argument('-max_llogs', help="maximum number of logs on LB",
                        default=10000000, type=int, dest='max_llogs')
    parser.add_argument("-miny", help="earliest year",
                        default=1890, type=int, dest='miny')
    parser.add_argument("-maxy", help="latest year",
                        default=2020, type=int, dest='maxy')
    parser.add_argument("-mint", help="minimum runtime",
                        default=0, type=int, dest='mint')
    parser.add_argument("-maxt", help="maximum runtime",
                        default=10000, type=int, dest='maxt')

    parser.add_argument("-genre", help="filter by genre",
                        default=None, nargs='*', dest='gen')
    parser.add_argument("-actor", help="filter by actor",
                        default=None, type=str, dest='ac')
    parser.add_argument("-director", help="filter by director",
                        default=None, type=str, dest='di')
    parser.add_argument("-producer", help="filter by producer",
                        default=None, type=str, dest='pro')
    parser.add_argument("-writer", help="filter by writer",
                        default=None, type=str, dest='wr')
    parser.add_argument("-editor", help="filter by editor",
                        default=None, type=str, dest='ed')
    parser.add_argument("-cinematography",
                        help="filter by cinematography",
                        default=None, type=str, dest='ci')
    parser.add_argument("-visual_effects", help="filter by visual effects",
                        default=None, type=str, dest='vfx')
    parser.add_argument("-composer", help="filter by composer",
                        default=None, type=str, dest='com')
    parser.add_argument("-sound", help="filter by sound",
                        default=None, type=str, dest='snd')
    parser.add_argument("-production_design",
                        help="filter by production design",
                        default=None, type=str, dest='pdes')
    parser.add_argument("-costumes", help="filter by costumes",
                        default=None, type=str, dest='cstm')
    parser.add_argument("-studio", help="filter by studio",
                        default=None, type=str, dest='stu')
    parser.add_argument("-country", help="filter by country",
                        default=None, type=str, dest='cou')
    parser.add_argument("-language", help="filter by language",
                        default=None, type=str, dest='lang')

    # Sorting flags
    parser.add_argument("-sort", help="sorting the resulting list\n",
                        nargs='+', default=['title_asc'], dest='sorts')
    # Column selection flags
    parser.add_argument("-cols", help="selected columns to display in list\n"
                        "Default: [title, year]\n"
                        "Look up README.md for all options",
                        nargs='+', dest='cols')

    main(parser.parse_args())
