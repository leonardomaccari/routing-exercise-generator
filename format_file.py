#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 14:39:11 2023

@author: Leonardo Maccari
"""
import os
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import networkx as nx
import matplotlib.pyplot as plt


css_string = '''
    @font-face {
        font-family: Gentium;
        src: url(https://example.com/fonts/Gentium.otf);
    }
    h1 { font-family: Gentium }
    h2 { font-family: Gentium }
    ol {
       list-style-type: none;
       font-family: "Lucida Console", "Courier New", monospace;
       }
    dl {
       font-family: "Lucida Console", "Courier New", monospace;
       }


'''

exercise_text = '''
Consider the network in the figure and assume that:
<ul>
<li> The adoupted routing is {routing} </li>
<li> The order of the generation of messages follows the numeric order of routers </li>
<li> The order of the arrival of messages follows the numeric order of routers </li>
</ul>

Write down the list of generated messages, and the final routing table.
You can omit messages that are received but do not alter the routing table of the receing router.
'''.format(routing='LS')


def save_document(g, updates, rt, args, fname='./exercise.pdf'):
    base_url = os.path.dirname(os.path.realpath(__file__))
    font_config = FontConfiguration()
    body = ''
    body += format_titlepage(g)
    body += exercise_text.format(routing=args.r)
    body += format_solution(updates)
    body += format_rt(rt, args.r)
    html = HTML(string=body, base_url=base_url)
    css = CSS(string=css_string, font_config=font_config)
    html.write_pdf(
        f'{fname}', stylesheets=[css],
        font_config=font_config)


def format_titlepage(g):
    pos = nx.spring_layout(g)
    nx.draw(g, pos, with_labels=True)
    labels = nx.get_edge_attributes(g, 'cost')
    nx.draw_networkx_edge_labels(g, pos, edge_labels=labels)
    plt.savefig('/tmp/graph.png')

    title = '<h1>Routing Exercise</h1>'
    img = """
    <div style="text-align: center;">
     <img width="400" src="/tmp/graph.png">
    </div>\n"""
    return title + img


def format_solution(updates):
    solutions = '<div style="break-before: page;">\n' + \
                '<h2>Message sequence</h2>\n' + \
                '<ol>\n' + \
                '\n'.join(['<li>' + event + '</li>' for event in updates]) + \
                '\n</div>\n</ol>'

    return solutions


def format_rt(rt, routing):
    rt_text = '<h2>Final Routing Table</h2>\n'
    rt_text += '<dl>\n'
    for host in rt:
        h_rt = rt[host]
        item = f'<dt>{host}</dt>\n'
        item += '<ol>\n'
        for dest in h_rt:
            if routing == 'LS':
                item += f'<li>{dest}: path={
                    "->".join(
                        str(elem) for elem in h_rt[dest]["path"])}, cost={
                    h_rt[dest]["cost"]}</li>\n'
            else:
                item += f'<li>{dest}: nh={
                    h_rt[dest]["nh"]}, cost={
                    h_rt[dest]["cost"]}</li>\n'
        item += '</ol>\n'
        rt_text += item
    rt_text += '</dl>\n'
    return rt_text
