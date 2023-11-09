
# Table of Contents

1.  [Context](#orgd8f3bd7)
2.  [Objectives](#org49167bc)
3.  [Tutorials](#org598bc62)
    1.  [Indicators](#org70bf577)
    2.  [Decision models](#org1d30ffa)
    3.  [Building bots](#org3bb639e)
    4.  [Data backends](#org624b71c)
4.  [Research Axes](#org0ad9512)
    1.  [Formalization and Probabilistic Modeling](#org965b9b2)
5.  [Technical Analysis](#org19ff75f)
6.  [References](#org1689e20)



<a id="orgd8f3bd7"></a>

# Context

A cryptocurrency is a virtual currency that operates independently of banks and governments. The
unique feature of cryptocurrency markets is their decentralization. This means that these currencies
are not issued by a central authority (such as a state) but through algorithms executed on a
computer network that ensures their coherence and transaction security. These markets evolve based
on supply and demand, but being decentralized markets, they are often better protected from economic
and political changes that generally impact traditional currencies <stachtchenko_manuel_2022>. 

Although the economic potential of these new currencies remains to be evaluated, they already offer
certain developing countries a more reliable financing alternative than a traditional currency
managed by failing banking infrastructures or state institutions. However, due to their youth, the
behavior of cryptocurrency markets can sometimes be very volatile. Therefore, managing the risks of
these new financial assets appears to be a strong socio-economic challenge for the coming years. 

Since 2014, EdgeMind has been developing methods and tools for evaluating and forecasting industrial
risks. To do this, EdgeMind implements various machine learning and simulation techniques to model
the dynamic behavior of complex systems and anticipate the occurrence of undesirable situations
based on the evolution of operational contexts. 

Today, EdgeMind is seeking to diversify its activity by entering the field of financial risks,
initially focusing on issues related to cryptocurrency analysis and algorithmic asset
management. Indeed, whether it is in industry or finance, the challenges surrounding asset
management are similar, namely predicting the future evolution of the considered asset system and
determining a set of actions to optimize its performance over time. For example, predictive
maintenance is a way to leverage operational data to optimize the availability of an industrial
asset system. In finance, trading algorithms do the same to optimize a portfolio of assets
<park_practical_2021>. Therefore, in this project, we aim to experiment with a portion of the
predictive analysis methods developed for industrial risk management in the field of financial
risks. 

Furthermore, unlike the industrial sector, data on major financial assets is available at high
sampling rates (on the order of seconds). This specificity is particularly interesting for the
development of near-real-time self-learning decision support algorithms but at the same time raises
numerous scientific and technical challenges.


<a id="org49167bc"></a>

# Objectives

The general objective of this project is the development of an autonomous AI capable of:

1.  evaluating risks related to the management of crypto-assets (e.g. cryptocurrencies), i.e. predicting the future performance of assets over a given time horizon;
2.  making decisions to optimize the performance of a portfolio of crypto-assets;
3.  self-adapting in "real-time" based on the evolution of the current economic and societal context.

All these developments are capitalized in the MOSAIC library, which we freely distribute as open
source.


<a id="org598bc62"></a>

# Tutorials

Cette section présente une liste de tutoriels permettant de prendre en main les principales
fonctionnalités de la librairie MOSAIC. 

This section presents a list of tutorials to help you get started with the main functionalities of the MOSAIC library.


<a id="org70bf577"></a>

## Indicators

For your convenience, we provide a refresher on certain fundamental concepts in finance,
particularly regarding return calculations, which you can find at [this page](./doc/basic_notions.md).

-   [*Support Range Index*](examples/indicators/sri.md) (to be updated)


<a id="org1d30ffa"></a>

## Decision models

-   [A gentle introduction to \`DM2ML\` decision models](examples/dm/dm2ml_tuto_01.md)


<a id="org3bb639e"></a>

## Building bots

-   [Building a bot : from indicators to decision model](examples/bot/step_by_step/tuto.md)
-   [Bot, backtest and MongoDB](examples/bot/bot_bt_db_mongo/tuto.md)
-   [Performing a parametric study of trading strategies](examples/bot/params_study/tuto.md)
-   [Backtesting a stratagy based on RSI indicator](examples/bot/bot_ta_dm/tuto.md)


<a id="org624b71c"></a>

## Data backends

-   [Using MongoDB with MOSAIC DB classes](examples/db/mongo/tuto.md)


<a id="org0ad9512"></a>

# Research Axes

The research axes of the MOSAIC project are succinctly presented in the following paragraphs.


<a id="org965b9b2"></a>

## Formalization and Probabilistic Modeling

Whether it is predicting the evolution of traditional assets <shen_stochastic_2020> <snow_machine_2020>, or cryptocurrencies
<bouri_trading_2019> <crone_exploration_2021> <hansen_periodicity_2021>, scientists working on the development of probabilistic models primarily focus on parametric approaches. This is mainly due to the simplicity and relative interpretability of these models. However, parametric approaches struggle to accurately represent the extreme behaviors of volatile assets. Recent articles have shown the interest of non-parametric methods in predicting the evolution of Bitcoin <balcilar_can_2017>
<jimenez_semi-nonparametric_2022>. These more complex models appear to be incompatible with considering exogenous variables that explain the behavior of the considered assets.

Our objective is to overcome this limitation by proposing a discrete non-parametric approach (the
distribution of asset returns is discretized). To our knowledge, this approach has not been tested
in the context of crypto-assets and has the advantage of being compatible with relevant
probabilistic modeling techniques (e.g. Bayesian techniques) to address the problem. 


<a id="org19ff75f"></a>

# Technical Analysis

In the field of financial market analysis, technical analysis refers to a set of tools aimed at
predicting the future returns of financial assets by studying the historical market data available,
primarily the price and volume of the considered assets <yamamoto_intraday_2012>. In the
literature review article on technical analysis <farias_nazario_literature_2017>, the authors
list the main analysis methodologies implemented over the past fifty years.  

The majority of the presented methodologies rely on the construction of specific indicators deemed
relevant by their authors (e.g. <hassanniakalager_trading_2021>,
<bao_intelligent_2008>). However, the evaluation of these indicators is only based on empirical
backtesting on arbitrarily chosen and relatively short periods, especially in the case of intraday
analysis. 

Like the authors of the article <farias_nazario_literature_2017>, we agree that assessing the
performance of technical analysis requires mathematical consolidation. 

Contributions:

-   Development of an innovative [strategy for evaluating technical indicators](indicator_analysis.md) based on the analysis of
    the conditional distribution of returns relative to observed indicators.


<a id="org1689e20"></a>

# References

<MOSAIC.bib>

