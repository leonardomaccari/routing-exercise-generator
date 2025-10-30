#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 14:39:11 2023

@author: Leonardo Maccari
"""

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import networkx as nx
import matplotlib.pyplot as plt
import os
  
css_string ='''
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
<li> The adopted routing is {routing} </li>
<li> The order of the generation of messages follows the numeric order of routers </li>
<li> The order of the arrival of messages follows the numeric order of routers </li>
</ul>

Write down the list of generated messages, and the final routing table. 
You can omit messages that are received but do not alter the routing table of the receing router.
'''

def save_document(g, rp, args, fname='./exercise.pdf'):
    base_url = os.path.dirname(os.path.realpath(__file__))
    font_config = FontConfiguration()
    body = ''
    body += format_titlepage(g)
    body += exercise_text.format(routing=args.r)
    body += format_solution(rp.get_messages())
    body += rp.format_rt()
    html = HTML(string=body, base_url=base_url)
    css = CSS(string=css_string, font_config=font_config)
    html.write_pdf(
        f'{fname}', stylesheets=[css],
        font_config=font_config)

def format_titlepage(g):
    pos = nx.spring_layout(g)
    nx.draw(g, pos, with_labels=True)
    labels = nx.get_edge_attributes(g,'cost')
    nx.draw_networkx_edge_labels(g, pos, edge_labels=labels)
    plt.savefig('/tmp/graph.png')
    
    title='<h1>Routing Exercise</h1>'
    img = """
    <div style="text-align: center;">
     <img width="400" src="/tmp/graph.png">
    </div>\n"""
    return title+img

def format_solution(updates):
    solutions = '<div style="break-before: page;">\n' + \
                '<h2>Message sequence</h2>\n' + \
                '<ol>\n' + \
                '\n'.join(['<li>' + event + '</li>' for event in updates]) + \
                '\n</div>\n</ol>'

    
    return  solutions
        
        
        
        
