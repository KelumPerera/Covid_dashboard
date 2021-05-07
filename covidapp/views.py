from django.shortcuts import render
from django.http import HttpResponse
import requests
import json
from datetime import datetime
import requests
import pandas as pd
import numpy as np
import pytz    # $ pip install pytz
import tzlocal
from dateutil import parser
from copy import deepcopy

confirmedGlobal=pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv',encoding='utf-8',na_values=None)
totalCount = confirmedGlobal[confirmedGlobal.columns[-1]].sum()
barPlotData = confirmedGlobal[['Country/Region',confirmedGlobal.columns[-1]]].groupby('Country/Region').sum()
barPlotData = barPlotData.reset_index()
barPlotData.columns = ['Country/Region','Totals']
barPlotData = barPlotData.sort_values(by='Totals', ascending=False)

barPlotTotals = barPlotData['Totals'].values.tolist()
barPlotNames = barPlotData['Country/Region'].values.tolist()




deathGLobal=pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv',encoding='utf-8',na_values=None)
recoverGlobal=pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv',encoding='utf-8',na_values=None)


total_confirmed = confirmedGlobal.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], value_vars=confirmedGlobal.columns[4:], var_name='date', value_name='confirmed')
total_deaths = deathGLobal.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], value_vars=deathGLobal.columns[4:], var_name='date', value_name='death')
total_recovered = recoverGlobal.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], value_vars=recoverGlobal.columns[4:], var_name='date', value_name='recovered')


covid_data = total_confirmed.merge(right = total_deaths, how = 'left', on = ['Province/State', 'Country/Region', 'date', 'Lat', 'Long'])
covid_data = covid_data.merge(right = total_recovered, how = 'left', on = ['Province/State', 'Country/Region', 'date', 'Lat', 'Long'])
covid_data['date'] = pd.to_datetime(covid_data['date'])
del confirmedGlobal, deathGLobal,recoverGlobal, total_confirmed, total_deaths, total_recovered 
covid_data['recovered'] = covid_data['recovered'].fillna(0)
covid_data['active'] = covid_data['confirmed'] - covid_data['death'] - covid_data['recovered']



covid_data.sort_values(by=['Province/State', 'Country/Region', 'Lat', 'Long', 'date'], inplace=True)
covid_data['Province/State'] = np.where(pd.isna(covid_data['Province/State']), covid_data['Country/Region'], covid_data['Province/State'] )


_covid_data_global = covid_data.groupby(["date"]).agg({'confirmed':'sum','death':'sum','recovered':'sum','active':'sum'}).reset_index()
covid_data_global = pd.DataFrame(_covid_data_global)
covid_data_global['Province/State'] = "World"
covid_data_global['Country/Region'] = "World"
covid_data_global['Lat'] = 0
covid_data_global['Long'] = 0

covid_data = covid_data.append(covid_data_global)
covid_data.sort_values(by=['Province/State', 'Country/Region', 'Lat', 'Long', 'date'], inplace=True)


covid_data['confirmed_daily'] = np.where(((covid_data['Country/Region']==covid_data['Country/Region'].shift(1)) & (covid_data['Province/State']==covid_data['Province/State'].shift(1)) ),covid_data['confirmed'] - covid_data['confirmed'].shift(1),0)

covid_data['death_daily'] = np.where(((covid_data['Country/Region']==covid_data['Country/Region'].shift(1)) & (covid_data['Province/State']==covid_data['Province/State'].shift(1)) ),covid_data['death'] - covid_data['death'].shift(1),0)
covid_data['recovered_daily'] = np.where(((covid_data['Country/Region']==covid_data['Country/Region'].shift(1)) & (covid_data['Province/State']==covid_data['Province/State'].shift(1)) ),covid_data['recovered'] - covid_data['recovered'].shift(1),0)
covid_data['active_daily'] = np.where(((covid_data['Country/Region']==covid_data['Country/Region'].shift(1)) & (covid_data['Province/State']==covid_data['Province/State'].shift(1)) ),covid_data['active'] - covid_data['active'].shift(1),0)

_covid_data_confirmed_daily = covid_data.groupby(['Country/Region','Province/State']).rolling('7D', on="date")['confirmed_daily'].mean().reset_index()
covid_data_confirmed_daily = pd.DataFrame(_covid_data_confirmed_daily)
covid_data_confirmed_daily = covid_data_confirmed_daily.rename(columns={"confirmed_daily":'cases_new_movingAvg_7D'})
covid_data = covid_data.merge(covid_data_confirmed_daily, how='left', left_on=['date', 'Country/Region','Province/State'] , right_on = ['date', 'Country/Region','Province/State'])
del covid_data_confirmed_daily, _covid_data_confirmed_daily

_covid_data_death_daily = covid_data.groupby(['Country/Region','Province/State']).rolling('7D', on="date")['death_daily'].mean().reset_index()
covid_data_death_daily = pd.DataFrame(_covid_data_death_daily)
covid_data_death_daily = covid_data_death_daily.rename(columns={"death_daily":'death_new_movingAvg_7D'})
covid_data = covid_data.merge(covid_data_death_daily, how='inner', left_on=['date', 'Country/Region','Province/State'] , right_on = ['date', 'Country/Region','Province/State'])
del covid_data_death_daily, _covid_data_death_daily

_covid_data_recovered_daily = covid_data.groupby(['Country/Region','Province/State']).rolling('7D', on="date")['recovered_daily'].mean().reset_index()
covid_data_recovered_daily = pd.DataFrame(_covid_data_recovered_daily)
covid_data_recovered_daily = covid_data_recovered_daily.rename(columns={"recovered_daily":'recoverd_new_movingAvg_7D'})

covid_data = covid_data.merge(covid_data_recovered_daily, how='inner', left_on=['date', 'Country/Region','Province/State'] , right_on = ['date', 'Country/Region','Province/State'])
del covid_data_recovered_daily, _covid_data_recovered_daily

_covid_data_active_daily = covid_data.groupby(['Country/Region','Province/State']).rolling('7D', on="date")['active_daily'].mean().reset_index()
covid_data_active_daily = pd.DataFrame(_covid_data_active_daily)
covid_data_active_daily = covid_data_active_daily.rename(columns={"active_daily":'active_new_movingAvg_7D'})

covid_data = covid_data.merge(covid_data_active_daily, how='inner', left_on=['date', 'Country/Region','Province/State'] , right_on = ['date', 'Country/Region','Province/State'])
del covid_data_active_daily, _covid_data_active_daily



url = "https://vaccovid-coronavirus-vaccine-and-treatment-tracker.p.rapidapi.com/api/npm-covid-data/"

summaryHeaders = {
    'x-rapidapi-key': "f5c9641e4cmsh8f9dc091aeea75ap1a9fd6jsnb45bb74ec924",
    'x-rapidapi-host': "vaccovid-coronavirus-vaccine-and-treatment-tracker.p.rapidapi.com"
    }

summaryResponse = requests.request("GET", url, headers=summaryHeaders).json()


vaccine_url = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.json"
vaccinationsData = requests.request("GET", vaccine_url).json()


mylist = []
for x in range(0, int(len(summaryResponse))):
    country_text = summaryResponse[x]['Country']
    #country_text = country_text.replace("-", " ")
    mylist.append(country_text)

mylist.sort()
mylist.insert(0, mylist.pop(mylist.index('World')))

# Line Chart data
#covid_data_for_line = covid_data[covid_data['Country/Region']==str(selectedCountry)].copy()
#totalCount = confirmedGlobal[confirmedGlobal.columns[-1]].sum()
#barPlotData = confirmedGlobal[['Country/Region',confirmedGlobal.columns[-1]]].groupby('Country/Region').sum()
#covid_data_for_line = covid_data_for_line.reset_index()
#barPlotData.columns = ['Country/Region','Totals']
#covid_data_for_line = covid_data_for_line.sort_values(by='date', ascending=False)

#linePlot_active_daily = covid_data_for_line['active_daily'].values.tolist()
#linePlot_date = covid_data_for_line['date'].values.tolist()

# Create your views here.
def covidView(request):
    if request.method=="POST":
        selectedCountry = request.POST['selectedCountry']
        
    else:
        selectedCountry = "Sri Lanka"

    
    #mylist = []
    #for x in range(0, int(len(summaryResponse))):
    #    country_text = summaryResponse[x]['Country']
        #country_text = country_text.replace("-", " ")
    #    mylist.append(country_text)
    #mylist.sort()
    #mylist.insert(0, mylist.pop(mylist.index('World')))
    mylist.insert(0, mylist.pop(mylist.index(str(selectedCountry))))

    #selectedCountry = selectedCountry.replace(" ", "-")
    """
    for x in range(0, int(len(response)) ):
        selectedCountry = selectedCountry.replace(" ", "-")
        selectedCountry = selectedCountry.replace("World", "All")
        if selectedCountry == response['response'][x]['country']:
            date = pd.to_datetime(str(response['response'][x]['time']))
        selectedCountry = selectedCountry.replace("-", " ")
        selectedCountry = selectedCountry.replace("All", "World")
    """

    for x in range(0, int(len(summaryResponse)) ):
        if selectedCountry == summaryResponse[x]['Country']:
            #date = pd.to_datetime(str(summaryResponse[x]['time']))
            infectionRisk = summaryResponse[x]['Infection_Risk']
            fatalityRate = summaryResponse[x]['Case_Fatality_Rate']
            recoveryProporation = summaryResponse[x]['Recovery_Proporation']
            testPercentage = summaryResponse[x]['Test_Percentage']
            new = summaryResponse[x]['NewCases']
            active = summaryResponse[x]['ActiveCases']
            critical = summaryResponse[x]['Serious_Critical']
            recovered = summaryResponse[x]['TotalRecovered']
            recoveredtoday = summaryResponse[x]['NewRecovered']
            total = summaryResponse[x]['TotalCases']
            deaths = summaryResponse[x]['TotalDeaths']
            deathstoday = summaryResponse[x]['NewDeaths']
            population = summaryResponse[x]['Population']
            tests = summaryResponse[x]['TotalTests']
            activePercentage = float("{:.2f}".format(int(active)/int(total)*100))


    
    summaryResponse_df = pd.json_normalize(summaryResponse)
    now1 = datetime.now()
    print(now1)
    if selectedCountry == "World":
        summaryResponse_df['Population'] = pd.to_numeric(summaryResponse_df['Population'])
        population = summaryResponse_df.loc[:, 'Population'].sum()
        summaryResponse_df['TotalTests'] = pd.to_numeric(summaryResponse_df['TotalTests'])
        tests = summaryResponse_df.loc[:, 'TotalTests'].sum()
        infectionRisk = float("{:.2f}".format(int(total)/int(population)*100))
        testPercentage = float("{:.2f}".format(int(tests)/int(population)*100))
        #activePercentage = float("{:.2f}".format(int(active)/int(total)*100))

    now2 = datetime.now()
    print(now2)            
        
    #selectedCountry = selectedCountry.replace("-", " ")
    
    vaccinations = "None"
    fully_Vaccinations = ""
    vaccine_Updated_Date = ""
    vacc = ""
    rename_country = {"USA":"United States","UK":"United Kingdom","UAE":"United Arab Emirates","S. Korea":"South Korea","Ivory Coast":"Cote d'Ivoire","DRC":"Democratic Republic of Congo","Cabo Verde":"Cape Verde","Curaçao":"Curacao","Turks and Caicos":"Turks and Caicos Islands","Timor-Leste":"Timor","St. Vincent Grenadines":"Saint Vincent and the Grenadines"}
    for c in rename_country:
        selectedCountry = selectedCountry.replace(c,str(rename_country[c]))
    #selectedCountry = selectedCountry.replace("USA", "United States")
    
    for y in range(0, len(vaccinationsData)):
        
        if selectedCountry == vaccinationsData[y]['country']:
            print("Yes")
            print(str(selectedCountry))    
            try:
                peopleFully_vaccinations =  vaccinationsData[y]['data'][-1]['people_fully_vaccinated']
            except Exception as e:
                print("Pep Vacc", e)
                peopleFully_vaccinations = 0
                pass
            try:
                People_vaccinations =  vaccinationsData[y]['data'][-1]['people_vaccinated']    
            except Exception as e:
                print("Pep Vacc", e)
                People_vaccinations = 0
                pass
            
            try:
                total_vaccinations =  vaccinationsData[y]['data'][-1]['total_vaccinations']
            except Exception as e:
                print("Pep Vacc", e)
                total_vaccinations = 0
                # KeyError:
                pass
            
            #fully_Vaccinations =  vaccinationsData[y]['data'][-1]['people_fully_vaccinated']
            vaccine_Updated_Date = (str(vaccinationsData[y]['data'][-1]['date']))
            print(vaccine_Updated_Date)
            
        else:
            #People_vaccinations = 0
            #eopleFully_vaccinations = 0
            #total_vaccinations = 0
            pass
    try:
        if 'total_vaccinations' not in locals():
            total_vaccinations = 0
        if 'peopleFully_vaccinations' not in locals():
            peopleFully_vaccinations= 0
        if ('People_vaccinations' in locals() and People_vaccinations != 0) :
            vaccinatedProporation = float("{:.2f}".format(int(People_vaccinations)/int(population)*100))
        else:
            vaccinatedProporation = float("{:.2f}".format(int(total_vaccinations)/int(population)*100))
        if 'People_vaccinations' not in locals():
            People_vaccinations = 0
        

        

    except Exception as e:
        # ZeroDivisionError , ValueError
        vaccinatedProporation = 0
    
        #querystring = {'continent': selectedCountry }

        #response2 = requests.request("GET", url, headers=headers_history, params=querystring).json()

    # Line Chart data
    print(str(selectedCountry))
    rename_country = {"United States":"US","South Korea":"Korea, South","Taiwan":"Taiwan*", }
    for c in rename_country:
        selectedCountry = selectedCountry.replace(c,str(rename_country[c]))
    covid_data_for_line = covid_data[((covid_data['Country/Region']==str(selectedCountry)) |(covid_data['Province/State']==str(selectedCountry)))].copy()
    covid_data_for_line = covid_data_for_line.sort_values(by='date', ascending=True)
    if covid_data_for_line.empty == False:
        if (covid_data_for_line['confirmed_daily'][covid_data_for_line.index[-1]] == 0):
            covid_data_for_line.drop(covid_data_for_line.tail(1).index,inplace=True)
        
    covid_data_for_line['date'] = covid_data_for_line['date'].dt.strftime("%Y-%m-%d")

    linePlot_confirmed_daily = covid_data_for_line['confirmed_daily'].values.tolist()
    linePlot_cases_new_movingAvg_7D = covid_data_for_line['cases_new_movingAvg_7D'].values.tolist()

    linePlot_death_daily = covid_data_for_line['death_daily'].values.tolist()
    linePlot_death_new_movingAvg_7D = covid_data_for_line['death_new_movingAvg_7D'].values.tolist()

    linePlot_recovered_daily = covid_data_for_line['recovered_daily'].values.tolist()
    linePlot_recoverd_new_movingAvg_7D = covid_data_for_line['recoverd_new_movingAvg_7D'].values.tolist()

    linePlot_active_daily = covid_data_for_line['active_daily'].values.tolist()
    linePlot_active_new_movingAvg_7D = covid_data_for_line['active_new_movingAvg_7D'].values.tolist()
    
    linePlot_date = covid_data_for_line['date'].values.tolist()
    
    
    rename_country = {"US":"United States","Korea, South":"South Korea","Taiwan*":"Taiwan"}
    for c in rename_country:
        selectedCountry = selectedCountry.replace(c,str(rename_country[c]))
    
    
    
    
    
    
    now3 = datetime.now()
    print(now3)
    
    context = {'mylist': mylist, 'selectedCountry': selectedCountry, 'infectionRisk': infectionRisk, 'fatalityRate': fatalityRate, 'recoveryProporation': recoveryProporation, 'testPercentage':testPercentage , 'vaccinatedProporation':vaccinatedProporation, 'activePercentage' :activePercentage, 'new': new, 'active': active, 'critical': critical, 'recovered': recovered, 'recoveredtoday': recoveredtoday, 'total': total, 'deaths': deaths , 'deathstoday' : deathstoday , 'population': population , 'tests': tests, 'totalCount' : totalCount, 'barPlotTotals': barPlotTotals, 'barPlotNames' : barPlotNames , 'peopleFully_vaccinations' : peopleFully_vaccinations, 'People_vaccinations':People_vaccinations, 'total_vaccinations': total_vaccinations, 'vaccine_Updated_Date': vaccine_Updated_Date, 'linePlot_date': linePlot_date,'linePlot_confirmed_daily':linePlot_confirmed_daily, 'linePlot_cases_new_movingAvg_7D':linePlot_cases_new_movingAvg_7D, 'linePlot_death_daily':linePlot_death_daily, 'linePlot_death_new_movingAvg_7D':linePlot_death_new_movingAvg_7D, 'linePlot_recovered_daily':linePlot_recovered_daily, 'linePlot_recoverd_new_movingAvg_7D':linePlot_recoverd_new_movingAvg_7D,'linePlot_active_daily':linePlot_active_daily, 'linePlot_active_new_movingAvg_7D': linePlot_active_new_movingAvg_7D}
    return render(request, "covid_index.html", context)
    

    
