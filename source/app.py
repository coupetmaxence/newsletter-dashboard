#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
    Dash application in order to make easier the creation of a
    newsletter for financial markets.
    Functionalities :
        - Personalized main message for the daily summary on
            the top of the newsletter
        - Choice of securities (from a JSON file in the asset folder)
            to display in the newsletter in order to target
            key securities for each desk
        - Choice of news to display (Now the sources are fixed but
            it could be enhanced in further version)
        - Automatically build the html newletter with above informations
            and send it to a predefined list of emails
            (Now the list of email is fixed in python, could be a
            parameter in the dash app later)
"""


import dash
import json
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
from dash.dependencies import Input, Output, State, Event
import requests
from newsletter import get_news, send_newsletter


error_flag = False
app = dash.Dash()

try:
    with open("../assets/json-files/companies.json", mode='r',
                encoding='utf-8') as f:
        data = json.load(f)

    short_news, all_news = get_news()
    if(short_news==None or all_news==None):
        raise Exception('News feed error')
except:
    error_flag = True


app.layout = html.Div(style={'width':'100%'}, children=[
    html.H1(children='Newsletter creator tool'),
    html.Div(children='''

    '''),
    html.H4(children='Main message'),
    dcc.Textarea(
        id='main-message',
        placeholder='Enter main message',
        value='',
        style={'width': '100%'}),
    html.H4(children='Securities to follow'),
    dcc.Dropdown(
        id='securities',
        options=data,
        multi=True),
    html.H4(children='News to display'),
    html.Div(style={"word-wrap": "break-word"}, children=[
        dt.DataTable(
            # Initialise the rows
            rows=short_news,
            row_selectable=True,
            filterable=False,
            sortable=False,
            selected_row_indices=[],
            id='table',
            resizable=True
        )]),
        html.Br(),
        html.Div(id='output-container-button',
                 children=''),
        html.Div(id='button', style={'margin-left':'20em'},
                 children=[html.Button('Send newsletter', id='send-mail')])
])


@app.callback(Output('output-container-button','children' ),
                    [Input('send-mail', 'n_clicks')],
                    [State('main-message', 'value'),
                    State('securities', 'value'),
                    State('table', 'selected_row_indices')])
def callback(n_click,  main_message, securities, row_indices):
    if(n_click != None):
        message = {}
        message['main-message'] = main_message
        articles = []
        if(securities==None or row_indices==None):
            return 'Check your entries'
        else:
            for row in row_indices:
                articles.append(all_news[row])
            message['articles'] = articles
            message['securities'] = securities
            send_newsletter(message)
            return 'Newsletter sent'


app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})


if __name__ == '__main__':
    if(error_flag==False):
        app.run_server(debug=True)
