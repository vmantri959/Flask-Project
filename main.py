from flask import Flask, render_template, request
import requests
app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('main_page.html')

@app.route('/add_stock')
def add_stock_page():
    return render_template('add_stock.html')

@app.route('/success_or_failure', methods=['POST'])
def show_success_or_failure_page():
    stock_name = request.form['stock_name']
    stock_info = requests.get('https://api.tdameritrade.com/v1/marketdata/' + stock_name + '/quotes?apikey=BECNZHSKXG7K2GNI4FKBG13KBXXQBGJR')
    if stock_info.text == '{}':
        print('Please enter a valid stock/ETF')
    else:
        print('Valid stock/ETF')

    return render_template('main_page.html')
    

