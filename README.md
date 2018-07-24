# Toolboxd

A Python3 script collection to get statistics about your [Letterboxd](https://letterboxd.com/) network.


### Dependencies
- **Python3** (tested on 3.5)
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [pandas](https://pandas.pydata.org/pandas-docs/stable/index.html)
- [numpy](https://docs.scipy.org/doc/numpy-1.10.4/user/install.html)


## Setup

Run
```
python3 setup.py
```
This will create necessary directories and ask you for your username.


## Retrieve movie ratings

In order to save which movies the users you followed on Letterboxd logged, run
```
python3 ratings.py -u [username]
```
It will create a new folder for each user in the `user` directory and a new csv each time this script is executed, a file that contains the Letterboxd movie URL and the rating (0-10).
Since the script downloads multiple HTMLs for each user, it takes a while to finish usually and maybe runs into exceeding traffic issues.
Without the `-u` flag, it will try to take the user set as default.
You can also run `ratings.py` for updating the whole database for recent additions.


## Generate full movie list without metadata

```
python3 ranking.py -o csv -r 0
```
This will put out a csv file including all movies ever logged by users you follow.
The three columns are `[movie title],[network rating],[network number of logs]`.

`ranking.py` also has other options available:
`-w y` : Only consider movies you already logged.
`-w n` : Filter movies you already logged.
`-r [rating]` : The minimum rating down to which value you want the resulting list to go. By default, this is `3.75`.
`-o [csv/net]` : Without the `-o` flag, the list is simply printed to your terminal in full.
`-b [weight]` : Choose weighting for bayesian averaging. Right now, the bayesian averaging is the only option for ranking movies, but you can change the way lesser known movies (those with only a few logs) are "punished" for being unpopular. The default is the number of users in your network divided by 100.
`-d [date]` : Date up to when ratings should be considered. This is useful for producing rankings from previous updates.


Some options are not available unless you download the metadata: In order to download the HTML of every movie page, run
```
python3 ladle.py
```
**Warning**: This usually takes around 10MB of disk space per 100 movies.

Now you can use the following flags with `ranking.py`:
`-m` (required for flags below) : Include metadata. At the moment, this is by default `[year],[letterboxd average rating],[letterboxd number of logs],[list of genres]`
`-g [genre]` : Filter by genre, e.g. `"science fiction"` or `action`.
`-miny [year]` : Movies released in or after this year.
`-maxy [year]` : Movies released in or before this year.


## Generate all-time favourites list importable to Letterboxd

When you downloaded the top few movies as movie pages using `ladle.py` you can run
```
python3 ranking.py -o net
```
to generate a `network` csv file which can be imported to Letterboxd.


## Update movie ratings

Coming soon.
This is only for updating the ratings in case they changed after a rewatch or adding the rating few days after simply logging it (rating 0). `ratings.py` will be your friend for downloading new logs.


## Find out popular movies with your friends since last update

Coming soon.
When you execute `ratings.py` for a second time a few days after, you most likely have new logs from your friends.