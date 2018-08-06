import datetime
import argparse
import pandas as pd

from ranking import collect_logs_from_users


def compare_ratings(user2, df, user1, tolerance=2):
    # Consider only films both users have watched
    df = df.loc[df[user1].notnull()]
    df = df.loc[df[user2].notnull()]
    df = df[["title", user1, user2]]

    comp_df = df.loc[df[user1] != 0.0]
    comp_df = comp_df.loc[comp_df[user2] != 0.0]
    comp_df["rating_diff"] = comp_df[user1] - comp_df[user2]
    comp_df.loc[abs(comp_df["rating_diff"]) <= tolerance] = 0

    if len(comp_df) > 0:
        avg_diff = comp_df["rating_diff"].sum()/len(df)
    else:
        avg_diff = 0
    return 1 - abs(avg_diff)


def count_matches(user2, df, user1, lbound=None):
    # TODO : Higher weight on high ratings
    if lbound:
        user1_favs = df.loc[df[user1] >= lbound]
        u1f_both_seen = user1_favs.loc[user1_favs[user2].notnull()]

    user1_seen = df.loc[df[user1].notnull()]
    both_seen = user1_seen.loc[user1_seen[user2].notnull()]
    #  both_seen = both_seen[["title", user1, user2]]
    if lbound:
        if len(u1f_both_seen) > 0 and len(user1_favs) > 0:
            return (0.5*(len(both_seen)/len(user1_seen))
                    + 0.5*(len(u1f_both_seen)/len(user1_favs)))
    return len(both_seen)/len(user1_seen)


def count_logs(user2, df, with_ratings=False):
    user2_seen = df.loc[df[user2].notnull()]
    if with_ratings:
        user2_rated = user2_seen.loc[user2_seen[user2] != 0.0]
        return len(user2_rated)/len(user2_seen)
    else:
        return len(user2_seen)


def calculate_total(col, mrm_weight, factor):
    col["avg_match_%"] = (mrm_weight * col["match_%"]
                          + (1 - mrm_weight) * col["rmatch_%"])

    rs_weight = (1 - factor) * col["nz_rats"]
    match_weight = 1 - rs_weight

    total = (match_weight * col["avg_match_%"]
             + rs_weight * col["rats_sim"])
    return total


def make_comp_table(user, lb=8, tol=2, mrm=.75, fac=.25):
    today = datetime.date.today()
    df = collect_logs_from_users(today)

    stats = pd.DataFrame({'user2':
                          list(df.drop(['title', args.user], axis=1))})

    stats["match_%"] = stats.apply(lambda x: count_matches(
        x['user2'], df, args.user, lbound=args.lb), axis=1)
    stats["rmatch_%"] = stats.apply(lambda x: count_matches(
        args.user, df, x['user2'], lbound=args.lb), axis=1)
    stats["rats_sim"] = stats.apply(lambda x: compare_ratings(
        x['user2'], df, args.user, tolerance=args.tol), axis=1)
    stats["nz_rats"] = stats.apply(lambda x: count_logs(
        x['user2'], df, with_ratings=True), axis=1)

    stats["total"] = stats.apply(lambda x: calculate_total(
        x, args.mrm, args.fac), axis=1)

    # Add user with 1.0
    stats = stats.append({'user2': args.user,
                          'match_%': 1,
                          'rmatch_%': 1,
                          'rats_sim': 1,
                          'nz_rats': 1,
                          'total': 1}, ignore_index=True)
    print("lower bound for ratings for matches: {}\n"
          "ratings similarity tolerance: {}\n"
          "match reverse-match factor: {}\n"
          "total (avg match vs. ratings similarity) factor: {}\n".format(
            args.lb, args.tol, args.mrm, args.fac))
    stats = stats.sort_values('total', ascending=False)
    print(stats.to_string())

    return stats, today


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", help="user to compare to everyone",
                        required=True, type=str, dest='user')
    parser.add_argument("-lb", help="lower bound for ratings of -u user for"
                        " matches",
                        default=8, type=int, dest='lb')
    parser.add_argument("-tol", help="ratings similarity tolerance",
                        default=2, type=int, dest='tol')
    parser.add_argument("-mrm", help="match reverse-match factor/weight",
                        default=0.75, type=float, dest='mrm')
    parser.add_argument("-fac", help="total (avg match vs. ratings similarity)"
                        " factor/weight",
                        default=0.25, type=float, dest='fac')
    args = parser.parse_args()

    stats, date = make_comp_table(args.user, args.lb, args.tol, args.mrm,
                                  args.fac)
    stats.to_csv('stats/{}_comparison_{}.csv'.format(args.user, date),
                 sep=',', index=False)
