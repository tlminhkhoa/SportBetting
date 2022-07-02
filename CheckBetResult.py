import sqlite3
import pandas as pd 
import time
import datetime
conn = sqlite3.connect('./DailyData/SoccerData.db')
c = conn.cursor()

def getUnknowBetResult(c):
    c.execute("""SELECT PlaceBetTable.fixtureId , PlaceBetTable.currentDate , PlaceBetTable.betOdd, PlaceBetTable.betDatePortion, Result.FTR, modelData.modelBet
    FROM PlaceBetTable
    join Result on PlaceBetTable.fixtureId = Result.fixtureId 
    join modelData on PlaceBetTable.fixtureId = modelData.fixtureId 
    where PlaceBetTable.betToResult is null and  Result.FTR is not null;""")
    listData = c.fetchall()
    fixtureIdList = []
    currentDateList = []
    betOddList = []
    BetdatePorprotionList = []
    FTRList = []
    modelBetList = []
    for tup in listData:
        fixtureIdList.append(tup[0])
        currentDateList.append(tup[1])
        betOddList.append(tup[2])
        BetdatePorprotionList.append(tup[3])
        FTRList.append(tup[4])
        modelBetList.append(tup[5])
    
    df = pd.DataFrame(columns=["fixtureId","currentDate","odd","betDatePortion"])
    df["fixtureId"] = fixtureIdList
    df["currentDate"] = currentDateList
    df["odd"] = betOddList
    df["betDatePortion"] = BetdatePorprotionList
    df["FTR"] = FTRList
    df["modelBet"] = modelBetList
    df["betToResult"] = df["FTR"] == df["modelBet"]
    return df

def calGainAndBetAmount(c,df):
    softmaxList =[]
    for date in df["currentDate"].unique():
        # print(date)

        # get previous date data
        date_format = datetime.datetime.strptime(date,
                                            "%Y-%m-%d %H:%M:%S")
        date_sample  = time.mktime(date_format.timetuple())
        # print(date_sample)
        c.execute("""SELECT *, max(currentDate_timestamp) from BudgetTrack """)
        listData = c.fetchall()
        
        print(date_sample)
        runningMoney = listData[0][2]
        refillAmount = listData[0][3]
        withdrawAmount = listData[0][4]
        TotalBudget = listData[0][5]
        

        data = df[df["currentDate"] == date]
        
        
        gain = []
        for rowtuple in data.iterrows():
            row = rowtuple[1]
            if row["betToResult"] == True:
                gainTemp = row["betDatePortion"] * runningMoney * (row["odd"] -1) * row["betDatePortion"]
            else:
                gainTemp = -row["betDatePortion"]*runningMoney

            gain.append(gainTemp)
            
            c.execute(""" 
            UPDATE PlaceBetTable
                            SET  betToResult = ?, BetAmount = ? ,Gain = ?  
                            WHERE fixtureId = ?;
                            """,(row["betToResult"], row["betDatePortion"] * runningMoney ,gainTemp,row["fixtureId"]))
            

        runningMoney = runningMoney + sum(gain)
        if runningMoney < 1:
            refillAmount = refillAmount + 10 
        if runningMoney > 1000:
            withdrawAmount = withdrawAmount + 1000

        TotalBudget = runningMoney - refillAmount + withdrawAmount

    
        c.execute(""" 
                INSERT INTO BudgetTrack VALUES(?,?,?,?,?,?)
                """,(date,date_sample,runningMoney,refillAmount,withdrawAmount,TotalBudget))
        conn.commit()
        

        



df = getUnknowBetResult(c)
calGainAndBetAmount(c,df)
# conn.commit()
c.close()
conn.close()