#!/bin/bash
set -xuv
for fname in 13964 14850 15378 18675
do
   cp "/home/luke/dev/python/bot-lax-adaptor/article-json/elife-$fname"* ./
done

