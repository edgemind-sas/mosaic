
# Table des matières

1.  [Introduction](#introduction)
2.  [Technical prerequisites](#init-env)
3.  [Creating a Bot](#org39258c6)
    1.  [Bot Specification](#orgd6f3d14)
        1.  [YAML Configuration](#orgb76173b)
        2.  [Bot Configuration Elements](#org68d2e5e)
    2.  [Executing the bot in backtest mode](#orgc8cd3c4)
4.  [Using MongoDB to monitor the bot](#org11ac31f)
    1.  [Install MongoDB with Docker-compose](#org4b2ae57)
    2.  [Storing bot data to the MongoDB database](#org44d66c7)



<a id="introduction"></a>

# Introduction

This tutorial presents the creation of a trading bot using the MOSAIC library.
As a reminder, the MOSAIC library is available on
[GitHub](https://github.com/edgemind-sas/mosaic.git) and provides functionalities for developing
trading strategies based on various technical indicators. 

This tutorial covers the following points:

-   Creating a bot from a YAML specification file.
-   Running a backtest.
-   Managing backtest data from a Mongo database.


<a id="init-env"></a>

# Technical prerequisites

The MOSAIC library requires Python version >= 3.10.

To facilitate your development projects, it is recommended to use a Python virtual environment to
perform this tutorial. So start by installing the `pew` manager if you haven't already done so: 

    pip install pew

Then create a new virtual environment:

    pew new mosaic_step_by_step

Now create a directory that will contain the files of this tutorial, e.g. `bot_bt_db`, and
navigate to this directory: 

    mkdir bot_bt_db
    cd bot_bt_db

Note that you can save this directory as associated with the virtual environment you just created
with the command: 

    pew setproject

Finally, install the MOSAIC library in your environment from GitHub:

    pip install https://github.com/edgemind-sas/mosaic.git          

If the installation was successful, you should be able to import the MOSAIC library in a Python
session and display its version: 

    import mosaic
    
    print(mosaic.__version__)

    0.0.40


<a id="org39258c6"></a>

# Creating a Bot


<a id="orgd6f3d14"></a>

## Bot Specification


<a id="orgb76173b"></a>

### YAML Configuration

To define a bot, the easiest way is to create a configuration file that specifies the
characteristics of the bot. 

To do this, create a YAML file named `bot.yaml` with the following elements:

    # Indicator definitions
    indics:
      rsi_short: &rsi_short
        cls: RSI
        length: 15
    
      mfi_short: &mfi_short
        cls: MFI
        length: 60
    
      mfi_long: &mfi_long
        cls: MFI
        length: 120
    
    # Definition of return prediction model.
    # Here we define a Logit up/down prediction model.
    predict_models:
      logit: &pm_logit
        cls: PMLogit
        returns_horizon: 60
        features:
          - *mfi_short
          - *mfi_long
    
    # Bot specification
    bot:
      name: "bot_dummy"
      mode: "btfast"
      bt_buy_on: high
      bt_sell_on: low
      
      ds_trading: &ds_trading
        symbol: "BTC/FDUSD"
        timeframe: "1s"
        dt_start: "2023-09-15 00:00:00"
        dt_end: "2023-09-16 00:00:00"
    
      ds_fit:
        <<: *ds_trading
        dt_start: "2023-09-12 00:00:00"
        dt_end: "2023-09-15 00:00:00"
    
      portfolio: 
        quote_amount_init: 1
        
      decision_model:
        cls: DM2ML
        buy_threshold: 0
        sell_threshold: 0
        pm_buy:
          <<: *pm_logit
          direction: up
    
        pm_sell:
          <<: *pm_logit
          direction: down
    
      order_model:
        cls: OrderMarket
        
      invest_model:
        cls: InvestLongModel
        nb_buy_allowed: 1
        buy_quote_rate: 1
        sell_base_rate: 1
            
      exchange :
        cls: ExchangeCCXT
        name: binance
        fees_rates:
          taker: 0
          maker: 0


<a id="org68d2e5e"></a>

### Bot Configuration Elements

**Definition of Indicators**

-   `indics`: This block defines multiple technical indicators used by the decision model.
    -   `rsi_short`: Defines an RSI indicator with a window of 15 time units.
    -   `mfi_short`: Defines an MFI indicator with a window of 60 time units.
    -   `mfi_long`: Defines another MFI indicator with a window of 120 time units.

**Prediction Models**

-   `predict_models`: Block describing the return prediction models.
    -   `logit`: Uses a Logit model for predicting future returns' increase/decrease.
        Uses `mfi_short` and `mfi_long` as explanatory variables.

**Bot Specification**

-   `bot`: This block specifies the trading bot configuration details.
    
    -   `name`: Bot name, in this case, "logit".
    -   `mode`: Operating mode, "btfast" for quick backtesting.
    -   `bt_buy_on` and `bt_sell_on`: Assumptions for buy and sell prices in backtesting.
    
    **Data Sources Configuration**
    
    -   `ds_trading`: Data source for real-time trading or backtesting.
    -   `ds_fit`: Data source for model fitting.
    
    **Models**
    
    -   `decision_model`: Specifies the decision model for buy and sell orders.
    -   `order_model`: Specifies the order model, in this case, a market order.
    -   `invest_model`: Specifies the investment model, allowing a single purchase and fixed sell/buy rates.
    
    **Exchange**
    
    -   `exchange`: Details of the exchange where OHLCV data is retrieved.
        -   `name`: The exchange's name, in this case, Binance.
        -   `fees_rates`: Used transaction fees.


<a id="orgc8cd3c4"></a>

## Executing the bot in backtest mode

Next, create the following Python file `bot.py` to backtest the bot defined in the previous YAML
file. 

    import mosaic.trading as mtr
    import yaml
    
    with open("bot.yaml", 'r', encoding="utf-8") as yaml_file:
        bot_config = yaml.load(yaml_file,
                               Loader=yaml.SafeLoader)
        bot_config["bot"].setdefault("cls", "BotTrading")
        bot = mtr.BotTrading.from_dict(bot_config["bot"])
    
    bot.start(
        data_dir=".",
        progress_mode=True,
    )
    
    print(bot.portfolio)

Launch the bot by running the `python bot.py` command. At the end of the execution, you should
observe the state of the bot's portfolio at the end of the backtest. In this case, we're not
profitable&#x2026;


<a id="org11ac31f"></a>

# Using MongoDB to monitor the bot


<a id="org4b2ae57"></a>

## Install MongoDB with Docker-compose

Before you begin, make sure you have a functional Docker installation with the ability to launch a
container without `sudo`. Also, make sure you have Docker-compose installed. 

Create the `docker-compose.yml` file with the following content:

    version: '3.1'
    
    services:
      db:
        image: mongo
        container_name: mongo_mosaic_trading
        ports:
          - 27017:27017
        networks: 
          - mongo-compose-network
        environment:
          MONGO_INITDB_ROOT_USERNAME: root
          MONGO_INITDB_ROOT_PASSWORD: example
    
    networks:
      mongo-compose-network:
        driver: bridge

Launch MongoDB with Docker-compose as follows:

    docker-compose up -d


<a id="org44d66c7"></a>

## Storing bot data to the MongoDB database

If you have set up a MongoDB database on your machine using the previous Docker configuration, you
can instruct the bot to save its state and actions in the database. 

To do this, you need to modify the script for launching the previous bot as follows:

    import mosaic.trading as mtr
    import yaml
    
    with open("bot.yaml", 'r', encoding="utf-8") as yaml_file:
        bot_config = yaml.load(yaml_file,
                               Loader=yaml.SafeLoader)
        bot_config["bot"].setdefault("cls", "BotTrading")
        bot_config["bot"].setdefault(
            "db",
            {
                "cls": "DBMongo",
                "name": "mosaic_trading",
                "config": {
                    "host": "mongodb://localhost",
                    "port": "27017",
                    "username": "root",
                    "password": "example",
                },
            })
    
        bot = mtr.BotTrading.from_dict(bot_config["bot"])
    
    bot.start(
        data_dir=".",
        progress_mode=True,
    )

Now we can retrieve bot data and results from MongoDB using the `bot_data` backend attribute
`db`. For example, to get the bot status at the end of the backtest: 

    bot_data = bot.db.get(endpoint="bots", filter={"uid": bot.uid})

Note the use of the `filter` parameter in the `get` method to retrieve only the data of our current
bot from MongoDB. If `filter` is omitted, all bot statuses stored in the database will be
retrieved. 

To retrieve the bot orders made during the backtest and transform them into a DataFrame:

    import pandas as pd
    
    bot_orders_data = bot.db.get(endpoint="orders",
                                 filter={"bot_uid": bot.uid})
    bot_orders_df = pd.DataFrame(bot_orders_data)

Just like before, we use the `filter` argument to specify our bot UID to only get orders made by
this bot. 

Finally, we can get the bot portfolio over time, which is a proxy for the bot's performance during
the backtest: 

    import pandas as pd
    
    bot_portfolio_data = bot.db.get(endpoint="portfolio",
                                    filter={"bot_uid": bot.uid})
    bot_portfolio_df = pd.DataFrame(bot_portfolio_data)

