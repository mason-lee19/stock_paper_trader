import argparse
import pandas as pd

from utils import DataHandler, ApplyIndicators

def prepare_data(dataMgr) -> pd.DataFrame:
    # Query data
    df = dataMgr.query_crypto_data()
    df = dataMgr.drop_cols(df)

    # Apply techincal analysis
    indMgr = ApplyIndicators()
    df = indMgr.apply_ta(df)

    # Normalize 
    cols_to_exclude = ['symbol','timestamp']
    excluded_columns_df = df[cols_to_exclude]

    cols_to_normalize = df.drop(cols_to_exclude,axis=1).columns
    
    normalized_data = df[cols_to_normalize].apply(dataMgr.normalize)

    df_normalize = pd.concat([excluded_columns_df,normalized_data],axis=1)

    df_normalize.dropna(inplace=True)

    return df_normalize

def main(args):
    # Get api key and secret
    dataMgr = DataHandler(requestConfig=args)

    # Pull and prepare data to be analyzed by model
    df = prepare_data(dataMgr)

    print(df.iloc[:10])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-s","--stockTicker",type=str,default=None,help="stock ticker")
    parser.add_argument("-d","--startDate",type=str,default="2020-01-01",help="start date")

    args = parser.parse_args()

    main(args)