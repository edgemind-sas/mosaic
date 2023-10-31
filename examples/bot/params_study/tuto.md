
# Table des matières

1.  [Introduction](#introduction)
2.  [Technical prerequisites](#init-env)
3.  [Creating the base strategy](#org3f472de)
4.  [Parameters study](#org0d44027)
    1.  [Set up](#org1a99d08)
    2.  [Back testing](#org842e874)
    3.  [Results analysis](#orgcb1ab17)



<a id="introduction"></a>

# Introduction

Implementing an investment strategy involves a lot of parameters in general. Finding the set of
parameters that maximizes the strategy's performance is a very difficult open problem in finance. A
basic approach involves backtesting the strategy by varying the parameters. 

This tutorial presents how to use MOSAIC to perform simple bot parameter studies.


<a id="init-env"></a>

# Technical prerequisites

The MOSAIC library requires Python version >= 3.10.

To facilitate your development projects, it is recommended to use a Python virtual environment to
perform this tutorial. So start by installing the `pew` manager if you haven't already done so: 

    pip install pew

Then create a new virtual environment:

    pew new mosaic_param_study

Now create a directory that will contain the files of this tutorial, e.g. `param_study`, and
navigate to this directory: 

    mkdir param_study
    cd param_study

Note that you can save this directory as associated with the virtual environment you just created
with the command: 

    pew setproject

Finally, install the MOSAIC library in your environment from GitHub:

    pip install https://github.com/edgemind-sas/mosaic.git          

If the installation was successful, you should be able to import the MOSAIC library in a Python
session and display its version: 

    import mosaic
    
    print(mosaic.__version__)

    0.0.41

Now let's install a MongoDB instance to monitor our automatic investment strategies.

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


<a id="org3f472de"></a>

# Creating the base strategy

In this tutorial, we will use a strategy that relies on:

-   The [SRI](../../indicators/sri.md) technical indicator which has only one parameter, i.e. the past processing window length.
-   a decision model based on logistic regression with multiple hyperparameters.

The following file `bot.yaml` provides the YAML configuration of the bot that represents our
strategy with some default parameters: 

    # Indicator definitions
    indics:
      sri_short: &sri_indic
        cls: SRI
        length: 30
    
    # Definition of return prediction model.
    # Here we define a Logit up/down prediction model.
    predict_models:
      logit: &pm_logit
        cls: PMLogit
        returns_horizon: 15
        features:
          - *sri_indic
    
    # Bot specification
    bot:
      name: "bot_dummy"
      mode: "btfast"
      bt_buy_on: high
      bt_sell_on: low
      
      ds_trading: &ds_trading
        symbol: "BTC/TUSD"
        timeframe: "1m"
        dt_start: "2023-10-01 00:00:00"
        dt_end: "2023-10-20 00:00:00"
    
      ds_fit:
        <<: *ds_trading
        dt_start: "2023-08-01 00:00:00"
        dt_end: "2023-10-01 00:00:00"
    
      portfolio: 
        quote_amount_init: 1
        
      decision_model:
        cls: DM2ML
        buy_threshold: 0.1
        sell_threshold: 0.1
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
    
      db:
        cls: DBMongo
        name: "mosaic_trading"
        config:
          host: "mongodb://localhost"
          port: "27017"
          username: "root"
          password: "example"

The hyperparameters of this strategy are:

-   The SRI indicator window length (set to 30)
-   The future returns prediction window length (set to 15)
-   The buy threshold related to the upward movement prediction model (set to 0.1)
-   The sell threshold related to the downward movement prediction model (set to 0.1)

We can evaluate this strategy with the proposed default hyperparameters using the following Python
file `bot.py`: 

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


<a id="org0d44027"></a>

# Parameters study


<a id="org1a99d08"></a>

## Set up

To perform a parameter study, we first define a dictionary called `params_dict` that specifies
different values for the hyperparameters of our trading strategy. Each key in the dictionary
represents a specific hyperparameter of the decision model. The values associated with each key are
a list of possible values for that hyperparameter:

    params_dict = {
        "decision_model.pm_*.features[0].length": list(range(40, 60)),
        "decision_model.pm_*.returns_horizon": list(range(40, 60)),
        }

Here's a breakdown of the keys and their corresponding hyperparameters:

-   `"decision_model.pm_*.features[0].length"`: This key specifies the length parameter of the first
    feature (i.e. the SRI indicator as we define only one feature here) in the upward and downward
    prediction models.
-   `"decision_model.pm_*.returns_horizon"`: This key specifies the future returns prediction horizon
    parameter in the upward and downward prediction models.


<a id="org842e874"></a>

## Back testing

These parameter combinations will be used to backtest the trading strategy with different settings
for these hyperparameters. Please note that it may take approximately 1 hour to complete.

    import mosaic.utils as mut
    import tqdm
    import ipdb
    
    # Compute the list of all parameters combination to backtest
    params_list = mut.compute_combinations(**params_dict)
    
    params_analysis = []
    for it, params in enumerate(tqdm.tqdm(params_list)):
        # Set current parameter combination to our bot
        mut.set_obj_attrs(bot, params)
    
        bot.uid = f"{it:06}"
    
        bot.start(
            data_dir=".",
            progress_mode=True,
        )
    
        # Save backtest performance of the current parameters combination
        params_analysis.append(dict(params, **bot.portfolio.dict()))
    
        # Reset the bot for the next parameters combination
        bot.reset()

The parameters study follows the following steps:

-   Compute the list of all parameter combinations to be tested using the
    `mut.compute_combinations` function, which takes the `params_dict` dictionary as input.
-   Initialize an empty list called `params_analysis` to store the results of each parameter
    combination.
-   Start a loop that iterates over each parameter combination. For each iteration:
    -   Set the current parameter combination to the bot by using the `mut.set_obj_attr` function to
        update the relevant attributes of the `bot` object.
    -   Assign a unique identifier (`uid`) to the bot based on the iteration number.
    -   Start the bot using the `bot.start` method, specifying the data directory, progress mode, and other relevant parameters.
    -   Save the backtest performance of the current parameter combination by appending a dictionary that contains the parameters and the portfolio status of the bot to the `params_analysis` list.
    -   Reset the bot for the next parameter combination using the `bot.reset` method.

After the loop completes, the `params_analysis` list will contain the backtest performance for each
parameter combination. Each dictionary in the list will have the parameters that were tested and the
corresponding portfolio status of the bot. 

Finally, we convert the results of the parameter study into a DataFrame so that we can easily sort
them based on performance. 

    import pandas as pd
    
    params_analysis_df = pd.DataFrame(params_analysis).sort_values(by="performance")
    
    # Save results to disk
    params_analysis_df.to_csv("params_analysis.csv", index=False)


<a id="orgcb1ab17"></a>

## Results analysis

This section presents a few examples of analysis that can be performed on the results of the
parameter study.

    import plotly.express as px
    fig = px.box(params_analysis_df,
                 x="decision_model.pm_*.features[0].length",
                 y="performance",
                 title="Performance distribution vs SRI length",
                 labels={
                     "decision_model.pm_*.features[0].length": "SRI length",
                     "decision_model.pm_*.returns_horizon": "Returns horizon",
                 })

<div>                        <script type="text/javascript">window.PlotlyConfig = {MathJaxConfig: 'local'};</script>
        <script src="https://cdn.plot.ly/plotly-2.18.0.min.js"></script>                <div id="706acde9-131c-43a5-9d8a-28294b8622c9" class="plotly-graph-div" style="height:100%; width:100%;"></div>            <script type="text/javascript">                                    window.PLOTLYENV=window.PLOTLYENV || {};                                    if (document.getElementById("706acde9-131c-43a5-9d8a-28294b8622c9")) {                    Plotly.newPlot(                        "706acde9-131c-43a5-9d8a-28294b8622c9",                        [{"alignmentgroup":"True","hovertemplate":"SRI length=%{x}<br>performance=%{y}<extra></extra>","legendgroup":"","marker":{"color":"#636efa"},"name":"","notched":false,"offsetgroup":"","orientation":"v","showlegend":false,"x":[30,30,25,35,35,35,30,30,40,40,35,40,45,40,45,45,45,50,40,50,50,50,55,50,55,55,55,50,45,55,60,60,60,45,55,60,60,60,65,65,65,65,65,70,55,50,70,70,70,45,65,70,75,75,75,70,75,80,80,75,80,25,85,55,80,80,85,75,80,85,85,90,95,85,85,60,90,50,90,90,95,100,90,95,90,65,95,100,95,95,100,100,100,105,105,105,105,100,60,105,110,110,105,110,110,100,110,115,110,105,105,115,115,110,20,115,115,110,115,120,120,120,115,100,110,120,120,120,35,115,115,70,120,40,120,45,95,120,110,120,115,40,120,115,120,120,105,110,105,105,95,110,110,115,115,115,120,120,30,110,120,35,105,90,35,35,100,20,100,100,100,85,40,80,110,115,110,115,115,120,90,95,105,115,105,30,90,120,110,110,95,100,120,110,120,115,105,95,90,105,100,30,95,95,30,85,90,75,80,25,110,80,115,90,90,80,85,95,85,120,110,45,100,85,105,105,40,105,45,90,90,90,50,50,50,50,50,50,45,45,45,45,90,45,45,45,45,45,45,45,100,100,100,100,100,50,55,20,55,55,55,55,55,55,55,50,50,50,100,50,50,95,95,95,95,95,95,90,90,90,90,30,35,30,30,30,30,30,30,30,30,30,30,30,35,20,20,20,20,20,20,20,25,20,20,20,20,35,95,40,40,40,40,40,40,40,40,40,40,40,55,35,35,35,35,35,35,105,105,35,35,35,35,65,70,70,70,70,70,70,70,70,70,70,70,70,70,70,65,65,65,65,80,80,80,80,80,80,80,55,25,25,25,25,25,25,25,25,30,25,25,25,25,75,25,25,25,25,25,20,20,20,20,20,20,20,85,75,60,60,60,60,60,60,60,60,60,85,85,85,60,85,85,85,85,85,85,80,80,80,80,55,55,75,75,75,75,75,75,75,75,75,75,75,60,75,65,65,65,65,65,65,65,65,65,60,60,50,55,40,115],"x0":" ","xaxis":"x","y":[0.4529292661910968,0.4726868094339425,0.4846520997408976,0.5002609469433771,0.510382069390647,0.5306116681420256,0.5392440362338975,0.5431256479274339,0.5480935783497141,0.5556740222806518,0.5627605571491633,0.5697755012805269,0.5918514714338062,0.6027292012216573,0.604347393515573,0.6047762086898439,0.6232928876204197,0.6276533102017435,0.6282897950511949,0.6323095040369034,0.6375981579760355,0.6430778135246084,0.6442048855526755,0.6464791138907955,0.6466798660666676,0.6563308875908588,0.6567470823632651,0.6579920145013778,0.6594942467102669,0.6626724399342662,0.6710134230637029,0.6715739943800272,0.6735607041030017,0.6737402791087789,0.6748200532782676,0.6751821168295131,0.6787727397152276,0.6910210479608736,0.6921051189100289,0.6923777771082948,0.6976029664232374,0.6998822429583232,0.7021235900574124,0.7025727219036038,0.7052650334849307,0.7059452573772452,0.7074498473160773,0.7082179398684013,0.7121924075246973,0.7136645696075686,0.7181826530921563,0.720721286031052,0.7227180231423199,0.7242334951595975,0.7259321739190495,0.7298474826952746,0.732888322066638,0.7341202214511525,0.7345851011913451,0.7394533316105886,0.7400911736440475,0.7414880672011672,0.7435743878720106,0.7440658035028468,0.7452502318171633,0.7462687260656028,0.7471640188282476,0.7473104912197722,0.7490364436446506,0.7508311685156605,0.7546149298532498,0.7552956496948708,0.7566795464348084,0.7577334688577555,0.7585983927928815,0.7588596357165092,0.7606024623259438,0.7617818936185354,0.7634786401937678,0.7635765167139404,0.7643792645880145,0.7652872436731925,0.7656438030081434,0.7665208497365185,0.7670627638962048,0.7672494157843776,0.7706283450861326,0.7709873668941349,0.771583830379649,0.7722907620391731,0.7732079531624672,0.7734233729565158,0.7740055569781525,0.7757316070205348,0.776452347018085,0.7781981142591746,0.7793142304561143,0.779331475292256,0.7797611263136194,0.7820022384088618,0.7840644072660955,0.7840824457481854,0.7847270811512487,0.7865391851882552,0.7877311618768548,0.7881637718716127,0.7910526411192704,0.7911748239388057,0.7918165837244361,0.7939387676949603,0.794249689753323,0.7949617308723875,0.7977921462493932,0.7982172707121595,0.7989483260432513,0.7998660056993323,0.8001774025794294,0.8021845595256477,0.8025772815981216,0.8031173968402625,0.8045711840764284,0.8050985178671494,0.8095130647739852,0.8096003621315039,0.8098281401722791,0.8099628569472328,0.8102645418370176,0.8104634515083462,0.8158242239787428,0.8170121897328191,0.817348309551054,0.8175044552573166,0.8182120612015785,0.8195849589634193,0.8207920712317842,0.8224107519270497,0.822710979011472,0.8252040299609376,0.8300925458623942,0.830397164808825,0.833312337836513,0.8344051497035536,0.8448270468173766,0.8474554672170668,0.8516894910457306,0.8616812969320077,0.8649319909858332,0.8703102905534635,0.8708686764573346,0.8718007225217119,0.8733077273683415,0.877747929471715,0.8810377544720505,0.8853402016052024,0.8877897489818256,0.889468782258151,0.8954287068289566,0.9050383855159144,0.9102338837033545,0.9126017777927626,0.9133116412725674,0.9163705084353544,0.9197230998226112,0.9213623138281736,0.923024619762793,0.9240436486667876,0.9287836916813624,0.9302863826802804,0.9317826878154132,0.932281271320786,0.9329557008113172,0.9353539306795878,0.9382380775766485,0.9455360760508642,0.945885539713721,0.9462514337092154,0.9462523544465892,0.9473311588711556,0.9489942325474404,0.952175919210487,0.9534759641806556,0.954839897614202,0.9589783512017248,0.960778535181302,0.9616697539828472,0.969608079902619,0.971431509620381,0.9745064467763168,0.9755200085481024,0.9762888999637528,0.9806496576994856,0.9841692183382388,0.9845748857561548,0.9848432570226372,0.9863541880177892,0.986719044389605,0.987132253019147,0.987976050432009,0.990854695645292,0.9916760839236948,0.9929446178106142,0.9941512557334008,0.9944770706883276,0.9949693149690546,0.9952997117768052,0.9955276717540296,0.9961146192726852,0.9961348969850726,0.996450626360646,0.9967505139958917,0.9969011129316556,0.9970339356630512,0.9971479580195992,0.997226343875773,0.997226343875773,0.997302358336165,0.9973589783940754,0.9974707955717156,0.9976004950171864,0.9979453843156508,0.9981401727871876,0.9983434629854068,0.9984116483940892,0.99872836642484,0.9988799455096148,0.9989350713100972,0.999127120806593,0.9992604902232524,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0002215458057695,1.000391440854799,1.0005920806844324,1.0012985431459245],"y0":" ","yaxis":"y","type":"box"}],                        {"template":{"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmapgl":[{"type":"heatmapgl","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"type":"scattergl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]},"layout":{"autotypenumbers":"strict","colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"white","plot_bgcolor":"#E5ECF6","polar":{"bgcolor":"#E5ECF6","angularaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"radialaxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"ternary":{"bgcolor":"#E5ECF6","aaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"baxis":{"gridcolor":"white","linecolor":"white","ticks":""},"caxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]]},"xaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"yaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"zaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"white","landcolor":"#E5ECF6","subunitcolor":"white","showland":true,"showlakes":true,"lakecolor":"white"},"title":{"x":0.05},"mapbox":{"style":"light"}}},"xaxis":{"anchor":"y","domain":[0.0,1.0],"title":{"text":"SRI length"}},"yaxis":{"anchor":"x","domain":[0.0,1.0],"title":{"text":"performance"}},"legend":{"tracegroupgap":0},"title":{"text":"Performance distribution vs SRI length"},"boxmode":"group"},                        {"displayModeBar": false, "responsive": true}                    )                };                            </script>        </div>

    import plotly.express as px
    fig = px.box(params_analysis_df,
                 x="decision_model.pm_*.returns_horizon",
                 y="performance",
                 title="Performance distribution vs Returns horizon",
                 labels={
                     "decision_model.pm_*.features[0].length": "SRI length",
                     "decision_model.pm_*.returns_horizon": "Returns horizon",
                 })

<div>                        <script type="text/javascript">window.PlotlyConfig = {MathJaxConfig: 'local'};</script>
        <script src="https://cdn.plot.ly/plotly-2.18.0.min.js"></script>                <div id="ac8f2036-4fd5-43cb-8e79-a4b08d443b25" class="plotly-graph-div" style="height:100%; width:100%;"></div>            <script type="text/javascript">                                    window.PLOTLYENV=window.PLOTLYENV || {};                                    if (document.getElementById("ac8f2036-4fd5-43cb-8e79-a4b08d443b25")) {                    Plotly.newPlot(                        "ac8f2036-4fd5-43cb-8e79-a4b08d443b25",                        [{"alignmentgroup":"True","hovertemplate":"Returns horizon=%{x}<br>performance=%{y}<extra></extra>","legendgroup":"","marker":{"color":"#636efa"},"name":"","notched":false,"offsetgroup":"","orientation":"v","showlegend":false,"x":[25,30,25,25,30,20,20,35,25,30,35,20,25,35,20,30,35,25,40,30,20,35,25,40,30,20,35,45,40,40,30,25,35,45,45,20,40,45,25,30,35,20,40,25,50,50,30,20,35,50,45,40,25,30,20,45,35,25,30,40,20,20,25,55,35,40,30,45,45,20,35,25,25,40,45,50,30,55,20,35,20,25,40,30,45,50,35,20,40,45,45,30,40,25,20,30,45,35,55,40,25,20,35,45,30,50,40,25,35,50,55,20,30,50,25,45,40,55,35,20,25,30,50,55,60,40,45,35,40,55,60,50,50,45,55,55,50,60,120,120,120,50,115,115,105,100,120,115,100,115,55,100,105,65,100,105,65,90,40,65,110,55,105,55,45,50,120,20,115,105,100,55,55,55,95,90,90,95,110,95,50,120,60,70,90,45,105,70,110,70,60,65,85,75,75,75,70,65,60,65,60,50,115,105,55,50,70,55,60,35,85,75,85,75,65,70,65,70,60,80,80,60,70,70,75,85,60,110,95,80,85,90,65,70,75,80,85,90,120,80,85,90,120,100,105,110,115,65,70,75,85,90,95,110,75,110,70,30,80,85,90,95,100,105,65,95,100,105,80,115,120,75,80,85,90,95,100,95,100,110,115,65,85,115,120,75,80,85,90,95,100,105,110,60,80,85,80,75,70,65,60,55,70,50,45,40,35,90,110,105,110,115,120,70,75,80,85,90,95,100,75,95,100,105,110,115,120,80,95,60,65,70,75,100,120,75,80,85,90,95,100,105,110,55,60,65,70,115,105,110,115,120,65,80,85,90,95,100,50,120,95,100,105,110,115,120,60,65,70,75,80,85,90,90,30,40,45,50,55,90,95,100,105,110,115,120,90,95,105,110,115,120,60,65,70,75,80,120,80,85,100,95,100,105,110,115,75,105,110,115,120,110,115,80,100,105,110,115,120,50,60,65,70,75,95,85,60,65,70,75,80,85,90,95,55,85,90,60,60,65,80],"x0":" ","xaxis":"x","y":[0.4529292661910968,0.4726868094339425,0.4846520997408976,0.5002609469433771,0.510382069390647,0.5306116681420256,0.5392440362338975,0.5431256479274339,0.5480935783497141,0.5556740222806518,0.5627605571491633,0.5697755012805269,0.5918514714338062,0.6027292012216573,0.604347393515573,0.6047762086898439,0.6232928876204197,0.6276533102017435,0.6282897950511949,0.6323095040369034,0.6375981579760355,0.6430778135246084,0.6442048855526755,0.6464791138907955,0.6466798660666676,0.6563308875908588,0.6567470823632651,0.6579920145013778,0.6594942467102669,0.6626724399342662,0.6710134230637029,0.6715739943800272,0.6735607041030017,0.6737402791087789,0.6748200532782676,0.6751821168295131,0.6787727397152276,0.6910210479608736,0.6921051189100289,0.6923777771082948,0.6976029664232374,0.6998822429583232,0.7021235900574124,0.7025727219036038,0.7052650334849307,0.7059452573772452,0.7074498473160773,0.7082179398684013,0.7121924075246973,0.7136645696075686,0.7181826530921563,0.720721286031052,0.7227180231423199,0.7242334951595975,0.7259321739190495,0.7298474826952746,0.732888322066638,0.7341202214511525,0.7345851011913451,0.7394533316105886,0.7400911736440475,0.7414880672011672,0.7435743878720106,0.7440658035028468,0.7452502318171633,0.7462687260656028,0.7471640188282476,0.7473104912197722,0.7490364436446506,0.7508311685156605,0.7546149298532498,0.7552956496948708,0.7566795464348084,0.7577334688577555,0.7585983927928815,0.7588596357165092,0.7606024623259438,0.7617818936185354,0.7634786401937678,0.7635765167139404,0.7643792645880145,0.7652872436731925,0.7656438030081434,0.7665208497365185,0.7670627638962048,0.7672494157843776,0.7706283450861326,0.7709873668941349,0.771583830379649,0.7722907620391731,0.7732079531624672,0.7734233729565158,0.7740055569781525,0.7757316070205348,0.776452347018085,0.7781981142591746,0.7793142304561143,0.779331475292256,0.7797611263136194,0.7820022384088618,0.7840644072660955,0.7840824457481854,0.7847270811512487,0.7865391851882552,0.7877311618768548,0.7881637718716127,0.7910526411192704,0.7911748239388057,0.7918165837244361,0.7939387676949603,0.794249689753323,0.7949617308723875,0.7977921462493932,0.7982172707121595,0.7989483260432513,0.7998660056993323,0.8001774025794294,0.8021845595256477,0.8025772815981216,0.8031173968402625,0.8045711840764284,0.8050985178671494,0.8095130647739852,0.8096003621315039,0.8098281401722791,0.8099628569472328,0.8102645418370176,0.8104634515083462,0.8158242239787428,0.8170121897328191,0.817348309551054,0.8175044552573166,0.8182120612015785,0.8195849589634193,0.8207920712317842,0.8224107519270497,0.822710979011472,0.8252040299609376,0.8300925458623942,0.830397164808825,0.833312337836513,0.8344051497035536,0.8448270468173766,0.8474554672170668,0.8516894910457306,0.8616812969320077,0.8649319909858332,0.8703102905534635,0.8708686764573346,0.8718007225217119,0.8733077273683415,0.877747929471715,0.8810377544720505,0.8853402016052024,0.8877897489818256,0.889468782258151,0.8954287068289566,0.9050383855159144,0.9102338837033545,0.9126017777927626,0.9133116412725674,0.9163705084353544,0.9197230998226112,0.9213623138281736,0.923024619762793,0.9240436486667876,0.9287836916813624,0.9302863826802804,0.9317826878154132,0.932281271320786,0.9329557008113172,0.9353539306795878,0.9382380775766485,0.9455360760508642,0.945885539713721,0.9462514337092154,0.9462523544465892,0.9473311588711556,0.9489942325474404,0.952175919210487,0.9534759641806556,0.954839897614202,0.9589783512017248,0.960778535181302,0.9616697539828472,0.969608079902619,0.971431509620381,0.9745064467763168,0.9755200085481024,0.9762888999637528,0.9806496576994856,0.9841692183382388,0.9845748857561548,0.9848432570226372,0.9863541880177892,0.986719044389605,0.987132253019147,0.987976050432009,0.990854695645292,0.9916760839236948,0.9929446178106142,0.9941512557334008,0.9944770706883276,0.9949693149690546,0.9952997117768052,0.9955276717540296,0.9961146192726852,0.9961348969850726,0.996450626360646,0.9967505139958917,0.9969011129316556,0.9970339356630512,0.9971479580195992,0.997226343875773,0.997226343875773,0.997302358336165,0.9973589783940754,0.9974707955717156,0.9976004950171864,0.9979453843156508,0.9981401727871876,0.9983434629854068,0.9984116483940892,0.99872836642484,0.9988799455096148,0.9989350713100972,0.999127120806593,0.9992604902232524,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0002215458057695,1.000391440854799,1.0005920806844324,1.0012985431459245],"y0":" ","yaxis":"y","type":"box"}],                        {"template":{"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmapgl":[{"type":"heatmapgl","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"type":"scattergl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]},"layout":{"autotypenumbers":"strict","colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"white","plot_bgcolor":"#E5ECF6","polar":{"bgcolor":"#E5ECF6","angularaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"radialaxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"ternary":{"bgcolor":"#E5ECF6","aaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"baxis":{"gridcolor":"white","linecolor":"white","ticks":""},"caxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]]},"xaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"yaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"zaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"white","landcolor":"#E5ECF6","subunitcolor":"white","showland":true,"showlakes":true,"lakecolor":"white"},"title":{"x":0.05},"mapbox":{"style":"light"}}},"xaxis":{"anchor":"y","domain":[0.0,1.0],"title":{"text":"Returns horizon"}},"yaxis":{"anchor":"x","domain":[0.0,1.0],"title":{"text":"performance"}},"legend":{"tracegroupgap":0},"title":{"text":"Performance distribution vs Returns horizon"},"boxmode":"group"},                        {"displayModeBar": false, "responsive": true}                    )                };                            </script>        </div>

