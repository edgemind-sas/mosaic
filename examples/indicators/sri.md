
# Table des matières

1.  [Définition](#org2066201)
    1.  [Examples](#org3602ba2)
2.  [Performance prédictive](#orgfa1749d)
    1.  [Cas 1 : données BTC/USDC 5min](#orgf5449aa)
        1.  [Évaluation ponctuelle](#org253e760)
        2.  [Analyses paramétriques](#orga612e9b)
    2.  [Cas 2 : données BTC/USDC 4h](#org683229d)
        1.  [Évaluation ponctuelle](#org1cf42dd)
        2.  [Analyses paramétriques](#org3d1d75b)
3.  [Environnement technique](#orgd31881b)
4.  [Références](#org9d4c46b)



<a id="org2066201"></a>

# Définition

The Support Range Index (SRI) is an oscillator-type indicator. Its purpose is to identify the behavior of a security within its range of variation (minimum and maximum closing prices) over a sliding time frame. Additionally, the SRI also provides a measure of the occurrences where the minimum and maximum prices exit the range within the given time frame. Therefore, the SRI indicator takes the form of a triplet that measures the position of an asset's price relative to its current range of variation, as well as the intensity of upward and downward movements at the range boundaries.

Let's consider a window of size $m \in \mathbb{N}$, we define:

-   $\text{c}^{\text{min}}_{m, t} = \min_{t - m \le i \le t} \text{c}_{i}$: the minimum closing price of the asset within the interval from $t - m$ to the current interval $t$.
-   $\text{c}^{\text{max}}_{m, t} = \max_{t - m \le i \le t} \text{c}_{i}$: the maximum closing price of the asset within the interval from $t - m$ to the current interval $t$.
-   $R_{m, t} = \text{c}^{\text{max}}_{m, t} - \text{c}^{\text{min}}_{m, t}$: the range of variation of the closing price between the intervals $t - m$ and $t$.

We can then derive the Range Index (RI) at interval $t$ by considering a past time horizon of size $m$ as follows:

\begin{equation}
\text{RI}^{m}_{t} = 2 \frac{\text{c}_{t}}{R_{m,t}} - 1.
\end{equation}

The indicator $\text{RI}^{m}_{t}$ thus varies between -1 and 1. When $\text{RI}^{m}_{t}$ tends towards -1, it means that the current price is close to its minimum value over the last $m$ intervals. Conversely, when $\text{RI}^{m}_{t}$ tends towards 1, the current price is close to its maximum value over the last $m$ intervals.

We then define the number of high solicitations, denoted $N^{\text{h}, m}_{t}$, as follows:

\begin{equation}
\text{N}^{\text{h}, m}_{t} = \text{Card}~\{\text{h}_{k} | \text{h}_{k} > \text{c}^{\text{max}}_{m, t} ; t - m \le k \le t \};
\end{equation}

and similarly, the number of low solicitations, denoted $N^{\text{l}, m}_{t}$:

\begin{equation}
\text{N}^{\text{l}, m}_{t} = \text{Card}~\{\text{l}_{k} | \text{l}_{k} > \text{c}^{\text{min}}_{m, t} ; t - m \le k \le t \}.
\end{equation}

Finally, the Support Range Index (SRI) indicator is defined as the following triplet:

\begin{equation}
\text{SRI}^{m}_{t} = (\text{RI}^{m}_{t}, \text{N}^{\text{h}, m}_{t}, \text{N}^{\text{l}, m}_{t}).
\end{equation}


<a id="org3602ba2"></a>

## Examples

Afin d'illustrer les caractéristiques de l'indicateur SRI, nous allons récupérer des données OHLCV (Open, High, Low, Close, Volume)
depuis la plateforme Binance. Pour ce faire, la librairie MOSAIC possède la class `ExchangeCCXT`
permettant une connexion avec différente plateforme d'échanges : 

    import mosaic.trading as mtr
    
    exchange = mtr.ExchangeCCXT(name="binance")
    exchange.connect()

We now use the `get_historic_ohlcv` method from our `exchange` variable in order to retrieve
historic OHLCV data. We specify :

-   the start and end dates of the data range as `'2021-01-01 00:00:00'` to `'2021-01-02 00:00:00'`.
-   the symbol pair `'BTC/USDC'` symbol
-   the sample timeframe of 5 minutes

    ohlcv_ex_df = \
        exchange.get_historic_ohlcv(
            date_start='2021-01-01 00:00:00',
            date_end='2021-01-02 00:00:00',
            symbol='BTC/USDC',
            timeframe='5m',
            index="datetime",
            data_dir=".",
            progress_mode=True,
        )

The 'datetime' column is specified as the index for the returned data saved as a DataFrame.

The first observations are:

<style type="text/css">
</style>
<table id="T_62135">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_62135_level0_col0" class="col_heading level0 col0" >timestamp</th>
      <th id="T_62135_level0_col1" class="col_heading level0 col1" >open</th>
      <th id="T_62135_level0_col2" class="col_heading level0 col2" >high</th>
      <th id="T_62135_level0_col3" class="col_heading level0 col3" >low</th>
      <th id="T_62135_level0_col4" class="col_heading level0 col4" >close</th>
      <th id="T_62135_level0_col5" class="col_heading level0 col5" >volume</th>
    </tr>
    <tr>
      <th class="index_name level0" >datetime</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
      <th class="blank col5" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_62135_level0_row0" class="row_heading level0 row0" >2021-01-01 01:00:00+01:00</th>
      <td id="T_62135_row0_col0" class="data row0 col0" >1 609 459 200 000</td>
      <td id="T_62135_row0_col1" class="data row0 col1" >28 964.54</td>
      <td id="T_62135_row0_col2" class="data row0 col2" >29 064.55</td>
      <td id="T_62135_row0_col3" class="data row0 col3" >28 958.66</td>
      <td id="T_62135_row0_col4" class="data row0 col4" >29 018.17</td>
      <td id="T_62135_row0_col5" class="data row0 col5" >8.77</td>
    </tr>
    <tr>
      <th id="T_62135_level0_row1" class="row_heading level0 row1" >2021-01-01 01:05:00+01:00</th>
      <td id="T_62135_row1_col0" class="data row1 col0" >1 609 459 500 000</td>
      <td id="T_62135_row1_col1" class="data row1 col1" >28 993.74</td>
      <td id="T_62135_row1_col2" class="data row1 col2" >28 996.04</td>
      <td id="T_62135_row1_col3" class="data row1 col3" >28 890.99</td>
      <td id="T_62135_row1_col4" class="data row1 col4" >28 914.30</td>
      <td id="T_62135_row1_col5" class="data row1 col5" >11.15</td>
    </tr>
    <tr>
      <th id="T_62135_level0_row2" class="row_heading level0 row2" >2021-01-01 01:10:00+01:00</th>
      <td id="T_62135_row2_col0" class="data row2 col0" >1 609 459 800 000</td>
      <td id="T_62135_row2_col1" class="data row2 col1" >28 902.53</td>
      <td id="T_62135_row2_col2" class="data row2 col2" >28 908.49</td>
      <td id="T_62135_row2_col3" class="data row2 col3" >28 741.86</td>
      <td id="T_62135_row2_col4" class="data row2 col4" >28 790.00</td>
      <td id="T_62135_row2_col5" class="data row2 col5" >4.58</td>
    </tr>
    <tr>
      <th id="T_62135_level0_row3" class="row_heading level0 row3" >2021-01-01 01:15:00+01:00</th>
      <td id="T_62135_row3_col0" class="data row3 col0" >1 609 460 100 000</td>
      <td id="T_62135_row3_col1" class="data row3 col1" >28 798.99</td>
      <td id="T_62135_row3_col2" class="data row3 col2" >28 891.63</td>
      <td id="T_62135_row3_col3" class="data row3 col3" >28 798.29</td>
      <td id="T_62135_row3_col4" class="data row3 col4" >28 884.38</td>
      <td id="T_62135_row3_col5" class="data row3 col5" >4.31</td>
    </tr>
    <tr>
      <th id="T_62135_level0_row4" class="row_heading level0 row4" >2021-01-01 01:20:00+01:00</th>
      <td id="T_62135_row4_col0" class="data row4 col0" >1 609 460 400 000</td>
      <td id="T_62135_row4_col1" class="data row4 col1" >28 845.04</td>
      <td id="T_62135_row4_col2" class="data row4 col2" >28 886.67</td>
      <td id="T_62135_row4_col3" class="data row4 col3" >28 789.15</td>
      <td id="T_62135_row4_col4" class="data row4 col4" >28 885.73</td>
      <td id="T_62135_row4_col5" class="data row4 col5" >13.21</td>
    </tr>
  </tbody>
</table>

Considérons à présent les paramètres :

-   taille de la fenêtre glissante, $m =$ ;
-   discrétisation du $\text{RI}$ : .
-   discrétisation des sollicitations basses et hautes: .

Le calcul de l'indicateurs $\text{RI}$ sur l'échantillon de données précédent
conduit aux résultats suivants :

<style type="text/css">
</style>
<table id="T_047a9">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_047a9_level0_col0" class="col_heading level0 col0" >RI_10</th>
      <th id="T_047a9_level0_col1" class="col_heading level0 col1" >SRI_HL_10</th>
      <th id="T_047a9_level0_col2" class="col_heading level0 col2" >SRI_HH_10</th>
    </tr>
    <tr>
      <th class="index_name level0" >datetime</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_047a9_level0_row0" class="row_heading level0 row0" >2021-01-01 01:45:00+01:00</th>
      <td id="T_047a9_row0_col0" class="data row0 col0" >0.816891</td>
      <td id="T_047a9_row0_col1" class="data row0 col1" >2.000000</td>
      <td id="T_047a9_row0_col2" class="data row0 col2" >1.000000</td>
    </tr>
    <tr>
      <th id="T_047a9_level0_row1" class="row_heading level0 row1" >2021-01-01 01:50:00+01:00</th>
      <td id="T_047a9_row1_col0" class="data row1 col0" >0.994114</td>
      <td id="T_047a9_row1_col1" class="data row1 col1" >2.000000</td>
      <td id="T_047a9_row1_col2" class="data row1 col2" >3.000000</td>
    </tr>
    <tr>
      <th id="T_047a9_level0_row2" class="row_heading level0 row2" >2021-01-01 01:55:00+01:00</th>
      <td id="T_047a9_row2_col0" class="data row2 col0" >1.000000</td>
      <td id="T_047a9_row2_col1" class="data row2 col1" >2.000000</td>
      <td id="T_047a9_row2_col2" class="data row2 col2" >2.000000</td>
    </tr>
    <tr>
      <th id="T_047a9_level0_row3" class="row_heading level0 row3" >2021-01-01 02:00:00+01:00</th>
      <td id="T_047a9_row3_col0" class="data row3 col0" >1.000000</td>
      <td id="T_047a9_row3_col1" class="data row3 col1" >3.000000</td>
      <td id="T_047a9_row3_col2" class="data row3 col2" >0.000000</td>
    </tr>
    <tr>
      <th id="T_047a9_level0_row4" class="row_heading level0 row4" >2021-01-01 02:05:00+01:00</th>
      <td id="T_047a9_row4_col0" class="data row4 col0" >1.000000</td>
      <td id="T_047a9_row4_col1" class="data row4 col1" >2.000000</td>
      <td id="T_047a9_row4_col2" class="data row4 col2" >1.000000</td>
    </tr>
  </tbody>
</table>

Illustration graphique des indicateurs sur les données exemples.


<a id="orgfa1749d"></a>

# Performance prédictive

Dans cette section, nous évaluons la performance prédictive de l'indicateur à partir des scores
présentés dans document d'introduction d'analyse technique.

Les scores sont évalués empiriquement en utilisant des données historiques de cotations.


<a id="orgf5449aa"></a>

## Cas 1 : données BTC/USDC 5min

Caractéristiques de la source de données utilisée :


<a id="org253e760"></a>

### Évaluation ponctuelle

Paramétrage considéré :

-   taille de la fenêtre glissante, $m =$ ;
-   discrétisation du $\text{RI}$ : .
-   discrétisation des sollicitations basses et hautes: .

Temps de calcul :

-   sur les données considérées : s ;
-   soit s/data.

Occurrences de l'indicateur discrétisé :


Nombre d'occurrences de l'indicateur discrétisé sur un horizon donné
Distribution du nombre de periodes entre chaque configuration d'indicateur (period between
configuration, PBC).


<a id="orga612e9b"></a>

### Analyses paramétriques

Cette section présente une analyse paramétrique des performances de l'indicateur $\text{RI}$.

L'analyse est réalisée en calculant le score PAWER au niveau de risque sur la grille de paramètres suivants :

-   taille de la fenêtre glissante, $m =$ ;
-   discrétisation du $\text{RI}$ : .
-   discrétisation des sollicitations basses et hautes: .

Le tableau suivant présente les 30 paramétrages de
l'indicateur permettant d'obtenir les meilleurs rendements en considérant un taux d'occurrences
minimum de 0.05%, soit occurrences.


<a id="org683229d"></a>

## Cas 2 : données BTC/USDC 4h

Caractéristiques de la source de données utilisée :


<a id="org1cf42dd"></a>

### Évaluation ponctuelle

Paramétrage considéré :

-   taille de la fenêtre glissante, $m =$ ;
-   discrétisation du $\text{RI}$ : .
-   discrétisation des sollicitations basses et hautes: .

Temps de calcul :

-   sur les données considérées : s ;
-   soit s/data.

Occurrences de l'indicateur discrétisé :


<a id="org3d1d75b"></a>

### Analyses paramétriques

Cette section présente une analyse paramétrique des performances de l'indicateur $\text{RI}$.

L'analyse est réalisée en calculant le score PAWER au niveau de risque sur la grille de paramètres suivants :

-   taille de la fenêtre glissante, $m =$ ;
-   discrétisation du $\text{RI}$ : .
-   discrétisation des sollicitations basses et hautes: .

Le tableau suivant présente les 30 paramétrages de
l'indicateur permettant d'obtenir les meilleurs rendements en considérant un taux d'occurrences
minimum de 0.05%, soit occurrences.


<a id="orgd31881b"></a>

# Environnement technique

Les librairies `Python` utilisées dans les traitements présentés dans ce document sont :

<style type="text/css">
</style>
<table id="T_27099">
  <thead>
    <tr>
      <th id="T_27099_level0_col0" class="col_heading level0 col0" >Library</th>
      <th id="T_27099_level0_col1" class="col_heading level0 col1" >Version</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td id="T_27099_row0_col0" class="data row0 col0" >MOSAIC</td>
      <td id="T_27099_row0_col1" class="data row0 col1" >0.0.40</td>
    </tr>
  </tbody>
</table>


<a id="org9d4c46b"></a>

# Références

<../MOSAIC.bib>

