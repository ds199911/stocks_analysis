#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from bs4 import BeautifulSoup
import requests
import os
import csv
import datetime
import xlsxwriter


# In[ ]:


def get_current_stock_price(ticker):
    if "." in ticker:
        ticker = ticker.replace(".","-")
    url = f"https://finance.yahoo.com/quote/{ticker}/"
    website_source = requests.get(url).text
    soup = BeautifulSoup(website_source, 'lxml')
    price = soup.find('span', {"class":'Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)'}) 
    #print('Symbol: ', ticker )
    #print(  'price: ', price.text)
    price.text.strip()
    if "," in price.text:
        price_lst = list(price.text)
        price_lst.remove(",")
        pr = ""
        for elem in price_lst:
            pr+=elem
        return float(pr)
    return float(price.text) 

    
class ExpDate:
    def __init__(self, exp_date):
        self.exp_date = exp_date
        self.options = []
    
    def calc_predicted_price(self):
        #Weightd Average of strike price with volume         # volume weighted average price
        numerator = 0
        denominator = 0
        for option in self.options:
            numerator += option.strike * option.volume   
            denominator += option.volume

        self.predicted_price = numerator / denominator

    def calc_percent_change(self, current_stock_price): 
        self.percent_change = (self.predicted_price - current_stock_price) / current_stock_price * 100
        
    def calc_volume_openinterest_ration(self):
        self.volopenration = (self.total_volume/self.total_openinterest) * 100

    def calc_total_volume(self):
        self.total_volume = 0
        for option in self.options:
            self.total_volume += option.volume
            
    def calc_total_openinterest(self):
        self.total_openinterest = 0
        for option in self.options:
            self.total_openinterest += option.openInterest
    

class Stock:
    def __init__(self, ticker):
        self.ticker = ticker
        self.price = get_current_stock_price(ticker)
        self.exp_dates = []


class OptionTrade:
    def __init__(self, ticker, strike, exp_date, last, volume, openInterest, iv):
        self.ticker = ticker
        self.strike = strike
        self.exp_date = exp_date
        self.last = last
        self.volume = volume
        self.openInterest = openInterest
        self.iv = iv
        self.total_cost = last * volume * 100.0


# In[ ]:


get_ipython().run_cell_magic('time', '', 'start = datetime.datetime.now() #For Optimization Purposes\n\nstocks_dict = {}\nfor file in os.listdir(\'data\'):\n    with open(f"data/{file}", \'r\') as csv_file:\n        csv_reader = csv.reader(csv_file)\n        next(csv_reader)\n        for line in csv_reader:\n            if len(line) > 2:\n                if (line[2].lower() == \'call\' and line[3] > line[1]) or (line[2].lower() == \'put\' and line[3] < line[1]): #for otm calls and puts\n                    mdy_list = line[4].split(\'/\')\n                    if int((mdy_list[2])) >2020:\n                        date = datetime.date(int(mdy_list[2]), int(mdy_list[0]), int(mdy_list[1]))\n                    else:\n                        date = datetime.date(int(mdy_list[2]) + 2000, int(mdy_list[0]), int(mdy_list[1]))\n                    if date > datetime.date.today():\n                        iv = float(line[13].replace(\'%\',\'\'))/100\n                        option = OptionTrade(line[0], float(line[3]), date, float(line[9]), int(line[10]), int(line[11]), iv)              \n                        if not option.ticker in stocks_dict:\n                            stocks_dict[option.ticker] = Stock(option.ticker)\n                        list_exp_dates = []\n                        for exp_date_obj in stocks_dict[option.ticker].exp_dates:\n                            list_exp_dates.append(exp_date_obj.exp_date)\n                        if not option.exp_date in list_exp_dates:\n                            stocks_dict[option.ticker].exp_dates.append(ExpDate(option.exp_date))\n                        for exp_date_obj in stocks_dict[option.ticker].exp_dates:\n                            if option.exp_date == exp_date_obj.exp_date:\n                                exp_date_obj.options.append(option)')


# In[ ]:


def sorting_exp_dates(exp_date_obj):
    return exp_date_obj.exp_date

for key, stock in stocks_dict.items():
    for exp_date in stock.exp_dates:
        exp_date.calc_predicted_price()
        exp_date.calc_percent_change(stock.price)
        exp_date.calc_total_volume()
        exp_date.calc_total_openinterest()
        exp_date.calc_volume_openinterest_ration()

    stock.exp_dates = sorted(stock.exp_dates, key=sorting_exp_dates)

def sorting_stocks(stock_obj):
    return abs(stock_obj.exp_dates[0].percent_change)

stocks_sorted_list = sorted(stocks_dict.values(), key=sorting_stocks, reverse=True)


workbook = xlsxwriter.Workbook('output/output.xlsx')
worksheet = workbook.add_worksheet('Unusual Options Predictions')

worksheet.write(0, 0, "Ticker")
worksheet.write(0, 1, "Option Date")
worksheet.write(0, 2, "Current Price")
worksheet.write(0, 3, "Predicted Price")
worksheet.write(0, 4, "Percent Change")
worksheet.write(0, 5, "Total Volume")
worksheet.write(0, 6, "Total Open Interest")
worksheet.write(0, 7, "Volume / Open Interest ratio%")


row = 1

for stock in stocks_sorted_list:

    for exp_date_obj in stock.exp_dates:
        worksheet.write(row, 0, stock.ticker)
        worksheet.write(row, 1, f'{exp_date_obj.exp_date.month}/{exp_date_obj.exp_date.day}/{exp_date_obj.exp_date.year}')
        worksheet.write(row, 2, stock.price)
        worksheet.write(row, 3, '{:.2f}'.format(exp_date_obj.predicted_price))
        worksheet.write(row, 4, '{:.2f}'.format(exp_date_obj.percent_change))
        worksheet.write(row, 5, exp_date_obj.total_volume)
        worksheet.write(row, 6, exp_date_obj.total_openinterest)
        worksheet.write(row, 7, exp_date_obj.volopenration)
        row += 1


workbook.close()


end = datetime.datetime.now()
print(end - start)


# In[ ]:


import pandas as pd
from datetime import datetime
from datetime import date
from datetime import timedelta
df = pd.read_excel("output/output.xlsx")


# In[ ]:


today = str(date.today())
today = datetime.strptime(today,"%Y-%m-%d")
for i in range(df.shape[0]):
    df.iloc[i,1] = datetime.strptime( df.iloc[i,1], "%m/%d/%Y")
df = df[(df.iloc[:,1] - today) < timedelta(days=31)]


# In[ ]:


df.sort_values(by=['Percent Change'], inplace=True, ascending = False)
call = df.drop_duplicates(['Ticker']).head(25)

df.sort_values(by=['Percent Change'], inplace=True, ascending = True)
put = df.drop_duplicates(['Ticker']).head(25)


# In[ ]:


call.to_excel("output\call.xlsx")


# In[ ]:


put.to_excel("output\put.xlsx")


# In[ ]:


print("Top 25 call options -->", list(call.iloc[:,0]))
print("")
print("Top 25 Put options -->", list(put.iloc[:,0]))


# In[ ]:


print("Top 18 call options -->") 
print(call.iloc[0:17,0].to_string(index = False))
print("")
print("Top 18 Put options -->") 
print(put.iloc[0:17,0].to_string(index = False))

call_str = call.iloc[0:17,0]
put_str = put.iloc[0:17,0]
c_str = ""
p_str = ""
for elem in call_str:
    c_str+="\""
    c_str+= str(elem)
    c_str+="\""
    c_str+= " "
for elem in put_str:
    p_str+="\""
    p_str+= str(elem)
    p_str+="\""
    p_str+= " "
print(c_str)
print(p_str)
