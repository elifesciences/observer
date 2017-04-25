# Observer
 
An effort by [eLife Sciences](http://elifesciences.org) to provide an 
unsophisticated reporting application for article data.

This project uses the [Python programming language](https://www.python.org/),
the [Django web framework](https://www.djangoproject.com/) and a
[relational database](https://en.wikipedia.org/wiki/Relational_database_management_system).

[Github repo](https://github.com/elifesciences/observer/).

## RSS

The URLs look like:

    /reportname/

For example, if you wanted all articles published:

    /latest-articles/

## installation

[code](https://github.com/elifesciences/observer/blob/master/install.sh)  

    git clone https://github.com/elifesciences/observer
    cd observer
    ./install.sh

PostgreSQL is used in production so there is a dependency on psycopg2 which 
requires your distribution's 'libpq' library to be installed. On Arch Linux, 
this is 'libpqxx', on Ubuntu this is 'libpq-dev'.

## updating

[code](https://github.com/elifesciences/observer/blob/master/install.sh)  

    ./install.sh

## testing 

[code](https://github.com/elifesciences/observer/blob/master/src/observer/tests/)  

    ./test.sh

## running

[code](https://github.com/elifesciences/observer/blob/master/manage.sh)

    ./manage.sh runserver
    firefox http://127.0.0.1:8000/api/docs/

## Copyright & Licence

Copyright 2017 eLife Sciences. Licensed under the [GPLv3](LICENCE.txt)

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

