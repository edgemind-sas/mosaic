import mosaic.db as mdb        

db_mongo = mdb.DBMongo(
    name="mosaic_trading",
    config={
        "host": "mongodb://localhost",
        "port": "27017",
        "username": "root",
        "password": "example",
    })

success = db_mongo.connect()
if success:
    print("Connection established")
else:
    print("Connection failed")

import pandas as pd

ohlcv_df = pd.read_csv("ohlcv.csv", index_col="datetime")

db_mongo.put(endpoint="ohlcv_test",
             data=ohlcv_df.reset_index().to_dict("records"),
             index=["datetime"])

ohlcv_list_d = db_mongo.get(endpoint="ohlcv_test",
                            filter={"volume": {"$gte": 1.0}},
                            projection=["datetime", "close", "volume"],
                            )
ohlcv_bis_df = pd.DataFrame(ohlcv_list_d)

ohlcv_all_list_d = db_mongo.get(endpoint="ohlcv_test")
ohlcv_all_bis_df = pd.DataFrame(ohlcv_all_list_d)

db_mongo.update(
    endpoint="ohlcv_test",
    index=[{"datetime": '2023-09-12 00:00:03+02:00'}, {"datetime": '2023-09-12 00:01:45+02:00'}],
    data=[{"volume": 10}, {"volume": 10}]
)
