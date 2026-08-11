import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis
from scipy.fft import fft

# ==========================================================
# Moving Averages
# ==========================================================

# MODIFIED: Changed from absolute price output to a percentage ratio.
# DELETED old logic: return series.rolling(window).mean()
def SMA_ratio(series, window):
    sma = series.rolling(window).mean()
    return (series - sma) / sma  # FIXED: Measures relative distance to prevent price-scale mismatch

# MODIFIED: Changed from absolute price output to a percentage ratio.
def WMA_ratio(series, window):
    weights = np.arange(1, window + 1)
    wma = series.rolling(window).apply(
        lambda x: np.dot(x, weights) / weights.sum(),
        raw=True
    )
    return (series - wma) / wma  # FIXED: Stationarized metric


# ==========================================================
# Stochastic Oscillator
# ==========================================================

def Stochastic_K(high, low, close, window=14):
    lowest = low.rolling(window).min()
    highest = high.rolling(window).max()
    denom = highest - lowest
    # FIXED: Added safety replacement for division by zero on flat days
    return 100 * ((close - lowest) / denom.replace(0, np.nan)).fillna(0)

def Stochastic_D(k, window=3):
    return k.rolling(window).mean()


# ==========================================================
# Accumulation Distribution Oscillator
# ==========================================================

# MODIFIED: Scaled cumulative volume value using rolling average volume.
# DELETED old logic: return (clv * volume).cumsum()
def AD_ratio(high, low, close, volume, window=20):
    denom = high - low
    clv = ((close - low) - (high - close)) / denom.replace(0, np.nan)
    clv = clv.fillna(0)
    ad_flow = clv * volume
    
    # FIXED: Cumulative values grow infinitely across time splits. 
    # Normalizing by rolling volume binds features to a consistent scale.
    rolling_vol = volume.rolling(window).mean()
    return ad_flow.cumsum() / rolling_vol.replace(0, np.nan)


# ==========================================================
# Percentage Differences
# ==========================================================

def pct_diff_low(close, low, window=14):
    lowest = low.rolling(window).min()
    return (close - lowest) / lowest.replace(0, np.nan)

# ==========================================================
# Fourier Features
# ==========================================================

def FFT_features(series, window=20):
    mins = []
    maxs = []

    values = series.values

    for i in range(len(series)):
        if i < window:
            mins.append(np.nan)
            maxs.append(np.nan)

            continue

        # FIXED Look-Ahead Bug: values[i-window:i] evaluates up to i-1.
        # This is safe, but because it maps to row index `i`, we protect it with a shift below.
        fft_vals = np.abs(fft(values[i-window:i]))
        mins.append(np.min(fft_vals))
        maxs.append(np.max(fft_vals))


    return mins, maxs

# ==========================================================
# Statistical Features
# ==========================================================

# MODIFIED: Calculated metrics on percentage changes instead of absolute close prices.
# DELETED old logic: return series.rolling(window).apply(skew/kurtosis/std, raw=True)
def rolling_skew(series, window):
    return series.pct_change().rolling(window).apply(skew, raw=True)  # FIXED: Stationarized

def rolling_kurtosis(series, window):
    return series.pct_change().rolling(window).apply(kurtosis, raw=True)  # FIXED: Stationarized

def rolling_sd(series, window):
    return series.pct_change().rolling(window).std()  # FIXED: Stationarized

# ==========================================================
# Build Feature Matrix
# ==========================================================

def build_features(df):
    df = df.copy()

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # FIXED/MODIFIED: Adjusted pointers to call newly stationarized ratio metrics
    df["SMA"] = SMA_ratio(close, 14)
    df["WMA"] = WMA_ratio(close, 14)

    df["StochD"] = Stochastic_D(Stochastic_K(high, low, close))

    df["AD"] = AD_ratio(high, low, close, volume)

    df["PctDiffLow"] = pct_diff_low(close, low)

    # FIXED Look-Ahead Bug: Applied .shift(1) to all Fourier metrics.
    # DELETED old logic: directly assigning lists to dataframe without an added offset shift.
    fft_min, fft_max = FFT_features(close)
    df["FFT_Min"] = pd.Series(fft_min, index=df.index).shift(1)
    df["FFT_Max"] = pd.Series(fft_max, index=df.index).shift(1)

    df["Skewness"] = rolling_skew(close, 20)
    df["Kurtosis"] = rolling_kurtosis(close, 20)
    df["SD"] = rolling_sd(close, 20)

    return df