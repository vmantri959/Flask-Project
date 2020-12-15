from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, IntegerField, DecimalField, validators
import requests
import json
from datetime import datetime

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

name_of_options = []
strike_prices = []
current_prices_underlying = []
type_of_options = []
statuses = []
days_to_expiration = []

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
    expiration_date = db.Column(db.DateTime, nullable = False) 

class StockForm(Form):
    ticker = StringField('Enter Stock/ETF Ticker', [validators.DataRequired()])
    quantity = IntegerField('Enter Quantity', [validators.DataRequired()])
    stock_bought_at_this_price = StringField('Enter the price at which stock/ETF was bought at', [validators.DataRequired()])

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

def add_updated_option_list():
    options = Option.query.all()
    name_of_options.clear()
    strike_prices.clear()
    current_prices_underlying.clear()
    statuses.clear()
    type_of_options.clear()
    days_to_expiration.clear()
    for option in options:
        name_of_options.append(option.name)
        strike_prices.append(option.strike_price)
        current_prices_underlying.append(option.current_price)
        statuses.append(option.status)
        type_of_options.append(option.type_of_option)
        days_to_expiration.append(str((option.expiration_date - datetime.now()).days + 1))

def update_stocks_and_options():
    stocks = Stock.query.all()
    for stock in stocks:
        stock_info = requests.get('https://api.tdameritrade.com/v1/marketdata/' + stock.name + '/quotes?apikey=BECNZHSKXG7K2GNI4FKBG13KBXXQBGJR')
        stock_info = json.loads(stock_info.text)
        bid_price = stock_info[stock.name]['bidPrice']
        ask_price = stock_info[stock.name]['askPrice']
        try:
            stock.price = (int(((bid_price + ask_price) / 2) * 100)) / 100 
            stock.current_market_value = round(float(stock.price) * float(stock.quantity), 2)
            stock.profit_or_loss = round(float(stock.current_market_value) - float(stock.cost), 2)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            print('Failed to update stock')
    options = Option.query.all()
    for option in options:
        stock_info = requests.get('https://api.tdameritrade.com/v1/marketdata/' + option.name + '/quotes?apikey=BECNZHSKXG7K2GNI4FKBG13KBXXQBGJR')
        stock_info = json.loads(stock_info.text)
        bid_price = stock_info[option.name]['bidPrice']
        ask_price = stock_info[option.name]['askPrice']
        try:
            current_price = (int(((bid_price + ask_price) / 2) * 100)) / 100 
            if current_price > option.strike_price:
                if option.type_of_option == 'Call':
                   option.status = 'In the money'
                else:
                    option.status = 'Out of the money'
            elif current_price == strike_price:
                option.status = 'At the money'
            else:
                if option.type_of_option == 'Call':
                    option.status = 'Out of the money'
                else:
                    option.status = 'In the money'
            option.current_price = current_price
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            print('Failed to update option')

@app.route('/')
def main_page():
    update_stocks_and_options()
    add_updated_stock_list()
    add_updated_option_list()
    return render_template('main_page.html', name_of_stocks = name_of_stocks, prices = prices, assets = assets, quantities = quantities, costs = costs, current_market_values = current_market_values, profit_or_losses = profit_or_losses, name_of_options = name_of_options, strike_prices = strike_prices, current_prices_underlying = current_prices_underlying, type_of_options = type_of_options, statuses = statuses, days_to_expiration = days_to_expiration)

@app.route('/add_stock')
def add_stock_page():
    form = StockForm()
    return render_template('add_stock.html', form = form)

@app.route('/add_option')
def add_option_page():
    return render_template('add_option.html')

@app.route('/remove_stock')
def remove_stock_page():
    add_updated_stock_list()
    return render_template('remove_stock.html', name_of_stocks = name_of_stocks)

@app.route('/remove_option')
def remove_option_page():
    add_updated_option_list()
    return render_template('remove_option.html', name_of_options = name_of_options)

@app.route('/add_stock_show_main_page', methods=['POST', 'GET'])
def add_stock_show_main_page():
    form = StockForm(request.form)
    if request.method == 'POST' and form.validate():
        stock_name = form.ticker.data
        quantity = int(form.quantity.data)
        stock_bought_at_this_price = float(form.stock_bought_at_this_price.data)
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
    update_stocks_and_options()
    add_updated_stock_list()
    add_updated_option_list()
    return render_template('main_page.html', name_of_stocks = name_of_stocks, prices = prices, assets = assets, quantities = quantities, costs = costs, current_market_values = current_market_values, profit_or_losses = profit_or_losses, name_of_options = name_of_options, strike_prices = strike_prices, current_prices_underlying = current_prices_underlying, type_of_options = type_of_options, statuses = statuses, days_to_expiration = days_to_expiration)

@app.route('/add_option_show_main_page', methods=['POST', 'GET'])
def add_option_show_main_page():
    if request.method == 'POST':
        underlying = request.form['underlying']
        strike_price = float(request.form['strike_price'])
        type_of_option = request.form['type_of_option']
        expiration_date = request.form['expiration_date'].split('-')
        expiration_date = datetime(int(expiration_date[0]), int(expiration_date[1]), int(expiration_date[2])) 
        #Send API request
        stock_info = requests.get('https://api.tdameritrade.com/v1/marketdata/' + underlying + '/quotes?apikey=BECNZHSKXG7K2GNI4FKBG13KBXXQBGJR')
        if stock_info.text != '{}':
            stock_info = json.loads(stock_info.text)
            bid_price = stock_info[underlying]['bidPrice']
            ask_price = stock_info[underlying]['askPrice']
            price = round((bid_price + ask_price) / 2, 2)
            if price > strike_price:
                if type_of_option == 'Call':
                    status = 'In the money'
                else:
                    status = 'Out of the money'
            elif price == strike_price:
                status = 'At the money'
            else:
                if type_of_option == 'Call':
                    status = 'Out of the money'
                else:
                    status = 'In the money'
            try:
                new_option = Option(status = status, name = underlying, type_of_option = type_of_option, strike_price = strike_price, current_price = price, expiration_date = expiration_date)
                db.session.add(new_option)
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()
        else:
            print('Option could not be added')
    update_stocks_and_options()
    add_updated_stock_list()
    add_updated_option_list()
    return render_template('main_page.html', name_of_stocks = name_of_stocks, prices = prices, assets = assets, quantities = quantities, costs = costs, current_market_values = current_market_values, profit_or_losses = profit_or_losses, name_of_options = name_of_options, strike_prices = strike_prices, current_prices_underlying = current_prices_underlying, type_of_options = type_of_options, statuses = statuses, days_to_expiration = days_to_expiration)


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
    update_stocks_and_options()
    add_updated_stock_list()
    add_updated_option_list()
    return render_template('main_page.html', name_of_stocks = name_of_stocks, prices = prices, assets = assets, quantities = quantities, costs = costs, current_market_values = current_market_values, profit_or_losses = profit_or_losses, name_of_options = name_of_options, strike_prices = strike_prices, current_prices_underlying = current_prices_underlying, type_of_options = type_of_options, statuses = statuses, days_to_expiration = days_to_expiration)

@app.route('/delete_option_show_main_page', methods = ['POST', 'GET'])
def delete_option_show_main_page():
    if request.method == 'POST':
        deleted_option_name = request.form['deleted_option']
        option_to_delete = Option.query.filter_by(name = deleted_option_name).first()
        try:
            db.session.delete(option_to_delete)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            print('Failed to delete option')
    update_stocks_and_options()
    add_updated_stock_list()
    add_updated_option_list()
    return render_template('main_page.html', name_of_stocks = name_of_stocks, prices = prices, assets = assets, quantities = quantities, costs = costs, current_market_values = current_market_values, profit_or_losses = profit_or_losses, name_of_options = name_of_options, strike_prices = strike_prices, current_prices_underlying = current_prices_underlying, type_of_options = type_of_options, statuses = statuses, days_to_expiration = days_to_expiration)
