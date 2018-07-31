import os
import argparse
import pandas as pd

from ratings import get_all_movies_from_page


def clone(full_url, clones_dir='lists/cloned', return_filename=False):
    # Formatting
    if full_url.startswith('http'):
        full_url = full_url.split('.com/')[-1]
    if full_url.startswith('/'):
        full_url = full_url[1:]
    if full_url.endswith('/'):
        full_url = full_url[:-1]

    url_parts = full_url.split('/')
    if len(url_parts) > 2:
        user, list_str, url_end = url_parts
        list_title = "{}/{}".format(list_str, url_end)
    else:
        # Person (e.g. director) page
        # (Not very intuitive var naming here)
        # user : director/actor/...
        # list_title : name/URL part of director/actor/...
        user, list_title = url_parts
        url_end = list_title
        clones_dir = 'lists'

    if not os.path.exists(clones_dir):
        os.makedirs(clones_dir)

    # Create directory according to username if necessary
    output_dir = '{}/{}'.format(clones_dir, user)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("{} : {}".format(user, list_title))

    return_path = get_all_movies_from_page(
        user=user,
        list_title=list_title,
        save_dir=clones_dir,
        output_name=url_end,
        with_ratings=False,
        to_reverse=False,
        create_meta_file=True,
        return_path=True)

    print("List saved to {}[.csv, _META.html]\n".format(return_path))
    if return_filename:
        return "{}.csv".format(return_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-url", help="URL to list on Letterboxd (also "
                        "possible to simply use the last part, i.e. "
                        "<user>/list/<title>)",
                        required=True, dest='url')
    parser.add_argument("-save_dir", help="directory to save list to",
                        default='lists/cloned', dest='sdir')
    args = parser.parse_args()

    clone(args.url, args.sdir)
