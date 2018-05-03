#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
    Set of utility function in order to retrieve datas (news and
    stock data), build the newsletter template and send the email.
"""


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import bs4
import requests
import json
import pandas as pd
import numpy as np


sending_email = "finance.newsletter.test@gmail.com"
sending_password = "aqwxszedc"


def get_stock(symbol):

    """
    Returns a pandas DataFrame with (Open, High, Low, Close, Volume) columns
    for the specific symbol and daily time_interval.
    Returns None if an exception occurs.
    """

    try:
        json_data = requests.request('GET', 'https://www.alphavantage.co'+
        '/query?function=TIME_SERIES_DAILY&symbol='+symbol+'&apikey=KNZX').json()
        json_data['Time Series (Daily)']
        data_frame = pd.DataFrame.from_records(json_data['Time Series (Daily)'])

        data_frame = data_frame.transpose()
        data_frame.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        return data_frame

    except:
        print("Error while loading data")
        return None


def daily_variation(symbol):

    """
        Returns an array with the last stock price of the
        symbol and the daily percentage change in price.
    """

    stock_data = get_stock(symbol)
    pct_change = (float(stock_data['Close'][0])
        - float(stock_data['Close'][1]))/float(stock_data['Close'][1])
    return [float(stock_data['Close'][0]), np.round(pct_change*100, 2)]


def get_news():

    """
        Returns two dictionnary object containing news articles
        informations. The first one is a short version, with little
        informations and the second one contains all the informations.
    """

    API_KEY = 'd913f4f1287a42819abc66f428e0fad4'
    sources = 'bloomberg'+ ',' + 'the-wall-street-journal' + ',' + 'les-echos' + ',' + 'business-insider'
    all_news = []
    short_news = []

    try:
        request_result = requests.request("GET",
                                          "https://newsapi.org/v2/"
                                          +"top-headlines?sources="+sources
                                          +"&sortBy=top&apiKey="+API_KEY)

        all_news = request_result.json()['articles']
        all_news = sorted(all_news, key=lambda k: k['publishedAt'],
                            reverse=True)

        for article in all_news:
            short_news.append({'source':article['source']['name'],
                                'title':article['title']})

        return short_news, all_news

    except:
        print('Error while loading the sources')
        return None, None




def send_mail(sending_email, sending_password, list_emails, subject, html_file):

    """
        Send a mail to a list of emails. The body is an html
        formated file template.
    """

    # Creating the server, and handling all connections steps
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.connect("smtp.gmail.com",587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sending_email, sending_password)

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sending_email

    with open(html_file, 'r') as myfile:
        html_data = myfile.read()

    # Adding the html core template
    html_email = MIMEText(html_data, 'html')

    msg.attach(html_email)

    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    for email in list_emails :
        msg['To'] = email
        server.sendmail(sending_email, email, msg.as_string())
    server.quit()


def build_newsletter(data, html_file_template, html_file):

    """
        Creates the html newsletter template with informations
        provided by the user. Saves the template in a file.
    """

    try:
        # Retrieve the empty newsletter template
        with open(html_file_template, 'r') as myfile:
            html_data = myfile.read()
            newsletter_template = bs4.BeautifulSoup(html_data, 'lxml')

        # Adding main message to the html file
        main_message = newsletter_template.find("p", {"id": "main-message"})
        # Clearing content
        newsletter_template.find("td", {"id": "main-message-container"}).string = ''
        main_message.string = data['main-message']
        newsletter_template.find("td",
                                {"id": "main-message-container"}).append(main_message)

        # Retrieve companies informations
        with open("../assets/json-files/companies.json", mode='r', encoding='utf-8') as f:
            companies = json.load(f)

        for security in data['securities']:
            with open("../assets/html-templates/left-img-div.html", 'r') as myfile:
                html_data = myfile.read()
                soup_left = bs4.BeautifulSoup(html_data, 'lxml')
            temp_stock = soup_left.find("tr", {"id":"stock"})
            price, variation = daily_variation(security)
            if(variation > 0):
                src="https://image.ibb.co/i9EK67/trending_up.png"
                temp_stock.find('img')['src'] = src
            else:
                src="https://image.ibb.co/b7wMKS/trending_down.png"
                temp_stock.find('img')['src'] = src
                temp_stock['id'] = security
            name = [item['label'] for item in companies if item['value']==security]
            name = name[0]

            temp_stock.find('h2', {'id':'h2-stock'}).string = name + ' ('+ security + ')'
            temp_stock.find('p', {'id':'p-stock'}).string = str(price) + ' $'
            temp_stock.find('p', {'id':'p2-stock'}).string = str(variation) + ' %'

            newsletter_template.find("div", {"id": "stock-container"}).append(temp_stock)

        newsletter_template.find("div", {"id":"news-container"}).string = ''
        for article in data['articles']:
            with open("../assets/html-templates/right-img-div.html", 'r') as myfile:
                html_data = myfile.read()
                soup_left = bs4.BeautifulSoup(html_data, 'lxml')
            temp_news = soup_left.find("tr", {"id":"news"})
            temp_news.find('h2', {'id':'title'}).string = article['title']
            temp_news.find('p', {'id':'description'}).string = article['description']
            temp_news.find('a', {'id':'button'})['href'] = article['url']
            temp_news.find('img', {'id':'image'})['src'] = article['urlToImage']
            newsletter_template.find("div", {"id":"news-container"}).append(temp_news)

        # Finally, we write the modified template in a specific file
        modified_template = '../assets/html-templates/modified-template.html'
        with open(modified_template, 'wb') as myfile:
            myfile.write(newsletter_template.encode("utf-8"))

        return True
    except:
        return False


def send_newsletter(data):

    """
        Function called by the Dash interface in order to make
        the link between the interface and core functions.
        Calls the function to create the template with the data
        provided by the interface and then calls the function
        to send the newsletter.
    """

    now = datetime.datetime.now()
    subject = "Financial newsletter {}".format(now.strftime("%m/%d/%Y"))
    html_file_template = '../assets/html-templates/newsletter-template.html'
    html_file = '../assets/html-templates/modified-template.html'
    success_build = build_newsletter(data, html_file_template, html_file)
    list_emails = ["maxence.coupet@gmail.com"]
    try:
        if(success_build):
            send_mail(sending_email, sending_password, list_emails,
                        subject, html_file)
            print('Newsletter successfully sent to : {}'.format(list_emails))
        else:
            raise Exception('Build error', 'An error occured during building')
    except:
        print('Error while creating the newsletter, please try again')
