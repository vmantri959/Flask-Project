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
prices = []
assets = []
quantities = []
costs = []
current_market_values = []
profit_or_losses =[]
statuses = []

class Stock(db.Model):
    name = db.Column(db.String, primary_key = True)
    price = db.Column(db.Float, nullable = False)
    quantity = db.Column(db.String, nullable = False) 
    asset_type = db.Column(db.String, nullable = False)
    cost = db.Column(db.String, nullable = False)     
    current_market_value = db.Column(db.String, nullable = False) 
    profit_or_loss = db.Column(db.Float, nullable = False) 

class Option(db.Model):
    name = db.Column(db.String, primary_key = True)
    strike_price = db.Column(db.Float, nullable = False)
    current_price = db.Column(db.Float, nullable = False)
    status = db.Column(db.String, nullable = False)
    type_of_option = db.Column(db.String, nullable = False)

def add_updated_stock_list():
    stocks = Stock.query.all()
    name_of_stocks.clear()
    prices.clear()
    assets.clear()
    quantities.clear()
    costs.clear()
    current_market_values.clear()
    profit_or_losses.clear()
    for stock in stocks:
        name_of_stocks.append(stock.name)
        prices.append(stock.price)
        assets.append(stock.asset_type)
        quantities.append(stock.quantity)
        costs.append(stock.cost)
        current_market_values.append(stock.current_market_value)
        profit_or_losses.append(stock.profit_or_loss)

@app.route('/')
def main_page():
    stocks = Stock.query.all()
    for stock in stocks:
        stock_info = requests.get('https://api.tdameritrade.com/v1/marketdata/' + stock.name + '/quotes?apikey=BECNZHSKXG7K2GNI4FKBG13KBXXQBGJR')
        stock_info = json.loads(stock_info.text)
        bid_price = stock_info[stock.name]['bidPrice']
        ask_price = stock_info[stock.name]['askPrice']
        try:
            stock.price = (int(((bid_price + ask_price) / 2) * 100)) / 100 
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            print('Failed to update stock')
    add_updated_stock_list()
    return render_template('main_page.html', name_of_stocks = name_of_stocks, prices = prices, assets = assets, quantities = quantities, costs = costs, current_market_values = current_market_values, profit_or_losses = profit_or_losses)

@app.route('/add_stock')
def add_stock_page():
    return render_template('add_stock.html')

@app.route('/add_option')
def add_option_page():
    return render_template('add_option.html')

@app.route('/remove_stock')
def remove_stock_page():
    add_updated_stock_list()
    return render_template('remove_stock.html', name_of_stocks = name_of_stocks)

@app.route('/add_stock_show_main_page', methods=['POST', 'GET'])
def add_stock_show_main_page():
    if request.method == 'POST':
        stock_name = request.form['stock_name']
        quantity = int(request.form['quantity'])
        stock_bought_at_this_price = float(request.form['stock_bought_at_this_price'])
        stock_info = requests.get('https://api.tdameritrade.com/v1/marketdata/' + stock_name + '/quotes?apikey=BECNZHSKXG7K2GNI4FKBG13KBXXQBGJR')
        if stock_info.text != '{}':
            stock_info = json.loads(stock_info.text)
            bid_price = stock_info[stock_name]['bidPrice']
            ask_price = stock_info[stock_name]['askPrice']
            asset_type = stock_info[stock_name]['assetType']
            price = round((bid_price + ask_price) / 2, 2)

            new_stock = Stock(name = stock_name, price = price, quantity = quantity, cost = round(quantity * stock_bought_at_this_price, 2), current_market_value = price * quantity, profit_or_loss = round(quantity * (price - stock_bought_at_this_price), 2), asset_type = asset_type)
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
    return render_template('main_page.html', name_of_stocks = name_of_stocks, prices = prices, assets = assets, quantities = quantities, costs = costs, current_market_values = current_market_values, profit_or_losses = profit_or_losses)

@app.route('/add_option_show_main_page', methods=['POST', 'GET'])
def add_option_show_main_page():
    if request.method == 'POST':
        underlying = request.form['underlying']
        strike_price = request.form['strike_price']
        type_of_option = request.form['type_of_option']

@app.route('/delete_stock_show_main_page', methods=['POST', 'GET'])
def delete_stock_show_main_page():
    if request.method == 'POST':
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
    return render_template('main_page.html', name_of_stocks = name_of_stocks, prices = prices, assets = assets, quantities = quantities, costs = costs, current_market_values = current_market_values, profit_or_losses = profit_or_losses)
