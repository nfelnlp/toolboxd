import argparse
import math
import os
import pandas as pd
import time
import unicodedata

from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime
from nltk.corpus import stopwords
from urllib import request


def query_imdb(res_pg, query):
    print("Searching for {} ...".format(query))
    time.sleep(20)
    with request.urlopen(
        'https://www.imdb.com/search/title?title={}&title_type=feature'
        '&sort=release_date,desc'.format(
            query)) as response:
        html = response.read()
        # Save results page
        with open(res_pg, 'w') as fw:
            soup = BeautifulSoup(html, 'html.parser')
            fw.write(soup.prettify())
            # print("Results written to {}".format(res_pg))
    return soup


def get_release_date(id_str, force_query=False):
    rel_pg = 'lists/vdfkino/imdb_release_pages/{}.html'.format(id_str)
    if os.path.exists(rel_pg) and not force_query:
        # print("Reading from existing file {}".format(rel_pg))
        with open(rel_pg, 'r') as rpr:
            content = rpr.read()
            soup = BeautifulSoup(content, 'html.parser')
    else:
        time.sleep(20)
        with request.urlopen(
            'https://www.imdb.com/title/{}/releaseinfo'.format(
                id_str)) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')
            with open(rel_pg, 'w') as rpw:
                rpw.write(soup.prettify())

    all_dates = soup.find_all('tr')
    candidates = defaultdict(list)

    def parse_cand_date(row):
        try:
            parsed_date = datetime.strptime(trow[1], '%d %B %Y')
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            return

    for dt in all_dates:
        # Remove whitespaces
        trow = dt.text.split('\n')
        trow = [t.strip() for t in trow if t.strip() != ""]
        if 2 <= len(trow) <= 3:
            new_cand = parse_cand_date(trow)
            if new_cand is not None:
                candidates[trow[0]].append(new_cand)
    return candidates


def format_query(query):
    query = query.replace(' ', '+').replace('+/+', '+').replace(
        ',', '').replace('(', '').replace(')', '').replace(
        ':', '').replace('+-+', '+').replace('/', '+').replace(
        '\"', '').replace('#', '').replace('&', '').replace('++', '+')

    if '\"' in query:
        query = query.strip('\"')

    # Remove stopwords if the title is not very short
    if len(query.split('+')) >= 5:
        query = '+'.join([w for w in query.split(
                '+') if w.lower() not in stopwords.words('english')])

    # Remove "(OmU)", "(IMAX)", etc.
    query = query.replace('(OmU)', '').replace('(OV)', '').replace(
        '(IMAX)', '').replace('(AT)', '').replace('(3D)', '').replace(
        '(2D/3D)', '').replace('aka', '')

    query = unicodedata.normalize('NFKD', query).encode(
        'ascii', 'ignore').decode('utf-8')
    if len(query.split('+')) >= 5:
        query = '+'.join(query.split('+')[:5])

    return query


def get_results(title, force_query=False):
    fmtd_query = format_query(title)
    res_pg = 'lists/vdfkino/results/{}.html'.format(fmtd_query)

    if os.path.exists(res_pg) and not force_query:
        print("Reading from existing file for {}".format(fmtd_query))
        with open(res_pg, 'r') as fr:
            content = fr.read()
            soup = BeautifulSoup(content, 'html.parser')
    else:
        soup = query_imdb(res_pg, fmtd_query)

    res_ops = [soup.find_all('td', class_='result_text'),
               soup.find_all('h3', class_='lister-item-header')]
    return max(res_ops, key=len)


def find_movie(col):

    def results_loop(results, max_num=5):
        if len(results) == 0:
            return
        if max_num:
            results = results[:max_num]
        approx_cands = {}
        for res in results:
            this_id = (res.find('a')['href']).split('/')[2]
            print("\t:: {}".format(
                res.find('a').text.strip()))
            if this_id.startswith('tt'):
                date_cands = get_release_date(this_id)
            else:
                continue

            for cou, dt in date_cands.items():
                if cou == "Germany":
                    if col['Datum'].strftime('%Y-%m-%d') in dt:
                        print("\t\tEXACT MATCH!\n")
                        return this_id

            sum_date_diffs = []
            for cou, dt in date_cands.items():
                this_date = dt[0]
                if this_date is not None:
                    sum_date_diffs.append(abs(
                        (col['Datum']
                         - datetime.strptime(this_date, '%Y-%m-%d')).days))
            if len(sum_date_diffs) > 0:
                avg_diff = round(sum(sum_date_diffs)/len(sum_date_diffs))
                print("\t\tAPPROX MATCH: {} ({})".format(
                    this_id, avg_diff))
                approx_cands[this_id] = avg_diff
            else:
                print("\t\tNO DATE AVAILABLE: {}".format(
                    this_id))
                approx_cands[this_id] = 1000

            if len(results) == 1:
                print("\t\tONLY ONE RESULT!\n")
                approx_cands[this_id] = 0
                break
        return approx_cands

    def strip_words(title, cut_front=False):
        wbw_title = title.split(' ')
        csize = round(math.sqrt(len(wbw_title)))

        if cut_front:
            return ' '.join(wbw_title[csize:])
        else:
            return ' '.join(wbw_title[:-csize])

    def save_match(em_file, res):
        # Save exact match
        with open(em_file, 'w') as wf:
            wf.write(res)

    # Ignore "WA" (Wiederaufführung)
    if '(WA)' in col['Filmtitel']:
        return

    em_dir = 'lists/vdfkino/exact_matches'

    cands = {}
    title_variations = []
    titles = [col['Filmtitel']]
    if type(col['Original Titel']) != float:
        titles.append(col['Original Titel'])
    for t in titles:
        title_variations += [t]
        title_variations += t.split(' - ')
        title_variations += [strip_words(t)]
        title_variations += [strip_words(t, cut_front=True)]
    for tv in reversed(sorted(list(set(title_variations)), key=len)):
        em_file = '{}/{}_{}.id'.format(em_dir, str(col['Datum'])[:10],
                                       format_query(tv))
        if os.path.exists(em_file):
            em = open(em_file, 'r').read()
            print("Exact match from previous iteration: {}".format(em))
            print("\t:: {}\n".format(tv))
            return em
        if len(tv) < 5 and len(col['Filmtitel']) > 15:
            continue
        res = results_loop(get_results(tv))
        if type(res) == dict:
            if len(res) == 1:
                res = list(res.keys())[0]
                save_match(em_file, res)
                return "* {}".format(res)
            cands = {**cands, **res}
        elif res is not None:
            save_match(em_file, res)
            return res

    if len(cands) > 0:
        print("")
        return "* {}".format(min(cands, key=cands.get))

    print("No match.\n")


def main(args):
    if args.dl:
        download_span(args.start, args.end, args.dl)

    root_dir = 'lists/vdfkino/import'
    all_htmls = os.listdir(root_dir)
    df_list = []
    for vdffile in sorted(all_htmls):
        with open('{}/{}'.format(root_dir, vdffile), 'r') as vf:
            contents = vf.read()

            # Choose the main table
            df = pd.read_html(contents)[3]
            df.columns = ['Datum', 'Filmtitel', 'Original Titel',
                          'Verleiher']

            # Forward-fill movie columns with preceding date
            df['Datum'] = df['Datum'].fillna(method='ffill')

            # Remove unnecessary columns / Clean up
            df = df.loc[df['Filmtitel'].notnull()]
            df = df.loc[df['Datum'].notnull()]
            df = df.loc[df['Filmtitel'] != 'Filmtitel']

            # Change date format to Y-m-d
            df['Datum'] = pd.to_datetime(df['Datum'], format="%d.%m.%Y")
            df = df.loc[df['Datum'] >= datetime.strptime(
                args.start, "%Y-%m-%d")]

            df_list.append(df[['Datum', 'Filmtitel', 'Original Titel']])

    # Concatenate from all files / pages
    span_df = pd.concat(df_list, ignore_index=True)

    # Group by date
    gb = span_df.groupby('Datum', as_index=False)

    for x in gb.groups:
        one_date_df = gb.get_group(x)

        filename = "{}.csv".format(
            one_date_df['Datum'].tolist()[0].strftime('%Y-%m-%d'))

        # Find the movie on IMDb
        one_date_df['imdbID'] = one_date_df.apply(lambda x: find_movie(x),
                                                  axis=1)
        one_date_df.to_csv(
            "{}/{}".format('lists/vdfkino/csvs', filename), index=False)
        print("\n_______________________________________\n")
        print(one_date_df.to_string())
        print("\n_______________________________________\n")


def download_span(start_date, end_date, max_page):
    for page_num in range(1, max_page+1):
        with request.urlopen('https://www.vdfkino.de/cgi-bin/termine.cgi?P={}'
                             '&F={}&T={}&A=datum&ACTION=&SEARCH=&SEARCH2='
                             '&month=&year='.format(
                page_num, start_date, end_date)) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')

            filename = 'lists/vdfkino/import/{}-page-{}.html'.format(
                start_date, page_num)
            with open(filename, 'w') as vf:
                vf.write(soup.prettify())
        print("VDF data written to {}".format(filename))
        time.sleep(10)


def export_to_lb(args):
    csv_dir = 'lists/vdfkino/csvs'
    df_list = []

    start = datetime.strptime(args.start, '%Y-%m-%d')
    end = datetime.strptime(args.end, '%Y-%m-%d')

    for date_f in sorted(os.listdir(csv_dir)):
        dfp = datetime.strptime(date_f.strip('.csv'), '%Y-%m-%d')
        if start <= dfp and end >= dfp:
            df_list.append(pd.read_csv('{}/{}'.format(
                csv_dir, date_f)))
    df = pd.concat(df_list, ignore_index=True)

    def choose_title(row):
        if type(row["Original Titel"]) != float:
            return row["Original Titel"]
        else:
            return row["Filmtitel"]

    def write_info(row):
        if '*' in row['imdbID']:
            info = '* {}'.format(row['Datum'])
        else:
            info = row['Datum']
        if (type(row['Original Titel']) != float
           and row['Original Titel'] != row['Filmtitel']):
            info = '{} | {}'.format(
                info, row['Filmtitel'])
        return info

    woid_df = df.loc[df['imdbID'].isnull()]
    df = df.loc[df["imdbID"].notnull()]
    df['Title'] = df.apply(lambda x: choose_title(x), axis=1)
    df['Note'] = df.apply(lambda x: write_info(x), axis=1)
    df['imdbID'] = df.apply(lambda x: x['imdbID'].strip('* '), axis=1)

    df = df.drop(['Original Titel', 'Filmtitel', 'Datum'], axis=1)
    filename = 'lists/vdfkino/export/vdfkino_{}.csv'.format(args.start)
    df.to_csv(filename, index=False)
    print("Exported to {}".format(filename))
    print(woid_df.to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-dl", default=None, type=int, dest='dl')
    parser.add_argument("-start", required=True, type=str, dest='start')
    parser.add_argument("-end", required=True, type=str, dest='end')
    main(parser.parse_args())
    export_to_lb(parser.parse_args())
