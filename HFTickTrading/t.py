import re
import pandas as pd


if __name__ == "__main__":
    df = pd.read_csv("cu1805_20180403.csv")
    pd.rolling_mean()
    df.describe(percentiles=0.1)