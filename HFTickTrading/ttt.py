import pandas as pd

import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    df = pd.read_csv('cu1805_20180411_all.csv')

    #quotation_df = df[6652:7099]
    quotation_df = df.where((df['updateTime']> '11:00:00') & (df['updateTime']< '11:25:00')).dropna(axis = 0, how ='any')


    #print(quotation_df.mean(axis=0, skipna=False))

    #print(quotation_df.std(axis=0, skipna=False))

    #print(quotation_df.quantile(0.99))

    #print(quotation_df.groupby(['buy_minus_sell_volume']).size())

    #DataFrame.rolling(window=120, center=False).sum()
    #df1 = pd.rolling_sum(quotation_df[['buy_minus_sell_volume']],window = 120)
    df1 = quotation_df[['buy_minus_sell_volume']].rolling(window=120, center=False).sum()
    df2 = quotation_df[['tick_volume']].rolling(window=120, center=False).sum()
    df3 =df1['buy_minus_sell_volume'] /df2['tick_volume']
    #作图
    fig, axes = plt.subplots(6, 1)
    l = quotation_df['lastPrice']
    v = quotation_df['tick_volume']
    s_v = quotation_df['sell_tick_volume']
    b_v = quotation_df['buy_tick_volume']
    op = df2['tick_volume']#s_v-b_v
    op1 = df3#s_v-b_v
    l.plot(ax=axes[0])
    v.plot(ax=axes[1],kind='bar')
    s_v.plot(ax=axes[2],kind='bar')
    b_v.plot(ax=axes[3],kind='bar')
    op.plot(ax=axes[4],kind='bar')
    op1.plot(ax=axes[5], kind='bar')

    plt.show()
