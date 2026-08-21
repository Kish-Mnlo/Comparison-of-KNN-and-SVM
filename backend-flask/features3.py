import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis
from scipy.fft import fft

#MOVING AVERAGES
def SMA_ratio(series, window):
    sma = series.rolling(window).mean()
    return (series - sma) / sma  

#WEIGHTED MEAN AVE
def WMA_ratio(series, window):
    weights = np.arange(1, window + 1)
    wma = series.rolling(window).apply(
        lambda x: np.dot(x, weights) / weights.sum(),
        raw=True
    )
    return (series - wma) / wma

#STOCHASTIC OSCILLATOR
def Stochastic_K(high, low, close, window=14):
    lowest = low.rolling(window).min()
    highest = high.rolling(window).max()
    denom = highest - lowest

    return 100 * ((close - lowest) / denom.replace(0, np.nan)).fillna(0)

def Stochastic_D(k, window=3):
    return k.rolling(window).mean()

#ACCUMULATION DISTRIBUTION OSCILLATOR
def AD_ratio(high, low, close, volume, window=20):
    denom = high - low
    clv = ((close - low) - (high - close)) / denom.replace(0, np.nan)
    clv = clv.fillna(0)
    ad_flow = clv * volume
    
    rolling_vol = volume.rolling(window).sum()
    rolling_ad = ad_flow.rolling(window).sum()
    return rolling_ad / rolling_vol.replace(0, np.nan)


#PERCENTAGE DIFFERENCES
def pct_diff_low(close, low, window=14):
    lowest = low.rolling(window).min()
    return (close - lowest) / lowest.replace(0, np.nan)

#FOURIER FEATURES
def FFT_features(series, window=20):
    mins = np.full(len(series), np.nan)
    maxs = np.full(len(series), np.nan)

    values = series.to_numpy()

    for i in range(window, len(series)):
        window_values = values[i-window:i]

        fft_vals = np.abs(fft(window_values))

        mins[i] = np.min(fft_vals)
        maxs[i] = np.max(fft_vals)

    return mins, maxs

#STATISTICAL FEATURES
def rolling_skew(series, window):
    return series.pct_change().rolling(window).apply(skew, raw=True) 

def rolling_kurtosis(series, window):
    return series.pct_change().rolling(window).apply(kurtosis, raw=True) 

def rolling_sd(series, window):
    return series.pct_change().rolling(window).std() 

#BUILD FEATURE MATRIX
def build_features(df):
    df = df.copy()

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    df["SMA"] = SMA_ratio(close, 14)
    df["WMA"] = WMA_ratio(close, 14)

    df["StochD"] = Stochastic_D(Stochastic_K(high, low, close))

    df["AD"] = AD_ratio(high, low, close, volume)

    df["PctDiffLow"] = pct_diff_low(close, low)


    fft_min, fft_max = FFT_features(close)
    df["FFT_Min"] = fft_min
    df["FFT_Max"] = fft_max

    df["Skewness"] = rolling_skew(close, 20)
    df["Kurtosis"] = rolling_kurtosis(close, 20)
    df["SD"] = rolling_sd(close, 20)

    return df
