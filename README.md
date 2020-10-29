# Observer

An effort by [eLife Sciences](http://elifesciences.org) to provide an 
unsophisticated reporting application for article data.

This project uses the [Python programming language](https://www.python.org/),
the [Django web framework](https://www.djangoproject.com/) and a
[relational database](https://en.wikipedia.org/wiki/Relational_database_management_system).

[Github repository](https://github.com/elifesciences/observer/).

## reports

A report URL looks like:

* /report/reportname

For example, if you wanted the latest articles published, the url would look like:

* [/report/latest-articles](/report/latest-articles)

Reports are paginated and ordered and you can page through their results. For example:

* [/report/latest-articles?page=20](/report/latest-articles?page=20)

returns the twentieth page of the latest articles. And:

* [/report/latest-articles?page=20&per-page=100](/report/latest-articles?page=20&per-page=100)

returns you results 2000 through 2100.

Reports have a default format and often have more than one format. For example:

* [/report/latest-articles](/report/latest-articles)

is formatted as RSS. The `latest-articles` report also supports plain CSV:

* [/report/latest-articles?format=csv](/report/latest-articles?format=csv)

or, as a simple format hint:

* [/report/latest-articles.csv](/report/latest-articles.csv)

## available reports

#### latest articles report

All of the latest articles published at eLife, including in-progress POA (publish-on-accept) articles.

* [RSS](/report/latest-articles.rss), [CSV](/report/latest-articles.csv)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/latest-articles?per-page=50) [100pp](/report/latest-articles?per-page=100)

#### latest articles by subject report

Articles published by eLife, filtered by given subjects

* [RSS](/report/latest-articles-by-subject.rss), [CSV](/report/latest-articles-by-subject.csv)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/latest-articles-by-subject?per-page=50) [100pp](/report/latest-articles-by-subject?per-page=100)
* accepts these extra parameters: subject () 

#### upcoming articles report

The latest eLife POA (publish-on-accept) articles. These articles are in-progress and their final VOR (version-of-record) is still being produced.

* [RSS](/report/upcoming-articles.rss), [CSV](/report/upcoming-articles.csv)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/upcoming-articles?per-page=50) [100pp](/report/upcoming-articles?per-page=100)

#### digests report

The latest eLife digests.

* [RSS](/report/digests.rss)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/digests?per-page=50) [100pp](/report/digests?per-page=100)

#### labs-posts report

The latest eLife labs-posts.

* [RSS](/report/labs-posts.rss)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/labs-posts?per-page=50) [100pp](/report/labs-posts?per-page=100)

#### community report

The latest eLife community content.

* [RSS](/report/community.rss)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/community?per-page=50) [100pp](/report/community?per-page=100)

#### interviews report

The latest eLife interviews.

* [RSS](/report/interviews.rss)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/interviews?per-page=50) [100pp](/report/interviews?per-page=100)

#### collections report

The latest eLife collections.

* [RSS](/report/collections.rss)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/collections?per-page=50) [100pp](/report/collections?per-page=100)

#### blog-articles report

The latest eLife blog articles.

* [RSS](/report/blog-articles.rss)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/blog-articles?per-page=50) [100pp](/report/blog-articles?per-page=100)

#### features report

The latest eLife featured articles.

* [RSS](/report/features.rss)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/features?per-page=50) [100pp](/report/features?per-page=100)

#### published article index report

The dates and times of publication for all articles published at eLife. If an article had a POA version, the date and time of the POA version is included.

* [CSV](/report/published-article-index.csv), [JSON](/report/published-article-index.json)  formats
* ordered by eLife manuscript ID (_least_ recent to most recent)

#### published research article index report

The dates and times of publication for all _research_ articles published at eLife. If an article had a POA version, the date and time of the POA version is included.

* [CSV](/report/published-research-article-index.csv), [JSON](/report/published-research-article-index.json)  formats
* ordered by eLife manuscript ID (_least_ recent to most recent)

#### daily profile counts report

Daily record of the total number of profiles

* [CSV](/report/profile-count.csv)  formats
* ordered by year, month and day (_most_ recent to least recent)

#### Exeter, new POA articles report

All POA articles ordered by the date and time they were first published, most recent POA articles to least recent.

* [JSON](/report/exeter-new-poa-articles.json)  formats
* ordered by date and time this article was _first_ published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/exeter-new-poa-articles?per-page=50) [100pp](/report/exeter-new-poa-articles?per-page=100)

#### Exeter, new and updated VOR articles report

All new and updated VOR articles ordered by their updated date, most recent VOR articles to least recent.

* [JSON](/report/exeter-new-and-updated-vor-articles.json)  formats
* ordered by date and time this _version_ of the article was published (_most_ recent to least recent)
* 28 articles per page (default) [50pp](/report/exeter-new-and-updated-vor-articles?per-page=50) [100pp](/report/exeter-new-and-updated-vor-articles?per-page=100)

## installation

[code](https://github.com/elifesciences/observer/blob/master/install.sh)

    git clone https://github.com/elifesciences/observer
    cd observer
    ./install.sh

PostgreSQL is used in production so there is a dependency on psycopg2 which 
requires your distribution's 'libpq' library to be installed. On Arch Linux, 
this is 'libpqxx', on Ubuntu this is 'libpq-dev'.

## updating

### installation

[code](https://github.com/elifesciences/observer/blob/master/install.sh)

    git pull
    ./install.sh

### documents

[code](https://github.com/elifesciences/observer/blob/master/regenerate-readme.sh)

    ./regenerate-readme.sh

### reports

See [updating reports](https://github.com/elifesciences/observer/blob/master/updating-reports.md) on instructions for 
modifying reports.

## testing 

[code](https://github.com/elifesciences/observer/blob/master/src/observer/tests/)

    ./test.sh

## running

[code](https://github.com/elifesciences/observer/blob/master/manage.sh)

    ./manage.sh runserver
    xdg-open http://127.0.0.1:8000/

## Copyright & Licence

Copyright 2020 eLife Sciences. Licensed under the [GPLv3](LICENCE.txt)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

