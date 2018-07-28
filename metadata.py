import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict


def str_filter(df, sf, sfv):
    df = df.dropna(subset=[sf])
    return df.loc[df[sf].apply(lambda x: sfv in x)]


def apply_meta_filters(df, min_lrating=None, min_llogs=None, max_llogs=None,
                       min_year=None, max_year=None, min_runtime=None,
                       max_runtime=None, genre=None, actor=None, director=None,
                       producer=None, writer=None, editor=None,
                       cinematography=None, visual_effects=None, composer=None,
                       sound=None, production_design=None, costumes=None,
                       studio=None, country=None, language=None):
    # Retrieve all the metadata
    df = df.apply(get_movie_info, axis=1)
    # Remove NaN-year entries
    df = df.dropna(subset=['year'], how='any')
    df["year"] = df["year"].apply(int)

    # Filter by LB rating
    if min_lrating:
        df = df.loc[df["lrating"] >= min_lrating]

    # Filter by LB logs
    if min_llogs or max_llogs:
        df = df.loc[(df["llogs"] <= max_llogs) & (
                     df["llogs"] >= min_llogs)]

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
               "visual-effects": visual_effects,
               "composer": composer,
               "sound": sound,
               "production-design": production_design,
               "costumes": costumes,
               "studio": studio,
               "country": country,
               "language": language}
    for sf, val in sf_dict.items():
        if val is not None:
            df = str_filter(df, sf, val)

    return df


def get_movie_info(df):
    title = df["title"]

    try:
        with open('moviedata/{}/{}.html'.format(title, title), 'r') as mf:
            contents = mf.read()
            soup = BeautifulSoup(contents, 'html.parser')
    except FileNotFoundError:
        return df

    # ACTUAL TITLE
    df["title"] = soup.find('span', class_='frame-title').text.strip()

    # AVG RATING BY LETTERBOXD USERS
    try:
        df["lrating"] = float((soup.find(
            attrs={'name': 'twitter:data2'})['content']).split()[0])
        # DIFFERENCE IN RATING
        df["diff"] = df["nrating"] - df["lrating"]
    except TypeError:
        df["lrating"] = None
        df["diff"] = None
    except KeyError:
        df["diff"] = None

    # NUMBER OF LETTERBOXD USERS WHO WATCHED IT
    logs_str = soup.find('li', class_='filmstat-watches').find(
        'a')['title'].split()[2]
    df["llogs"] = int(logs_str.replace(',', ''))

    # RELEASE YEAR
    try:
        df["year"] = int(soup.find(itemprop='datePublished').text.strip())
    except AttributeError:
        df["year"] = None

    # GENRES
    try:
        tab_genres = soup.find('div', id='tab-genres').find_all('a')
        df["genre"] = [t.text.strip() for t in tab_genres]
    except AttributeError:
        df["genre"] = [""]

    # RUNTIME
    runtime_str = soup.find('p', class_='text-link').text.split()[0]
    if runtime_str == "More":
        df["runtime"] = 0
    else:
        df["runtime"] = int(runtime_str.replace(',', ''))

    # ACTORS, DIRECTOR, PRODUCERS, WRITER, EDITOR, CINEMATOGRAPHY, COMPOSER
    # STUDIOS, COUNTRY, LANGUAGES
    slugs = [a for a in (sl.find_all('a') for sl in soup.find_all(
        'div', class_='text-sluglist')) if a]
    slugdict = defaultdict(list)
    for slug in slugs:
        for link in slug:
            try:
                lpart = link['href'][1:][:-1]
            except KeyError:
                continue
            if lpart.startswith('films'):
                lpart = lpart[6:]
                if lpart.startswith('genre'):
                    continue
            k, v = lpart.split('/')
            slugdict[k].append(v)
    for k, v in slugdict.items():
        df[k] = v

    # IMDb ID
    for link in soup.find_all('a'):
        if link.text.strip() == "IMDb":
            df["imdb"] = "tt"+link['href'].split(
                '/title/')[1].strip('/maindetails')
            break

    return df
