#!/bin/bash
set -e
scraper=/home/luke/dev/python/bot-lax-adaptor
home=$(pwd)

function scrape {
    regex=".*elife-([0-9]{5})\-v([0-9]{1})\.xml$"
    cd $scraper
    target=$1
    shift # pop first arg
    fname_list="$@" # consume all/rest of args

    for fname in $fname_list; do
        for path in ./article-xml/articles/$fname*; do         
           if [[ $path =~ $regex ]]; then
                msid=${BASH_REMATCH[1]}
                ver=${BASH_REMATCH[2]}
                url="https://lax.elifesciences.org/api/v2/articles/$msid/versions/$ver"
                echo "fetching: $url"
                curl --silent -X GET "$url" | jq . > $home/$target/${path##*/}.json
            else
                echo "[error extracting msid+ver from $path]"
            fi
       done
    done
    cd -
}

scrape ajson elife-13964- elife-14850- elife-15378- elife-18675- elife-20125-v1
