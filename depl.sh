#!/bin/bash

CURDIR=`pwd`


for dest in 'comcast' 'att' 'amazon' 'rack' 'softlayer' 'timewarner'
do
    cd ${CURDIR}/$dest
    scrapy deploy
done
sudo service scrapyd restart
