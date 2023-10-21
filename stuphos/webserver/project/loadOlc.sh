#!/bin/bash
mudbase="/StuphMUD/lib"
libdata="${mudbase}/python/supplemental/libdata"
wlddir="${mudbase}/world"

./manage.py sqlreset web.server > .stuphweb-reset.sql
./manage.py dbshell < .stuphweb-reset.sql
rm .stuphweb-reset.sql

python -m web.server.load \
       -L ${libdata} \
       -w ${wlddir} \
       -t -v --cascade
