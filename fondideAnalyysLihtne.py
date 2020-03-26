import pandas as pd
import numpy as np
import datetime as dt

# Eeldatav kulu (sisaldab peidetud tasusid, fondi-fondide tasusid jne)
kulu = 0.015 # blogi.fin.ee/2014/09/pensionifondide-tasud-miks-ja-kuidas-neid-alandada/

# Impordi fondide mahud ja fondide NAV; korrasta kuupäevad
mahud       = pd.read_excel('Eesti fondide mahud.xlsx')
navid       = pd.read_excel('Eesti fondide NAV.xlsx')
thi         = pd.read_excel('THI.xlsx')
bundYield   = pd.read_excel('bund yield.xlsx')

# Fondide koondinfo
fondid = pd.merge(navid, mahud[['Kuupäev', 'ISIN', 'Maht']], on=['Kuupäev', 'ISIN'])
fondid['Kuupäev'] = pd.to_datetime(fondid['Kuupäev'], format='%d.%m.%Y') #.dt.date
fondid['Aasta'] = pd.to_datetime(fondid['Kuupäev'], format='%d.%m.%Y').dt.year
fondid = fondid.sort_values(by=['ISIN', 'Kuupäev'], ascending=True, na_position='first')

# Arvuta päevane log tootlus ja fondi kasum
fondid['Päevane tootlus'] = np.log(fondid['NAV']/fondid['NAV'].shift(1))
firstObs = fondid['ISIN'].eq(fondid['ISIN'].shift())
fondid['Puhastootlus'] = fondid['Maht'] * fondid['Päevane tootlus'] * firstObs

# Leia igale perioodile päevane inflatsioon ja raha väärtuse kahanemine
thi['Päevane inflatsioon'] = (1 + thi['thi']/100)**(1/256) -1
fondid = pd.merge(fondid, thi, on=['Aasta'])
fondid['Inflatsioon sööb ära'] = fondid['Maht'] * fondid['Päevane inflatsioon']

# Leia igale perioodile Bundi yield ja raha väärtuse kahanemine
bundYield['Aasta'] = bundYield['Date'].dt.year
bund = bundYield.groupby('Aasta')['Price'].mean().reset_index()
bund['Päevane riskivaba tootlus'] = (1 + bund['Price']/100)**(1/256) -1
fondid = pd.merge(fondid, bund, on=['Aasta'])
fondid['Saksa bundi tootlus'] = fondid['Maht'] * fondid['Päevane riskivaba tootlus']

# Jaota andmed aastasteks ajavahemikeks
vahemikud = pd.Series([dt.datetime(x, 3, 19) for x in range(2001, 2021)])
fondid['Periood'] = pd.cut(fondid['Kuupäev'], vahemikud)

# Teenustasude arvestus
fondid['Teenustasud'] = fondid['Maht'] * kulu / 265

# Impordi tulemused
fondid.to_excel("fondide_tulemused_19032020.xlsx", index=False)