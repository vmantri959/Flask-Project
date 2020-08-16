from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Stock(db.Model):
    name = db.Column(db.String, primary_key = True)
    bid_price = db.Column(db.Float, nullable = False)
    ask_price = db.Column(db.Float, nullable = False)

@app.route('/')
def main_page():
    name_of_stocks = []
    bid_prices = []
    ask_prices = []
    stocks = Stock.query.all()
    for stock in stocks:
        name_of_stocks.append(stock.name)
        bid_prices.append(stock.bid_price)
        ask_prices.append(stock.ask_price)
    return render_template('main_page.html', name_of_stocks = name_of_stocks, bid_prices = bid_prices, ask_prices = ask_prices)

@app.route('/add_stock')
def add_stock_page():
    return render_template('add_stock.html')

@app.route('/success_or_failure', methods=['POST'])
def show_success_or_failure_page():
    stock_name = request.form['stock_name']
    stock_info = requests.get('https://api.tdameritrade.com/v1/marketdata/' + stock_name + '/quotes?apikey=BECNZHSKXG7K2GNI4FKBG13KBXXQBGJR')
    if stock_info.text != '{}':
        stock_info = json.loads(stock_info.text)
        bid_price = stock_info[stock_name]['bidPrice']
        ask_price = stock_info[stock_name]['askPrice']
        new_stock = Stock(name = stock_name, bid_price = bid_price, ask_price = ask_price)
        try:
            db.session.add(new_stock)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            print('Failed due to exception')
    else:
        print('Stock could not be added')
    name_of_stocks = []
    bid_prices = []
    ask_prices = []
    stocks = Stock.query.all()
    for stock in stocks:
        name_of_stocks.append(stock.name)
        bid_prices.append(stock.bid_price)
        ask_prices.append(stock.ask_price)
    return render_template('main_page.html', name_of_stocks = name_of_stocks, bid_prices = bid_prices, ask_prices = ask_prices)
