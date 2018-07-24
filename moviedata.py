from bs4 import BeautifulSoup


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
        df["lb_rating"] = float((soup.find(
            attrs={'name': 'twitter:data2'})['content']).split()[0])
    except TypeError:
        df["lb_rating"] = None

    # NUMBER OF LETTERBOXD USERS WHO WATCHED IT
    logs_str = soup.find('li', class_='filmstat-watches').find(
        'a')['title'].split()[2]
    df["lb_logs"] = int(logs_str.replace(',', ''))

    # RELEASE YEAR
    try:
        df["year"] = int(soup.find(itemprop='datePublished').text.strip())
    except AttributeError:
        df["year"] = None

    # GENRES
    try:
        tab_genres = soup.find('div', id='tab-genres').find_all('a')
        df["genres"] = [t.text.strip() for t in tab_genres]
    except AttributeError:
        df["genres"] = [""]

    # RUNTIME
    df["runtime"] = soup.find('p', class_='text-link').text.split()[0]

    # DIRECTOR
    try:
        df["director"] = soup.find('span', class_='prettify').text.strip()
    except AttributeError:
        df["director"] = None

    # ACTORS
    # LANGUAGES
    # COUNTRIES

    for link in soup.find_all('a'):
        if link.text.strip() == "IMDb":
            df["IMDb_ID"] = "tt"+link['href'].split('/title/')[1].strip('/maindetails')
            break

    return df
