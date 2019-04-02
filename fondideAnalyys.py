import pandas as pd
import numpy as np

# Eeldatav kulu (sisaldab peidetud tasusid, ei tea sisenemis/valjumiskulude osas)
kulu = 0.015 # blogi.fin.ee/2014/09/pensionifondide-tasud-miks-ja-kuidas-neid-alandada/

# Impordi fondide mahud
mahud = pd.read_excel('Eesti fondide mahud.xlsx')
mahud['Kuupäev'] = pd.to_datetime(mahud['Kuupäev'], format='%d.%m.%Y')

# Impordi fondide NAV
navid = pd.read_excel('Eesti fondide NAV.xlsx')
navid['Kuupäev'] = pd.to_datetime(navid['Kuupäev'], format='%d.%m.%Y')

# Impordi inflatsiooniandmed ja reinvesteeritava DAXi indeks
thi = pd.read_excel('THI.xlsx')
thi['thi'] = thi['thi'] / 100

gdax = pd.read_excel('gdax.xlsx')
gdax = gdax[gdax['Date'].dt.month == 12]
gdax['DAX aasta tootlus'] = gdax['Adj Close'].pct_change()

# Arvuta paevased tootlused
navid = navid.sort_values(by=['ISIN', 'Kuupäev'], ascending=True, na_position='first')
navid['Päevane tootlus'] = np.log(navid['NAV']/navid['NAV'].shift(1))
navid.loc[navid['ISIN'] != navid['ISIN'].shift(1), 'Päevane tootlus'] = 0

# Fondide koondinfo
fondid = pd.merge(navid, mahud[['Kuupäev', 'ISIN', 'Maht']], on=['Kuupäev', 'ISIN'])
fondid.isna().sum()
fondid.describe()
fondid.info(verbose=True)

# Arvuta fondi kasum 
fondid['Kasum'] = fondid['Maht'] * fondid['Päevane tootlus']

# Arvuta fondi maht aasta lopus
grouped = fondid.groupby(['ISIN', 'Year'])
fondi_maht = grouped.last()
aasta_maht = fondi_maht.groupby(fondi_maht['Kuupäev'].dt.year)['Maht'].agg(['sum']).reset_index()
aasta_maht = aasta_maht.rename(columns={'sum': 'Kogumaht'})

# Arvuta koikide fondide kasum aastat loikes
zen = fondid.groupby(fondid['Kuupäev'].dt.year)['Kasum'].agg(['sum']).reset_index()
zen = zen.rename(columns={'sum': 'Kogukasum'})

# Liida tulemused ja arvuta kogukulu
zen = pd.merge(aasta_maht, zen, on='Kuupäev')
zen['Aasta keskmine maht'] = zen['Kogumaht'].rolling(2, min_periods=1).mean()
zen['EE aasta tootlus'] = zen['Kogukasum'] / zen['Aasta keskmine maht']
zen['EE aasta kulu'] = zen['Aasta keskmine maht'] * kulu

# Pane kylge inflatsiooni ja DAXi andmed
zen = pd.merge(zen, thi[['aasta','thi']], left_on='Kuupäev', right_on='aasta')
zen = pd.merge(zen, gdax, left_on='Kuupäev', right_on=gdax['Date'].dt.year)
lopp = zen[['aasta','Aasta keskmine maht','EE aasta tootlus','thi','DAX aasta tootlus']]

koond = pd.DataFrame({'Aasta':[], 'aasta_EE':[], 'aasta_DAX':[], 'cagr_EE':[], 'cagr_DAX':[], 'cum_thi':[], 'keskmine_EE':[], 'kaalutud_keskmine_EE':[]})
# Arvuta tootlused
for i in range(0, len(lopp)):   
    kala = lopp.tail(len(lopp)-i)
    aasta = lopp.iloc[i]['aasta'] 
    b1 = lopp.iloc[i]['EE aasta tootlus'] 
    b2 = lopp.iloc[i]['DAX aasta tootlus']     
    a1 = (1 + kala['EE aasta tootlus']).values.cumprod() - 1
    b3 = ((((a1[-1]+1))) ** (1/(len(zen)-i))) - 1
    a2 = (1 + kala['DAX aasta tootlus']).values.cumprod() - 1
    b4 = ((((a2[-1]+1))) ** (1/(len(zen)-i))) - 1
    a3 = (1 + kala['thi']).values.cumprod() - 1    
    b5 = ((((a3[-1]+1))) ** (1/(len(zen)-i))) - 1
    b6 = kala['EE aasta tootlus'].mean()   
    b7 = np.average(kala['EE aasta tootlus'], weights=kala['Aasta keskmine maht'])    
       
    koond.loc[i] = [aasta, b1, b2, b3, b4, b5, b6, b7]
