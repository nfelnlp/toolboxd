import os
import pandas as pd
import time

from bs4 import BeautifulSoup
from urllib import request

from ladle import save_soup, lb_search_film


def read_html(html):
    with open(html, 'r') as fr:
        contents = fr.read()
        soup = BeautifulSoup(contents, 'html.parser')
    return soup


def get_films_from_index(ix):
    ref_list = []
    for div in ix.find_all('div', class_='lister-item-image'):
        ref_list.append(div.find('a')['href'].split('/')[2])
    return ref_list


def get_missing():
    ids = []
    read_dir = 'lists/prime/imdb_index'
    for idf in os.listdir(read_dir):
        ids += [line.rstrip('\n') for line in open(
            '{}/{}'.format(read_dir, idf))]
    # Collect all imdbIDs from moviedata
    id_list = []
    for mov_dir in os.listdir('moviedata'):
        meta_file = 'moviedata/{}/{}.html'.format(mov_dir, mov_dir)
        try:
            with open(meta_file, 'r') as mf:
                contents = mf.read()
                soup = BeautifulSoup(contents, 'html.parser')
        except FileNotFoundError:
            print('X\t{}'.format(meta_file))
        for link in soup.find_all('a'):
            if link.text.strip() == "IMDb":
                id_list.append("tt"+link['href'].split(
                    '/title/')[1].strip('/maindetails'))
                break

    print("Retrieving missing films in moviedata...")
    for prime_mov in ids:
        if prime_mov not in id_list:
            lb_search_film(prime_mov)
            time.sleep(10)


def check_lang(df):
    print("Checking for OV/OmU availability...")

    def follow_imdb(mov_id):
        amzn_page = 'lists/prime/amzn/{}'.format(mov_id)
        if os.path.exists(amzn_page):
            soup = read_html(amzn_page)
        else:
            imdb_soup = save_soup('https://www.imdb.com/title/{}/'.format(
                                    mov_id),
                                  None)
            time.sleep(10)
            offsite = imdb_soup.find(
                'div', class_='winner-option')['data-href']
            print("\t{}".format(
                mov_id), end='\r')
            soup = save_soup('https://www.imdb.com/{}/'.format(offsite),
                             amzn_page)
            time.sleep(10)
            try:
                temp = soup.find('h1', id='aiv-content-title').text
                print('\t{}'.format(
                    soup.find('h1', id='aiv-content-title').text.strip(
                        ).split('\n')[0]))
            except AttributeError:
                pass
        table = soup.find('table', class_='a-keyvalue')
        for tr in table.find_all('tr'):
            head = tr.find('th').text.strip()
            val = tr.find('td').text.strip()
            if head == 'Sprachen':
                if "," in val:
                    return val.split(',')
                return [val]

    df = df.drop_duplicates(subset='imdbID')
    df['AP_lang'] = df.apply(lambda x: follow_imdb(x['imdbID']), axis=1)
    # Include all German language movies by default

    df_ger = df.loc[df['language'].apply(lambda x: 'german' == x[0])]
    # No spoken language
    df_nol = df.loc[df['AP_lang'].isnull()]

    df = df.loc[df['AP_lang'].notnull()]
    # All other languages
    df_oth = df.loc[~(df['AP_lang'].apply(lambda x: 'Deutsch' in x) &
                      (df['AP_lang'].apply(len) == 1))]

    df = pd.concat([df_oth, df_ger]) #, df_nol])

    return df


def main():
    general_save_dir = 'lists/prime'
    imdb_save_dir = '{}/imdb_index'.format(general_save_dir)

    for page_num in range(1, 48):
        imdb_index = ('https://www.imdb.com/search/title?online_availability=DE/'
                      'today/Amazon/subs&title_type=feature&sort=release_date,asc'
                      '&page={}&view=simple').format(page_num)
        filename = '{}/page-{}.html'.format(imdb_save_dir, page_num)

        if (os.path.exists(filename)
           or os.path.exists('{}.ids'.format(filename))):
            print(": {}.".format(filename), end='\r')
            continue
        else:
            save_soup(imdb_index, filename)
            print("Downloaded: {}".format(filename))

        print("")
        films_on_page = get_films_from_index(read_html(filename))

        with open('{}.ids'.format(filename), 'w') as wf:
            for film in films_on_page:
                wf.write('{}\n'.format(film))
        os.remove(filename)
        time.sleep(20)

    get_missing()


if __name__ == "__main__":
    main()
