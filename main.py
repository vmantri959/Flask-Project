from flask import Flask, render_template, request
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
    return render_template('main_page.html')
    

