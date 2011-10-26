#!/usr/bin/env python

import sys
import re
import os
import os.path
import string
import time


class Row(dict):
    def __init__(self, graph, date):
        self.graph = graph
        self.date = date
    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        self.graph.columns[key]=1;
    def getDate(self):
        d = time.gmtime(time.mktime(self.date))
        return "Date.UTC(%s, %s, %s, %s, %s, %s)" % \
            (d.tm_year, d.tm_mon-1, d.tm_mday, d.tm_hour, d.tm_min, d.tm_sec)

class Graph:
    def __init__(self, id, title):
        self.columns = {}
        self.id = id
        self.title = title
        self.rows = []
        self.date2row = {}
        
    def __getitem__(self, date):
        try:
            row = self.date2row[date]
        except KeyError:
            row = len(self.rows)
            self.date2row[date] = row
        try:
            return self.rows[row]
        except IndexError:
            self.rows[row:row] = [Row(self, date)]
            return self.rows[row]

    def jschart(self):
        print """
			window.chart = new Highcharts.StockChart({
			    chart: {
			        renderTo: '"""+self.id+"""'
			    },
			    
			    rangeSelector: {
			        selected: 1
			    },
			    
			    title: {
			        text: '"""+self.title+"""'
			    },
                            legend: {
                                enabled: true,
                                align: "left",
                                layout: "vertical",
                                floating: "true",
                                verticalAlign: "top",
                                x: 100,
                                y: 60,
                            },
                            tooltip: {
                                formatter: function() {
                                    var s = '<b>'+ Highcharts.dateFormat('%a, %d %b %Y %H:%M:%S', this.x) +'</b><br/>';
                                    s += commitMap[this.x];
                                    $.each(this.points, function(i, point) {
                                        s += '<br/>'+ point.series.name +': '+point.y;
                                    });
                                    return s;
                                }
                            },			    
			    xAxis: {
			        maxZoom: 14 * 24 * 3600000 // fourteen days
			    },
			    yAxis: ["""
    	for col in self.columns:
            print "\t\t\t\t{ title: { text: '%s' } }," % col.upper()
        print """\t\t\t    ],
				
			    series: ["""
        num = 0
	for col in self.columns.keys():
            print "\t\t\t\t{ name: '%s', yAxis: %d, data: [" % (col, num)
            num += 1
            for row in self.rows:
                print "\t\t\t\t\t[%s, %s], " % (row.getDate(), row[col])
            print "\t\t\t\t]},"
        print """\t\t\t    ],
			});"""

class Graphs(dict):
    pass        

graphs = Graphs()
commits = {}

re_date = re.compile('^Date: (.*)')
re_testing = re.compile('^(\([0-9]+\) )?\s*Testing "(.*)" in (.*):\s*$')
re_commit = re.compile('(\S+) (.*?), commit: (.*)')
re_check = re.compile('^(\([0-9]+\) (#   )?)?!\s*(.*?)\s+(\S+)\s*$')
re_perf =  re.compile('^(\([0-9]+\) (#   )?)?!\s*(.*?)\s+PERF:\s*(.*?)\s+(\S+)\s*$')

for line in sys.stdin.readlines():
    line = line.rstrip()

    match = re_date.match(line)
    if (match):
        date = time.strptime(match.group(1), "%a, %d %b %Y %H:%M:%S +0200")
        continue
    
    match = re_testing.match(line)
    if match:
        what = match.group(2)
        where = match.group(3)

        match = re_commit.match(what)
        if match:
            date = time.strptime(match.group(2), "%Y-%m-%d %H:%M:%S")
            commit = match.group(3)
            commits[date] = commit
        
        (basename, ext) = os.path.splitext(os.path.basename(where))
        
        if what != "all": title = what
        else: title = basename
        try:
            graph = graphs[basename]
        except KeyError:
            graph = Graph(basename, title)
            graphs[basename] = graph
        continue

    match = re_perf.match(line)
    if match:
        perf = match.group(4)
        perf = perf.split()
        key = perf[0]
        val = perf[1]
        try:
            unit = perf[2]
        except:
            unit = None        

        graph[date][key] = val

graphs = [g for g in graphs.values() if len(g.columns)]


print """
<!DOCTYPE HTML>
<html>
    <head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<title>NUL Performance Plots</title>
	
	<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js"></script>
	<script type="text/javascript">
		var commitMap = {"""
for (d, v) in commits.items():
    print '\t\t\t%d: "%s",' % (1000*time.mktime(d), v.replace('"', '\\"'))
print """\t\t};
		$(function() {"""
for graph in graphs:
    graph.jschart()
print """
		});
	</script>
    </head>

    <body>
	<h1>NUL Performance Plots</h1>
	<script type="text/javascript" src="js/highstock.js"></script>
"""
for graph in graphs:
    print "	<h2>%s</h2>" % graph.title
    print '	<div id="%s" style="height: 400px"></div>' % graph.id
print """
    </body>
</html>
"""