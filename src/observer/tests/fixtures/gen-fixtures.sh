#!/bin/bash
set -xuv
scraper=/home/luke/dev/python/bot-lax-adaptor
home=$(pwd)

function scrape {
    cd $scraper
    target=$1
    shift # pop first arg
    fname_list="$@" # consume all/rest of args
    for fname in $fname_list
    do
       for path in ./article-xml/articles/$fname*
       do
         ./scrape-article.sh "$path" | jq '.article' > $home/$target/${path##*/}.json
       done
    done
    cd -
}

scrape ajson elife-13964- elife-14850- elife-15378- elife-18675-
