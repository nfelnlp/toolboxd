from bs4 import BeautifulSoup
from collections import defaultdict


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
    except TypeError:
        df["lrating"] = None

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
            df["IMDb_ID"] = "tt"+link['href'].split(
                '/title/')[1].strip('/maindetails')
            break

    return df
