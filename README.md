
# Table of Contents

1.  [Context](#org5463ac1)
2.  [Objectives](#orgdcdc86c)
3.  [Tutorials](#orgfb163c9)
    1.  [Indicators](#orgd59e94f)
    2.  [Building bots](#org4d34800)
    3.  [Data backends](#orga34b103)
4.  [Research Axes](#org01255f4)
    1.  [Formalization and Probabilistic Modeling](#org0a8e2ed)
5.  [Technical Analysis](#org4fcdbc9)
6.  [References](#orgb416cd4)



<a id="org5463ac1"></a>

# Context

A cryptocurrency is a virtual currency that operates independently of banks and governments. The
unique feature of cryptocurrency markets is their decentralization. This means that these currencies
are not issued by a central authority (such as a state) but through algorithms executed on a
computer network that ensures their coherence and transaction security. These markets evolve based
on supply and demand, but being decentralized markets, they are often better protected from economic
and political changes that generally impact traditional currencies [1]. 

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
[2]. Therefore, in this project, we aim to experiment with a portion of the
predictive analysis methods developed for industrial risk management in the field of financial
risks. 

Furthermore, unlike the industrial sector, data on major financial assets is available at high
sampling rates (on the order of seconds). This specificity is particularly interesting for the
development of near-real-time self-learning decision support algorithms but at the same time raises
numerous scientific and technical challenges.


<a id="orgdcdc86c"></a>

# Objectives

The general objective of this project is the development of an autonomous AI capable of:

1.  evaluating risks related to the management of crypto-assets (e.g. cryptocurrencies), i.e. predicting the future performance of assets over a given time horizon;
2.  making decisions to optimize the performance of a portfolio of crypto-assets;
3.  self-adapting in "real-time" based on the evolution of the current economic and societal context.

All these developments are capitalized in the MOSAIC library, which we freely distribute as open
source.


<a id="orgfb163c9"></a>

# Tutorials

Cette section présente une liste de tutoriels permettant de prendre en main les principales
fonctionnalités de la librairie MOSAIC. 

This section presents a list of tutorials to help you get started with the main functionalities of the MOSAIC library.


<a id="orgd59e94f"></a>

## Indicators

For your convenience, we provide a refresher on certain fundamental concepts in finance,
particularly regarding return calculations, which you can find at [this page](./doc/basic_notions.md).

-   [*Support Range Index*](examples/indicators/sri.md) (to be updated)


<a id="org4d34800"></a>

## Building bots

-   [Building a bot : from indicators to decision model](examples/bot/step_by_step/tuto.md)
-   [Bot configuration with YAML](examples/bot/bot_dummy/tuto.md) (to be updated)


<a id="orga34b103"></a>

## Data backends

-   [Using MongoDB with MOSAIC DB classes](examples/db/mongo/tuto.md)


<a id="org01255f4"></a>

# Research Axes

The research axes of the MOSAIC project are succinctly presented in the following paragraphs.


<a id="org0a8e2ed"></a>

## Formalization and Probabilistic Modeling

Whether it is predicting the evolution of traditional assets [3] [4], or cryptocurrencies
[5] [6] [7], scientists working on the development of probabilistic models primarily focus on parametric approaches. This is mainly due to the simplicity and relative interpretability of these models. However, parametric approaches struggle to accurately represent the extreme behaviors of volatile assets. Recent articles have shown the interest of non-parametric methods in predicting the evolution of Bitcoin [8]
[9]. These more complex models appear to be incompatible with considering exogenous variables that explain the behavior of the considered assets.

Our objective is to overcome this limitation by proposing a discrete non-parametric approach (the
distribution of asset returns is discretized). To our knowledge, this approach has not been tested
in the context of crypto-assets and has the advantage of being compatible with relevant
probabilistic modeling techniques (e.g. Bayesian techniques) to address the problem. 


<a id="org4fcdbc9"></a>

# Technical Analysis

In the field of financial market analysis, technical analysis refers to a set of tools aimed at
predicting the future returns of financial assets by studying the historical market data available,
primarily the price and volume of the considered assets [10]. In the
literature review article on technical analysis [11], the authors
list the main analysis methodologies implemented over the past fifty years.  

The majority of the presented methodologies rely on the construction of specific indicators deemed
relevant by their authors (e.g. [12],
[13]). However, the evaluation of these indicators is only based on empirical
backtesting on arbitrarily chosen and relatively short periods, especially in the case of intraday
analysis. 

Like the authors of the article [11], we agree that assessing the
performance of technical analysis requires mathematical consolidation. 

Contributions:

-   Development of an innovative [strategy for evaluating technical indicators](indicator_analysis.md) based on the analysis of
    the conditional distribution of returns relative to observed indicators.


<a id="orgb416cd4"></a>

# References

[1]A. Stachtchenko, “Manuel de survie dans la jungle des poncifs anti-Bitcoin (version longue),” Medium. Jan. 2022. Accessed: Feb. 08, 2022. [Online]. Available: <https://medium.com/@AlexStach/manuel-de-survie-dans-la-jungle-des-poncifs-anti-bitcoin-version-longue-523e381745ff>

[2]D.-Y. Park and K.-H. Lee, “Practical Algorithmic Trading Using State Representation Learning and Imitative Reinforcement Learning,” Ieee access, vol. PP, p. 1, Nov. 2021, doi: 10.1109/ACCESS.2021.3127209.

[3]J. Shen, A Stochastic LQR Model for Child Order Placement in Algorithmic Trading. 2020.

[4]D. Snow, “Machine Learning in Asset Management - Part 1 : Portfolio Construction - Trading Strategies,” The journal of financial data science, vol. 2, no. 1, pp. 10–23, Jan. 2020, doi: 10.3905/jfds.2019.1.021.

[5]E. Bouri, C. K. M. Lau, B. Lucey, and D. Roubaud, “Trading volume and the predictability of return and volatility in the cryptocurrency market,” Finance research letters, vol. 29, pp. 340–346, Jun. 2019, doi: 10.1016/j.frl.2018.08.015.

[6]N. Crone, E. Brophy, and T. Ward, Exploration of Algorithmic Trading Strategies for the Bitcoin Market. 2021.

[7]P. Hansen, C. Kim, and W. Kimbrough, Periodicity in Cryptocurrency Volatility and Liquidity. 2021.

[8]M. Balcilar, E. Bouri, R. Gupta, and D. Roubaud, “Can volume predict Bitcoin returns and volatility? A quantiles-based approach,” Economic modelling, vol. 64, pp. 74–81, Aug. 2017, doi: 10.1016/j.econmod.2017.03.019.

[9]I. Jiménez, A. Mora-Valencia, and J. Perote, “Semi-nonparametric risk assessment with cryptocurrencies,” Research in international business and finance, vol. 59, p. 101567, Jan. 2022, doi: 10.1016/j.ribaf.2021.101567.

[10]R. Yamamoto, “Intraday technical analysis of individual stocks on the Tokyo Stock Exchange,” Journal of banking & finance, vol. 36, no. 11, pp. 3033–3047, Nov. 2012, doi: 10.1016/j.jbankfin.2012.07.006.

[11]R. T. Farias Nazário, J. L. e Silva, V. A. Sobreiro, and H. Kimura, “A literature review of technical analysis on stock markets,” The quarterly review of economics and finance, vol. 66, pp. 115–126, Nov. 2017, doi: 10.1016/j.qref.2017.01.014.

[12]A. Hassanniakalager, G. Sermpinis, and C. Stasinakis, “Trading the foreign exchange market with technical analysis and Bayesian Statistics,” Journal of empirical finance, vol. 63, pp. 230–251, Sep. 2021, doi: 10.1016/j.jempfin.2021.07.006.

[13]D. Bao and Z. Yang, “Intelligent stock trading system by turning point confirming and probabilistic reasoning,” Expert systems with applications, vol. 34, no. 1, pp. 620–627, Jan. 2008, doi: 10.1016/j.eswa.2006.09.043.

