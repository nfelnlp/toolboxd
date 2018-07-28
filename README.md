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

The three columns are `[title],[network_rating],[network_number_of_logs]`.

`ranking.py` also has other options available:
- `-r [rating]` : The minimum rating down to which value you want the resulting list to go. By default, this is `3.75`.
- `-w y` : Only consider movies you already logged.
- `-w n` : Filter movies you already logged.
- `-mode [std/bayesian]` : Choose mode of rating value calculation. `std` is the naive way where the sum of rating values is divided by the number of ratings. By default, this is `bayesian` where movies with few logs get punished.
- `-b [weight]` : Choose weighting for bayesian averaging. The default is the number of users in your network divided by 100. This has no effect when `mode` is set to `std`.
- `-o [csv/net]` : Without the `-o` flag, the list is simply printed to your terminal in full. `csv` saves the list to a file with the columns mentioned above. See below for `net`.
- `-d [date]` : Date up to when ratings should be considered. This is useful for producing rankings from previous updates.


## Download metadata and enable filters

Some options are not available unless you download the metadata: In order to download the HTML of every movie page, run
```
python3 ladle.py
```
**Warning**: This usually takes around 10MB of disk space per 100 movies.

By default, this takes the csv file in the `lists` directory with the latest date in its name. You have the following options with `ladle.py`:
- `-r [rating]` : Specify minimum rating (default: 3.75)
- `-f` : Select another csv file
- `-refresh` : Download HTMLs again (limit: once per day). The older file gets moved into a sub directory which has the "last-modified" date as its name.
- `-w [seconds]` : Sleep timer after each request
- `-cols [col1] [col2]` : Specify which columns the csv file has

Now you can use the following flags with `ranking.py`:
- `-m` (required for flags below) : Include metadata. At the moment, this is by default `[year],[letterboxd_average_rating],[letterboxd_number_of_logs],[list_of_genres]`
- `-lbr [rating]` : Minimum Letterboxd rating.
- `-min_llogs [logs]` : Minimum number of logs on Letterboxd.
- `-max_llogs [logs]` : Maximum number of logs on Letterboxd.
- `-miny [year]` : Movies released in or after this year.
- `-maxy [year]` : Movies released in or before this year.
- `-mint [runtime in min]` : Minimum runtime of a movie.
- `-maxt [runtime in min]` : Maximum runtime of a movie.
- `-genre [genre]` : Filter by genre, e.g. `"science fiction"` or `action`.

For the following flags, please follow the letterboxd URL (search function coming soon!), so it's best to include hyphens instead of spaces:
- `-actor` : Filter by actor, e.g. `nicolas-cage`.
- `-director` : Filter by director, e.g. `stanley-kubrick`.
- `-producer` : Filter by producer, e.g. `paul-thomas-anderson`.
- `-writer` : Filter by writer, e.g. `aaron-sorkin`.
- `-editor` : Filter by editor, e.g. `tricia-cooke`.
- `-cinematography` : Filter by cinematographer, e.g. `robert-elswit`.
- `-visual_effects` : Filter by visual effects crew, e.g. `janet-yale`.
- `-composer` : Filter by composer, e.g. `jonny-greenwood`.
- `-sound` : Filter by sound crew, e.g. `ben-burtt`.
- `-production_design` : Filter by production designer, e.g. `leslie-dilley`.
- `-costumes` : Filter by costume designer, e.g. `mary-zophres`.
- `-studio` : Filter by studio, e.g. `a24`.
- `-country` : Filter by country, e.g. `italy`.
- `-language` : Filter by language, e.g. `thai`.


## Sort the list by a different column

Run
```
python3 ranking.py -sort <column_name>
```
with any column appearing in the metadata, e.g.:
- `title` : Reverse alphabetical order according to movie title (`title_asc` for alphabetical)
- `year` : Release year of the movie, newest first (`year_asc` for earliest first)
- `nrating` : Highest network rating (average of your friends' ratings) first (this is the default way of sorting if you don't specify `-sort`)
- `nlogs` : Number of logs from your friends, highest first
- `lrating` : Highest Letterboxd rating first
- `llogs` : Number of logs on Letterboxd, highest first. Note: This number won't change unless you manually delete all folders in `moviedata` (not recommended, though!).
- `diff` : Difference between `nrating` and `lrating`.

It is possible to pass multiple columns, separated by spaces, where the last column sort gets done first s.t. only for ties at the first column sort the next few decide on the order.


## Select columns to show in the list

You can also change the columns (next to the mandatory "title" and "year") displayed at the end by running
```
python3 ranking.py -cols <column_name>
```
e.g. `genre`, `runtime`, `llogs` (number of Letterboxd logs), `lrating` (Letterboxd rating), `director`, `cinematography`, `language`.


## Generate all-time favourites list importable to Letterboxd

When you downloaded the top few movies as movie pages using `ladle.py` you can run
```
python3 ranking.py -o net
```
to generate a `network` csv file which can be imported to Letterboxd.


## Update movie ratings

```
python3 ratings.py -c
```
The `-c` flag is for updating the ratings in case they changed after a rewatch or adding the rating few days after simply logging it (rating 0). It makes absolutely sure that no movie is ignored and also keeps the ratings in case someone deleted them (to 0).


## Find out popular movies with your friends since last update

When you execute `ratings.py` for a second time a few days after, you most likely have new logs from your friends. In order to see what movies changed the most, run
```
python3 hype.py -old <path/to/old/csv> -new <path/to/new/csv> -flags popular
```
By default (without `-old` and `-new`), it will look for the csvs with the two most recent dates in the `lists` directory.

Using the `-flags` option, you can (currently) choose from three different hype lists which are:
- `rising` (default) : Movies with a rating of above 3.00 that have gained at least 0.05
- `popular` : Movies that have gained the most new logs
- `top` : See how the current top 20 movies were placed last time

**Note**: `hype.py` currently only works with downloaded metadata (`moviedata` directory).


## Download your watchlist or other lists on Letterboxd

Run `python3 clone_list.py <URL>` to clone a list from Letterboxd.

Run `python3 ladle.py -f <path/to/csv/file> -r 0` to download the necessary metadata that is not already in the `moviedata` directory.

Or you can run `python3 ranking.py -list <path/to/csv/file>` to filter all ratings by this list.