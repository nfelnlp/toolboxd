import pandas as pd

from moviedata import get_movie_info


def str_filter(df, sf, sfv):
    df = df.dropna(subset=[sf])
    return df.loc[df[sf].apply(lambda x: sfv in x)]


def apply_meta_filters(df, min_lb_rating=None, min_lb_logs=None,
                       max_lb_logs=None, min_year=None, max_year=None,
                       min_runtime=None, max_runtime=None, genre=None,
                       actor=None, director=None, producer=None, writer=None,
                       editor=None, cinematography=None, composer=None,
                       studio=None, country=None, language=None):
    # Retrieve all the metadata
    df = df.apply(get_movie_info, axis=1)
    # Remove NaN-year entries
    df = df.dropna(subset=['year'], how='any')
    df["year"] = df["year"].apply(int)

    # Filter by LB rating
    if min_lb_rating:
        df = df.loc[df["lb_rating"] >= min_lb_rating]

    # Filter by LB logs
    if min_lb_logs or max_lb_logs:
        df = df.loc[(df["lb_logs"] <= max_lb_logs) & (
                     df["lb_logs"] >= min_lb_logs)]

    # Filter by year
    if min_year or max_year:
        df = df.loc[(df["year"] >= min_year) & (df["year"] <= max_year)]

    # Filter by runtime
    if min_runtime or max_runtime:
        df = df.loc[(df["runtime"] >= min_runtime) & (
                     df["runtime"] <= max_runtime)]

    # Filter by string
    sf_dict = {"genre": genre,
               "actor": actor,
               "director": director,
               "producer": producer,
               "writer": writer,
               "editor": editor,
               "cinematography": cinematography,
               "composer": composer,
               "studio": studio,
               "country": country,
               "language": language}
    for sf, val in sf_dict.items():
        if val is not None:
            df = str_filter(df, sf, val)

    return df


def apply_sorting(df, sort_lbl=False):
    if sort_lbl:
        # Sort by number of LB logs
        df = df.sort_values("lb_logs")
    return df
