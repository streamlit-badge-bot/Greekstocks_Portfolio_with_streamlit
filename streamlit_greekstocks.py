# -*- coding: utf-8 -*-
"""
Created on Sun Oct 25 13:19:50 2020

@author: ioannis.psomiadis@gmail.com
"""
import streamlit as st
import csv
import requests as req
from contextlib import closing
import pandas as pd
import numpy as np
from scipy import stats

import pypfopt
from pypfopt.efficient_frontier import EfficientFrontier,objective_functions
from pypfopt import expected_returns,risk_models #,plotting
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from pypfopt.risk_models import CovarianceShrinkage


@st.cache
def load_data():
    df=pd.DataFrame()
    stocks=['CENER.ATH','CNLCAP.ATH','TITC.ATH','AVAX.ATH','AVE.ATH','ADMIE.ATH','ALMY.ATH','ALPHA.ATH','AEGN.ATH',
            'ASCO.ATH','TATT.ATH','VIO.ATH','BIOSK.ATH','VOSYS.ATH','BYTE.ATH','GEBKA.ATH','GEKTERNA.ATH','PPC.ATH',
            'DOMIK.ATH','EEE.ATH','EKTER.ATH','ELIN.ATH','TELL.ATH','ELLAKTOR.ATH','ELPE.ATH','ELTON.ATH','ELHA.ATH','ENTER.ATH',
            'EPSIL.ATH','EYAPS.ATH','ETE.ATH','EYDAP.ATH','EUPIC.ATH','EUROB.ATH','EXAE.ATH','IATR.ATH','IKTIN.ATH','ILYDA.ATH',
            'INKAT.ATH','INLOT.ATH','INTERCO.ATH','INTET.ATH','INTRK.ATH','KAMP.ATH','KEKR.ATH','KEPEN.ATH',
            'KLM.ATH','KMOL.ATH','QUAL.ATH','QUEST.ATH','KRI.ATH','LAVI.ATH','LAMDA.ATH','KYLO.ATH','LYK.ATH','MEVA.ATH',
            'MERKO.ATH','MIG.ATH','MIN.ATH','MOH.ATH','BELA.ATH','BRIQ.ATH','MYTIL.ATH','NEWS.ATH','OLTH.ATH','PPA.ATH',
            'OLYMP.ATH','OPAP.ATH','HTO.ATH','OTOEL.ATH','PAIR.ATH','PAP.ATH','PASAL.ATH','TPEIR.ATH','PERF.ENAX',
            'PETRO.ATH','PLAT.ATH','PLAIS.ATH','PLAKR.ATH','PPAK.ATH','PROF.ATH','REVOIL.ATH','SAR.ATH','SPACE.ATH',
            'SPIR.ATH','TENERGY.ATH','TRASTOR.ATH','FLEXO.ATH','FOYRK.ATH','FORTH.ATH'           
            ]
    i=1
    for stock in stocks:
        dates=[]
        close=[]
        url='https://www.naftemporiki.gr/finance/Data/getHistoryData.aspx?symbol={}&type=csv'.format(stock)
        with closing(req.get(url, verify=True, stream=True)) as r:
            f = (line.decode('utf-8') for line in r.iter_lines())
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                dates.append(row[0])
                row[4]=row[4].replace(',','.')
                close.append(row[4])
                
        del dates[0]
        del close[0]
        df_temp=pd.DataFrame({'Dates':dates, stock:close})
        #df_temp=df_temp.apply(lambda x: x.str.replace(',','.'))
        df_temp=df_temp.tail(600)
        if i>1:
            df=df.join(df_temp.set_index('Dates'), on='Dates',how='inner')
        if i==1:
            df=df_temp
            i=i+1
           
    a=df['Dates']
    df=df.iloc[:,1:].astype('float')
    df.insert(0,'Dates', a)
    df.to_csv('greek_stockdata.csv')
    df=df.reset_index()
    df=df.set_index('Dates')
    return df

# Momentum score function
def momentum_score(ts):
    x = np.arange(len(ts))
    log_ts = np.log(ts)
    regress = stats.linregress(x, log_ts)
    annualized_slope = (np.power(np.exp(regress[0]), 252) -1) * 100
    return annualized_slope * (regress[2] ** 2)

#select stocks columns
def select_columns(data_frame, column_names):
    new_frame = data_frame.loc[:, column_names]
    return new_frame

#cumulative returns calculation
def cumulative_returns(stock,returns):
    res = (returns + 1.0).cumprod()
    res.columns = [stock]
    return res

#stock universe 
stocks=['CENER.ATH','CNLCAP.ATH','TITC.ATH','AVAX.ATH','AVE.ATH','ADMIE.ATH','ALMY.ATH','ALPHA.ATH','AEGN.ATH',
            'ASCO.ATH','TATT.ATH','VIO.ATH','BIOSK.ATH','VOSYS.ATH','BYTE.ATH','GEBKA.ATH','GEKTERNA.ATH','PPC.ATH',
            'DOMIK.ATH','EEE.ATH','EKTER.ATH','ELIN.ATH','TELL.ATH','ELLAKTOR.ATH','ELPE.ATH','ELTON.ATH','ELHA.ATH','ENTER.ATH',
            'EPSIL.ATH','EYAPS.ATH','ETE.ATH','EYDAP.ATH','EUPIC.ATH','EUROB.ATH','EXAE.ATH','IATR.ATH','IKTIN.ATH','ILYDA.ATH',
            'INKAT.ATH','INLOT.ATH','INTERCO.ATH','INTET.ATH','INTRK.ATH','KAMP.ATH','KEKR.ATH','KEPEN.ATH',
            'KLM.ATH','KMOL.ATH','QUAL.ATH','QUEST.ATH','KRI.ATH','LAVI.ATH','LAMDA.ATH','KYLO.ATH','LYK.ATH','MEVA.ATH',
            'MERKO.ATH','MIG.ATH','MIN.ATH','MOH.ATH','BELA.ATH','BRIQ.ATH','MYTIL.ATH','NEWS.ATH','OLTH.ATH','PPA.ATH',
            'OLYMP.ATH','OPAP.ATH','HTO.ATH','OTOEL.ATH','PAIR.ATH','PAP.ATH','PASAL.ATH','TPEIR.ATH','PERF.ENAX',
            'PETRO.ATH','PLAT.ATH','PLAIS.ATH','PLAKR.ATH','PPAK.ATH','PROF.ATH','REVOIL.ATH','SAR.ATH','SPACE.ATH',
            'SPIR.ATH','TENERGY.ATH','TRASTOR.ATH','FLEXO.ATH','FOYRK.ATH','FORTH.ATH'           
            ]
st.beta_set_page_config(layout="wide")
st.title('Βελτιστοποιημένο Χαρτοφυλάκιο Μετοχών του ΧΑ')
data_load_state = st.text('Loading data...')
# Load rows of data into the dataframe.
data = load_data()
# Notify the reader that the data was successfully loaded.
data_load_state.text("Done! (using st.cache)")
st.write('υπολογισμός βέλτιστου χαρτοφυλακίου από 90 μετοχές του ΧΑ βασισμένο'+
        'στην σύγχρονη θεωρία Χαρτοφυλακίου του Νομπελίστα Οικονομολόγου Harry Markowitz')
st.write('Βλ. στο παρακάτω παράθυρο την λίστα των μετοχών με τις ιστορικές '+
        'ημερήσιες τιμές κλεισίματός τους για τις τελευταίες '+str(len(data))+' μέρες')
st.write('Οι μετοχές που έχουν αρχικά επιλεγεί είναι οι παρακάτω που βλέπουμε στον πίνακα των τιμών κλεισίματος τους. Τα ονόματα τους είναι τα ονόματα των στηλών του πίνακα.')
st.sidebar.write('ΓΕΝΙΚΕΣ ΠΑΡΑΜΕΤΡΟΙ ΒΕΛΤΙΣΤΟΠΟΙΗΜΕΝΩΝ ΧΑΡΤΟΦΥΛΑΚΙΩΝ')
st.dataframe(data=data.iloc[:,1:])
df=data.iloc[:,1:]
q=st.sidebar.slider('Υπολογισμός με βάση τις τιμές των τελευταίων Χ ημερών', 60, 300, 180,10)
df_t=df.tail(q)
df_pct=df_t.pct_change()
df_cum_ret=pd.DataFrame()
for stock in stocks:
    df_cum_ret[stock]=cumulative_returns(stock, df_pct[stock])

st.write('Συσσωρευτικές αποδόσεις των παραπάνω μετοχών για τις Χ τελευταίες ημέρες')
st.dataframe(100*(df_cum_ret.iloc[-1:,:]-1))
m_cum_ret=pd.DataFrame((df_cum_ret.iloc[-1:,:])).max()
max_ret=round(100*(m_cum_ret.max()-1),0)
st.write('Πίνακας των ημερησίων ποσοστιαίων μεταβολών όλων των μετοχών για τις Χ ημέρες')
st.dataframe(df_pct)
corr_table = df_pct.corr()
corr_table['stock1'] = corr_table.index
corr_table = corr_table.melt(id_vars = 'stock1', var_name = 'stock2').reset_index(drop = True)
corr_table = corr_table[corr_table['stock1'] < corr_table['stock2']].dropna()
corr_table['abs_value'] = np.abs(corr_table['value'])
st.write('Πίνακας τικών συντελεστών συσχέτισης των μετοχών')
st.dataframe(corr_table)
#-----Γενικές παράμετροι
port_value=st.sidebar.slider('Αρχική επένδυση στο χαρτοφυλάκιο', 1000, 10000, 3000,1000)
riskmo = st.sidebar.checkbox('Επιλeγμένο επιλέγει το μοντέλο ρίσκου Ledoit Wolf αλλιώς χρησιμοποιεί τον πίνακα των συνδιακυμάνσεων')
weightsmo=st.sidebar.checkbox('Επιλεγμένο επιλέγει τον υπολογισμό των βαρών με βάση τον μέγιστο Sharpe Ratio αλλιώς με την ελάχιστη διακύμανση')
allocmo=st.sidebar.checkbox('Επιλεγμένο επιλέγει τον υπολογισμό του greedy_portfolio αλλιώς επιλέγει το lp_portfolio')
cutoff=st.sidebar.slider('Ελάχιστο Ποσοστό συμμετοχής μιας Μετοχής στο χαρτοφυλάκιο', 0.01, 0.30, 0.05)

c1,c2,c3,c4= st.beta_columns((1,1,1,1))
#-----Χαρτοφυλάκιο Νο1 γενικό
#Calculate portofolio mu and S
mu = expected_returns.mean_historical_return(df_t)
if riskmo:
    S = CovarianceShrinkage(df_t).ledoit_wolf()
else:
    S = risk_models.sample_cov(df_t)
# Optimise the portfolio 
ef = EfficientFrontier(mu, S, gamma=2) # Use regularization (gamma=1)
if weightsmo:
    weights = ef.max_sharpe()
else:
    weights = ef.min_volatility()
cleaned_weights = ef.clean_weights(cutoff=cutoff,rounding=3)
ef.portfolio_performance()

c1.subheader('Χαρτοφυλάκιο Νο1')
c1.write('Το προτινόμενο χαρτοφυλάκιο από τις ιστορικές τιμές των επιλεγμένων μετοχών έχει τα παρακάτω χαρακτηριστικά')
c1.write('Αρχική Αξία Χαρτοφυλακίου : '+str(port_value)+'€')
c1.write('Sharpe Ratio: '+str(round(ef.portfolio_performance()[2],2)))
c1.write('Απόδοση Χαρτοφυλακίο: '+str(round(ef.portfolio_performance()[0]*100,2))+'%')
c1.write('Μεταβλητότητα Χαρτοφυλακίου: '+str(round(ef.portfolio_performance()[1]*100,2))+'%')
# Allocate
latest_prices = get_latest_prices(df_t)
da =DiscreteAllocation(
    cleaned_weights,
    latest_prices,
    total_portfolio_value=port_value
    )
if allocmo:
    allocation = da.greedy_portfolio()[0]
    non_trading_cash=da.greedy_portfolio()[1]
else:
    allocation = da.lp_portfolio()[0]
    non_trading_cash=da.lp_portfolio()[1]
# Put the stocks and the number of shares from the portfolio into a df
symbol_list = []
cw=[]
num_shares_list = []
l_price=[]
tot_cash=[]
for symbol, num_shares in allocation.items():
    symbol_list.append(symbol)
    cw.append(round(cleaned_weights[symbol],3))
    num_shares_list.append(num_shares)
    l_price.append(round(latest_prices[symbol],2))
    tot_cash.append(round(num_shares*latest_prices[symbol],2))
    
df_buy=pd.DataFrame()
df_buy['stock']=symbol_list
df_buy['weights']=cw
df_buy['shares']=num_shares_list
df_buy['price']=l_price
df_buy['value']=tot_cash

c1.write(df_buy)
c1.write('Επενδυμένο σε μετοχές {0:.2f}€ ή το {1:.2f}% του χαρτοφυλακίου'.format(df_buy['value'].sum(),100*df_buy['value'].sum()/port_value))
c1.write('Εναπομείναντα μετρητά :{0:.2f}€ ή το {1:.2f}% του χαρτοφυλακίου'.format(port_value-df_buy['value'].sum(),100-100*df_buy['value'].sum()/port_value))
df_buy=df_buy.append({'stock':'CASH','weights': round(1-df_buy['value'].sum()/port_value,2),'shares':0,'price':0,'value':round(port_value-df_buy['value'].sum(),2)}, ignore_index=True)
print(df_buy)
if c1.button('Σώσε αυτό το Χαρτοφυλάκιο τύπου 1',key=1):
    df_buy.to_csv('Portfolio1.csv')
#------Χαρτοφυλάκιο Νο2
st.sidebar.write('Παράμετροι για το Χαρτοφυλάκιο Νο2')
c2.subheader('Χαρτοφυλάκιο Νο2')
c2.write('Θα γίνει ο ίδιος υπολογισμός αλλά ξεκινώντας από μικρότερο πλήθος μετοχών από τις αρχικές με βάση '+
         'τον υπολογισμό ενός δείκτη momentum και την κατάταξη των μετοχών σε φθίνουσα σειρά.'+
         ' Κατόπιν ο υπολογισμός του χαρτοφυλακίου έχει τις ίδιες επιλογές με το παραπάνω')
ps=st.sidebar.slider('Υπολογισμός με βάση αρχικά επιλεγμένο πλήθος μετοχών',5,30,10)
mom=st.sidebar.slider('Επιλογή με βάση την τιμή του mom',0,6,0)
portfolio_size=ps
#Calculate momentum and put the values in a dataframe
df_m=pd.DataFrame()
m_s=[]
stm=[]
for s in ['CENER.ATH','CNLCAP.ATH','TITC.ATH','AVAX.ATH','AVE.ATH','ADMIE.ATH','ALMY.ATH','ALPHA.ATH','AEGN.ATH',
            'ASCO.ATH','TATT.ATH','VIO.ATH','BIOSK.ATH','VOSYS.ATH','BYTE.ATH','GEBKA.ATH','GEKTERNA.ATH','PPC.ATH',
            'DOMIK.ATH','EEE.ATH','EKTER.ATH','ELIN.ATH','TELL.ATH','ELLAKTOR.ATH','ELPE.ATH','ELTON.ATH','ELHA.ATH','ENTER.ATH',
            'EPSIL.ATH','EYAPS.ATH','ETE.ATH','EYDAP.ATH','EUPIC.ATH','EUROB.ATH','EXAE.ATH','IATR.ATH','IKTIN.ATH','ILYDA.ATH',
            'INKAT.ATH','INLOT.ATH','INTERCO.ATH','INTET.ATH','INTRK.ATH','KAMP.ATH','KEKR.ATH','KEPEN.ATH',
            'KLM.ATH','KMOL.ATH','QUAL.ATH','QUEST.ATH','KRI.ATH','LAVI.ATH','LAMDA.ATH','KYLO.ATH','LYK.ATH','MEVA.ATH',
            'MERKO.ATH','MIG.ATH','MIN.ATH','MOH.ATH','BELA.ATH','BRIQ.ATH','MYTIL.ATH','NEWS.ATH','OLTH.ATH','PPA.ATH',
            'OLYMP.ATH','OPAP.ATH','HTO.ATH','OTOEL.ATH','PAIR.ATH','PAP.ATH','PASAL.ATH','TPEIR.ATH','PERF.ENAX',
            'PETRO.ATH','PLAT.ATH','PLAIS.ATH','PLAKR.ATH','PPAK.ATH','PROF.ATH','REVOIL.ATH','SAR.ATH','SPACE.ATH',
            'SPIR.ATH','TENERGY.ATH','TRASTOR.ATH','FLEXO.ATH','FOYRK.ATH','FORTH.ATH'           
            ]:
    stm.append(s)
    m_s.append(momentum_score(df_t[s]))
df_m['stock']=stm    
df_m['momentum'] = m_s
# Get the top momentum stocks for the period
df_m = df_m.sort_values(by='momentum', ascending=False).head(portfolio_size)
if mom==1:
    df_m=df_m[df_m['momentum']> df_m['momentum'].mean()-df_m['momentum'].std()]
if mom==2:
    df_m=df_m[df_m['momentum']> df_m['momentum'].mean()]
if mom==3:
    df_m=df_m[df_m['momentum']< df_m['momentum'].mean()+0.5*df_m['momentum'].std()]
if mom==4:
    df_m=df_m[df_m['momentum']< df_m['momentum'].mean()+df_m['momentum'].std()]    
if mom==5: 
    df_m=df_m[df_m['momentum']> 0]
if mom==6:
    df_m=df_m[df_m['momentum']< df_m['momentum'].mean()]
#print(df_m)
# Set the universe to the top momentum stocks for the period
universe = df_m['stock'].tolist()
# Create a df with just the stocks from the universe
df_tr = select_columns(df_t, universe)

#Calculate portofolio mu and S
mum = expected_returns.mean_historical_return(df_tr)
if riskmo:
    Sm = CovarianceShrinkage(df_tr).ledoit_wolf()
else:
    Sm = risk_models.sample_cov(df_tr)
# Optimise the portfolio 
efm = EfficientFrontier(mum, Sm, gamma=2) 

if weightsmo:
    weightsm = efm.max_sharpe()
else:
    #efm.add_objective(objective_functions.L2_reg, gamma=2)# Use regularization (gamma=1)
    weightsm = efm.min_volatility()
cleaned_weightsm = efm.clean_weights(cutoff=cutoff,rounding=3)
efm.portfolio_performance()
# Allocate
latest_pricesm = get_latest_prices(df_tr)
dam=DiscreteAllocation(
    cleaned_weightsm,
    latest_pricesm,
    total_portfolio_value=port_value
    )
if allocmo:
    allocationm = dam.greedy_portfolio()[0]
    non_trading_cashm=dam.greedy_portfolio()[1]
else:
    allocationm = dam.lp_portfolio()[0]
    non_trading_cashm=dam.lp_portfolio()[1]
# Put the stocks and the number of shares from the portfolio into a df
symbol_listm = []
mom=[]
cwm=[]
num_shares_listm = []
l_pricem=[]
tot_cashm=[]
for symbolm, num_sharesm in allocationm.items():
    symbol_listm.append(symbolm)
    cwm.append(round(cleaned_weightsm[symbolm],3))
    num_shares_listm.append(num_sharesm)
    l_pricem.append(round(latest_pricesm[symbolm],2))
    tot_cashm.append(round(num_sharesm*latest_pricesm[symbolm],2))
  
df_buym=pd.DataFrame()
df_buym['stock']=symbol_listm
df_buym['weights']=cwm
df_buym['shares']=num_shares_listm
df_buym['price']=l_pricem
df_buym['value']=tot_cashm

c2.write("Το προτινόμενο χαρτοφυλάκιο έχει τα παρακάτω χαρακτηριστικά")
c2.write('Αρχική Αξία Χαρτοφυλακίου : '+str(port_value)+'€')
c2.write('Sharpe Ratio: '+str(round(efm.portfolio_performance()[2],2)))
c2.write('Απόδοση Χαρτοφυλακίου: '+str(round(efm.portfolio_performance()[0]*100,2))+'%')
c2.write('Μεταβλητότητα Χαρτοφυλακίου: '+str(round(efm.portfolio_performance()[1]*100,2))+'%')
c2.write(df_buym)
c2.write('Επενδυμένο σε μετοχές {0:.2f}€ ή το {1:.2f}% του χαρτοφυλακίου'.format(df_buym['value'].sum(),100*df_buym['value'].sum()/port_value))
c2.write('Εναπομείναντα μετρητά :{0:.2f}€ ή το {1:.2f}% του χαρτοφυλακίου'.format(port_value-df_buym['value'].sum(),100-100*df_buym['value'].sum()/port_value))
df_buym=df_buym.append({'stock':'CASH','weights': round(1-df_buym['value'].sum()/port_value,2),'shares':0,'price':0,'value':round(port_value-df_buym['value'].sum(),2)}, ignore_index=True)
print(df_buym)
if c2.button('Σώσε αυτό το Χαρτοφυλάκιο τύπου 2',key=2):
    df_buym.to_csv('Portfolio2.csv')
#-----------------------------------------
st.sidebar.write('Παράμετροι για το Χαρτοφυλάκιο Νο3')
c3.subheader('Χαρτοφυλάκιο Νο3')
c3.write('Το προτινόμενο χαρτοφυλάκιο με τις μετοχές ελάχιστης συσχέτισης έχει τα παρακάτω χαρακτηριστικά')
me=st.sidebar.slider('Από Πόσες μετοχές ελάχιστης συσχέτισης? ',10,50,20,1)
c3.write('Αρχική Αξία Χαρτοφυλακίου : '+str(port_value)+'€')
highest_corr = corr_table.sort_values("abs_value",ascending = True).head(me)
hi_corr_stocks_list=list(set(list(highest_corr['stock1'])) | set(highest_corr['stock2']))
hi_corr_universe = hi_corr_stocks_list
# Create a df with just the stocks from the universe
df_hicorr = select_columns(df_t, hi_corr_universe)
muh = expected_returns.mean_historical_return(df_hicorr)
if riskmo:
    Sh = CovarianceShrinkage(df_hicorr).ledoit_wolf()
else:
    Sh = risk_models.sample_cov(df_hicorr)
# Optimise the portfolio 
efh = EfficientFrontier(muh, Sh, gamma=2) # Use regularization (gamma=1)
if weightsmo:
    weightsh = efh.max_sharpe()
else:
    weightsh = efh.min_volatility()
cleaned_weightsh = efh.clean_weights(cutoff=cutoff,rounding=3)
efh.portfolio_performance()

c3.write('Sharpe Ratio: '+str(round(efh.portfolio_performance()[2],2)))
c3.write('Απόδοση Χαρτοφυλακίο: '+str(round(efh.portfolio_performance()[0]*100,2))+'%')
c3.write('Μεταβλητότητα Χαρτοφυλακίου: '+str(round(efh.portfolio_performance()[1]*100,2))+'%')
# Allocate
latest_pricesh = get_latest_prices(df_hicorr)
dah =DiscreteAllocation(
    cleaned_weightsh,
    latest_pricesh,
    total_portfolio_value=port_value
    )
if allocmo:
    allocationh = dah.greedy_portfolio()[0]
    non_trading_cashh=dah.greedy_portfolio()[1]
else:
    allocationh = dah.lp_portfolio()[0]
    non_trading_cashh=dah.lp_portfolio()[1]
# Put the stocks and the number of shares from the portfolio in a df
symbol_listh = []
cwh=[]
num_shares_listh = []
l_priceh=[]
tot_cashh=[]
for symbolh, num_sharesh in allocationh.items():
    symbol_listh.append(symbolh)
    cwh.append(round(cleaned_weightsh[symbolh],3))
    num_shares_listh.append(num_sharesh)
    l_priceh.append(round(latest_pricesh[symbolh],2))
    tot_cashh.append(round(num_sharesh*latest_pricesh[symbolh],2))
    
df_buyh=pd.DataFrame()
df_buyh['stock']=symbol_listh
df_buyh['weights']=cwh
df_buyh['shares']=num_shares_listh
df_buyh['price']=l_priceh
df_buyh['value']=tot_cashh

c3.write(df_buyh)
c3.write('Επενδυμένο σε μετοχές {0:.2f}€ ή το {1:.2f}% του χαρτοφυλακίου'.format(df_buyh['value'].sum(),100*df_buyh['value'].sum()/port_value))
c3.write('Εναπομείναντα μετρητά :{0:.2f}€ ή το {1:.2f}% του χαρτοφυλακίου'.format(port_value-df_buyh['value'].sum(),100-100*df_buyh['value'].sum()/port_value))
df_buyh=df_buyh.append({'stock':'CASH','weights': round(1-df_buyh['value'].sum()/port_value,2),'shares':0,'price':0,'value':round(port_value-df_buyh['value'].sum(),2)}, ignore_index=True)
if c3.button('Σώσε αυτό το Χαρτοφυλάκιο τύπου 3',key=3):
    df_buyh.to_csv('Portfolio3.csv')

#-----Χαρτοφυλάκιο Νο4-------------------------------
st.sidebar.write('Παράμετροι για το Χαρτοφυλάκιο Νο4')
c4.subheader('Χαρτοφυλάκιο Νο4')
c4.write('Το προτινόμενο χαρτοφυλάκιο με τις μετοχές μέγιστης κεφαλοποιημένης απόδοσης για τις Χ ημέρες έχει τα παρακάτω χαρακτηριστικά')
mc=st.sidebar.slider('Από μετοχές ελάχιστης συσσωρευμένης απόδοσης τουλάχιστον ',10,int(max_ret),20,1)
c4.write('Αρχική Αξία Χαρτοφυλακίου : '+str(port_value)+'€')
c4.write('Επιλέγουμε από μετοχές με συσσωρευμένη απόδοση τουλάχιστον '+str(mc)+'%')
mc=float(mc/100+1)
m_c=[]
for rw in stocks:
    if float(m_cum_ret[rw])>=mc:
        m_c.append(rw)
hi_cum_universe=m_c

# Create a df with just the stocks from the universe
df_cum = select_columns(df_t, hi_cum_universe)
muc = expected_returns.mean_historical_return(df_cum)
if riskmo:
    Sc = CovarianceShrinkage(df_cum).ledoit_wolf()
else:
    Sc = risk_models.sample_cov(df_cum)
# Optimise the portfolio 
efc = EfficientFrontier(muc, Sc, gamma=2) # Use regularization (gamma=1)
if weightsmo:
    weightsc = efc.max_sharpe()
else:
    weightsc = efc.min_volatility()
cleaned_weightsc = efc.clean_weights(cutoff=cutoff,rounding=3)
efc.portfolio_performance()

c4.write('Sharpe Ratio: '+str(round(efc.portfolio_performance()[2],2)))
c4.write('Απόδοση Χαρτοφυλακίο: '+str(round(efc.portfolio_performance()[0]*100,2))+'%')
c4.write('Μεταβλητότητα Χαρτοφυλακίου: '+str(round(efc.portfolio_performance()[1]*100,2))+'%')
# Allocate
latest_pricesc = get_latest_prices(df_cum)
dac =DiscreteAllocation(
    cleaned_weightsc,
    latest_pricesc,
    total_portfolio_value=port_value
    )
if allocmo:
    allocationc = dac.greedy_portfolio()[0]
    non_trading_cashc=dac.greedy_portfolio()[1]
else:
    allocationc = dac.lp_portfolio()[0]
    non_trading_cashc=dac.lp_portfolio()[1]
# Put the stocks and the number of shares from the portfolio in a df
symbol_listc = []
cwc =[]
num_shares_listc = []
l_pricec=[]
tot_cashc=[]
for symbolc, num_sharesc in allocationc.items():
    symbol_listc.append(symbolc)
    cwc.append(round(cleaned_weightsc[symbolc],3))
    num_shares_listc.append(num_sharesc)
    l_pricec.append(round(latest_pricesc[symbolc],2))
    tot_cashc.append(round(num_sharesc*latest_pricesc[symbolc],2))
    
df_buyc=pd.DataFrame()
df_buyc['stock']=symbol_listc
df_buyc['weights']=cwc
df_buyc['shares']=num_shares_listc
df_buyc['price']=l_pricec
df_buyc['value']=tot_cashc

c4.write(df_buyc)
c4.write('Επενδυμένο σε μετοχές {0:.2f}€ ή το {1:.2f}% του χαρτοφυλακίου'.format(df_buyc['value'].sum(),100*df_buyc['value'].sum()/port_value))
c4.write('Εναπομείναντα μετρητά :{0:.2f}€ ή το {1:.2f}% του χαρτοφυλακίου'.format(port_value-df_buyc['value'].sum(),100-100*df_buyc['value'].sum()/port_value))
df_buyc=df_buyc.append({'stock':'CASH','weights': round(1-df_buyc['value'].sum()/port_value,2),'shares':0,'price':0,'value':round(port_value-df_buyc['value'].sum(),2)}, ignore_index=True)
if c4.button('Σώσε αυτό το Χαρτοφυλάκιο τύπου 4',key=4):
    df_buyc.to_csv('Portfolio4.csv')

#-----------------------------------------------
st.write('Εαν έχεις προηγουμένως σώσει ένα Χαροφυλάκιο πατήστε ένα από τα παρακάτω κουμπιά, ανάλογα τον τύπο, για να δούμε πόσο αποδίδει τώρα')    
if c1.button('Χαρτοφυλάκιο τύπου 1'):
    df1=pd.read_csv('Portfolio1.csv')
    df1=df1.iloc[:,1:]
    df1=df1.rename(columns={'price':'bought price'})
    last_price=[]
    new_values=[]
    new_weights=[]
    pct=[]
    for stock in list(df1.iloc[:-1]['stock']):
        last_price.append(df.iloc[-1][stock])
        nv=df1.loc[df1['stock']==stock,'shares'].values[0]*df.iloc[-1][stock]
        new_values.append(nv)
        pt=round(100*(df.iloc[-1][stock]/df1.loc[df1['stock']==stock,'bought price'].values[0]-1),2)
        pct.append(pt)
    last_price.append(0)
    pct.append(0)
    df1['last price']=last_price
    new_values.append(df1.iloc[-1]['value'])
    df1['new value']=new_values
    df1['pct_change%']=pct
    new_port_value=df1['new value'].sum()
    for stock in list(df1.iloc[:-1]['stock']):
        new_weights.append(df1.loc[df1['stock']==stock,'shares'].values[0]*df.iloc[-1][stock]/new_port_value)
    new_weights.append(df1.iloc[-1]['new value']/ new_port_value)
    df1['new weights']=new_weights    
    c1.write('Αρχική αξία του Χαροφυλακίου ήταν :'+str(df1['value'].sum())+'€')
    c1.write('Τώρα είναι :'+str(round(new_port_value,2))+'€')
    c1.write(' δηλ. έχουμε μια απόδοση ίση με '+str(100*round(new_port_value/df1['value'].sum()-1,4))+'%')
    c1.dataframe(df1)
    
  
if c2.button('Χαρτοφυλάκιο τύπου 2'):
    df2=pd.read_csv('Portfolio2.csv')
    df2=df2.iloc[:,1:]
    df2=df2.rename(columns={'price':'bought price'})
    last_price=[]
    new_values=[]
    new_weights=[]
    pct=[]
    for stock in list(df2.iloc[:-1]['stock']):
        last_price.append(df.iloc[-1][stock])
        nv2=df2.loc[df2['stock']==stock,'shares'].values[0]*df.iloc[-1][stock]
        new_values.append(nv2)
        pt=round(100*(df.iloc[-1][stock]/df2.loc[df2['stock']==stock,'bought price'].values[0]-1),2)
        pct.append(pt)
    last_price.append(0)
    pct.append(0)
    df2['last price']=last_price
    new_values.append(df2.iloc[-1]['value'])
    df2['new value']=new_values
    df2['pct_change%']=pct
    new_port_value2=df2['new value'].sum()
    for stock in list(df2.iloc[:-1]['stock']):
        new_weights.append(df2.loc[df2['stock']==stock,'shares'].values[0]*df.iloc[-1][stock]/new_port_value2)
    new_weights.append(df2.iloc[-1]['new value']/ new_port_value2)
    df2['new weights']=new_weights    
    c2.write('Αρχική αξία του Χαροφυλακίου ήταν :'+str(df2['value'].sum())+'€')
    c2.write('Τώρα είναι :'+str(round(new_port_value2,2))+'€')
    c2.write('δηλ. έχουμε μια απόδοση ίση με '+str(100*round(new_port_value2/df2['value'].sum()-1,4))+'%')
    c2.dataframe(df2)
    
if c3.button('Χαρτοφυλάκιο τύπου 3'):
    df3=pd.read_csv('Portfolio3.csv')
    df3=df3.iloc[:,1:]
    df3=df3.rename(columns={'price':'bought price'})
    last_price=[]
    new_values=[]
    new_weights=[]
    pct=[]
    for stock in list(df3.iloc[:-1]['stock']):
        last_price.append(df.iloc[-1][stock])
        nv3=df3.loc[df3['stock']==stock,'shares'].values[0]*df.iloc[-1][stock]
        new_values.append(nv3)
        pt=round(100*(df.iloc[-1][stock]/df3.loc[df3['stock']==stock,'bought price'].values[0]-1),2)
        pct.append(pt)
    last_price.append(0)
    pct.append(0)
    df3['last price']=last_price
    new_values.append(df3.iloc[-1]['value'])
    df3['new value']=new_values
    df3['pct_change%']=pct
    new_port_value3=df3['new value'].sum()
    for stock in list(df3.iloc[:-1]['stock']):
        new_weights.append(df3.loc[df3['stock']==stock,'shares'].values[0]*df.iloc[-1][stock]/new_port_value3)
    new_weights.append(df3.iloc[-1]['new value']/ new_port_value3)
    df3['new weights']=new_weights    
    c3.write('Αρχική αξία του Χαροφυλακίου ήταν :'+str(df3['value'].sum())+'€')
    c3.write('Τώρα είναι :'+str(round(new_port_value3,2))+'€')
    c3.write('δηλ. έχουμε μια απόδοση ίση με '+str(100*round(new_port_value3/df3['value'].sum()-1,4))+'%')
    c3.dataframe(df3) 
    
if c4.button('Χαρτοφυλάκιο τύπου 4'):
    df4=pd.read_csv('Portfolio4.csv')
    df4=df4.iloc[:,1:]
    df4=df4.rename(columns={'price':'bought price'})
    last_price=[]
    new_values=[]
    new_weights=[]
    pct=[]
    for stock in list(df4.iloc[:-1]['stock']):
        last_price.append(df.iloc[-1][stock])
        nv4=df4.loc[df4['stock']==stock,'shares'].values[0]*df.iloc[-1][stock]
        new_values.append(nv4)
        pt=round(100*(df.iloc[-1][stock]/df4.loc[df4['stock']==stock,'bought price'].values[0]-1),2)
        pct.append(pt)
    last_price.append(0)
    pct.append(0)
    df4['last price']=last_price
    new_values.append(df4.iloc[-1]['value'])
    df4['new value']=new_values
    df4['pct_change%']=pct
    new_port_value4=df4['new value'].sum()
    for stock in list(df4.iloc[:-1]['stock']):
        new_weights.append(df4.loc[df4['stock']==stock,'shares'].values[0]*df.iloc[-1][stock]/new_port_value4)
    new_weights.append(df4.iloc[-1]['new value']/ new_port_value4)
    df4['new weights']=new_weights    
    c4.write('Αρχική αξία του Χαροφυλακίου ήταν :'+str(df4['value'].sum())+'€')
    c4.write('Τώρα είναι :'+str(round(new_port_value4,2))+'€')
    c4.write('δηλ. έχουμε μια απόδοση ίση με '+str(100*round(new_port_value4/df4['value'].sum()-1,4))+'%')
    c4.dataframe(df4)    
