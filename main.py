from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
#Global constants
name_of_stocks = []
bid_prices = []
ask_prices = []

class Stock(db.Model):
    name = db.Column(db.String, primary_key = True)
    bid_price = db.Column(db.Float, nullable = False)
    ask_price = db.Column(db.Float, nullable = False)

def add_updated_stock_list():
    stocks = Stock.query.all()
    name_of_stocks.clear()
    bid_prices.clear()
    ask_prices.clear()
    for stock in stocks:
        name_of_stocks.append(stock.name)
        bid_prices.append(stock.bid_price)
        ask_prices.append(stock.ask_price)

@app.route('/')
def main_page():
    stocks = Stock.query.all()
    for stock in stocks:
        stock_info = requests.get('https://api.tdameritrade.com/v1/marketdata/' + stock.name + '/quotes?apikey=BECNZHSKXG7K2GNI4FKBG13KBXXQBGJR')
        stock_info = json.loads(stock_info.text)
        bid_price = stock_info[stock.name]['bidPrice']
        ask_price = stock_info[stock.name]['askPrice']
        try:
            stock.bid_price = bid_price
            stock.ask_price = ask_price
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            print('Failed to update stock')
    add_updated_stock_list()
    return render_template('main_page.html', name_of_stocks = name_of_stocks, bid_prices = bid_prices, ask_prices = ask_prices)

@app.route('/add_stock')
def add_stock_page():
    return render_template('add_stock.html')

@app.route('/remove_stock')
def remove_stock_page():
    add_updated_stock_list()
    return render_template('remove_stock.html', name_of_stocks = name_of_stocks)

@app.route('/add_stock_show_main_page', methods=['POST'])
def add_stock_show_main_page():
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
    add_updated_stock_list()
    return render_template('main_page.html', name_of_stocks = name_of_stocks, bid_prices = bid_prices, ask_prices = ask_prices)

@app.route('/delete_stock_show_main_page', methods=['POST'])
def delete_stock_show_main_page():
    deleted_stock_name = request.form['deleted_stock']
    stock_to_delete = Stock.query.filter_by(name = deleted_stock_name).first()
    try:
        db.session.delete(stock_to_delete)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        print('Failed to delete stock')
    add_updated_stock_list()
    return render_template('main_page.html', name_of_stocks = name_of_stocks, bid_prices = bid_prices, ask_prices = ask_prices)
