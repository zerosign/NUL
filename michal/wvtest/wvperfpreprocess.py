#!/usr/bin/env python

import sys
import re
import os
import os.path
import string
import time

re_date = re.compile('^Date: (.*)')
re_testing = re.compile('^(\([0-9]+\) (#   )?)?\s*Testing "(.*)" in (.*):\s*$')
re_commit = re.compile('(\S+) (.*?), commit: (.*)')
re_commithash = re.compile('([0-9a-f]{7}) \(')
re_check = re.compile('^(\([0-9]+\) (#   )?)?!\s*(.*?)\s+(\S+)\s*$')
re_perf =  re.compile('^(\([0-9]+\) (#   )?)?!\s*(.*?)\s+PERF:\s*(.*?)\s+(\S+)\s*$')

# State variables
date = time.localtime(time.time())
linetype = None
what = None
where = None
commit = None
commithash = None
basename = None
ext = None
perf = None
key = None
val = None
units = None

def matches(re):
    global match, line
    match = re.match(line)
    return match

for line in sys.stdin.readlines():
    line = line.rstrip()
    match = None

    # Parse known lines
    if matches(re_date):
        linetype='date'
        date = time.strptime(match.group(1), "%a, %d %b %Y %H:%M:%S +0200")
    elif matches(re_testing):
        linetype='testing'
        what = match.group(3)
        where = match.group(4)

        match = re_commit.match(what)
        if match:
            linetype='commitid'
            date = time.strptime(match.group(2), "%Y-%m-%d %H:%M:%S")
            commit = match.group(3)
            if matches(re_commithash):
                commithash = match.group(1)
            else:
                commithash = None

        (basename, ext) = os.path.splitext(os.path.basename(where))
    elif matches(re_perf):
        linetype='perf'
        perf = match.group(4)
        perf = perf.split()
        key = perf[0]
        try:
            val = float(perf[1])
        except ValueError:
            val = None
        try:
            units = perf[2]
        except:
            units = None
    else:
        linetype='other'

    # Rewriting rules
    if where.find('/vancouver-kernelbuild') != -1:
        global tag
        if linetype == 'testing':
            m = re.compile('vancouver-kernelbuild-(.*).wv').search(where)
            if m: tag = m.group(1)
            else: tag = 'ept-vpid'

            line='Testing "Kernel compile inside VM (on ramdisk)" in vancouver-kernelbuild:'
        if linetype == 'perf':
            line = line.replace('kbuild', tag);
            line = line.replace('ok', 'axis="kbuild" ok');

    # Output (possibly modified) line
    print line

# Local Variables:
# compile-command: "cat nul-nightly/nul_*.log|./wvperfpreprocess.py|./wvperf2html.py > graphs.html"
# End: