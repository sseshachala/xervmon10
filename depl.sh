#!/bin/bash

CURDIR=`pwd`


for dest in 'comcast' 'att' 'amazon' 'rack' 'softlayer' 'timewarner' 'myrack'
do
    cd ${CURDIR}/$dest
    scrapy deploy
done
sudo service scrapyd restart
