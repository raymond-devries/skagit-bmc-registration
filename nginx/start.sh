#!/bin/bash

FILE=/etc/nginx/conf.d/default.conf

if test -f "$FILE"; then
  echo "default.conf exists, therfore it will be removed"
  rm "$FILE"
  cp /home/nginx.conf /etc/nginx/conf.d/
else
  echo "default.conf not found original nginx.conf will be kept"
fi