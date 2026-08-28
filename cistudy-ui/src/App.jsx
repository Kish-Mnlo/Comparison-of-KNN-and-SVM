import { useState, useEffect, useMemo } from 'react'
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import stockDown from './assets/stock_down.png'
import stockUp from './assets/stock_up.png'
import sun from './assets/sun.png'
import moon from'./assets/moon.png'
import './App.css'
import './OpeningBanner.css'
import PredictionChart from './PredictionChart.jsx'
import './PredictionChart.css'
import OpeningScreen from './Openingscreen.jsx'
import './Loading.css'
import './History.css'

function OpeningBanner(){
  return (
    <div className="open-banner">
      <h2 className='open-line'>PREDICTING THE PHILIPPINE STOCK EXCHANGE INDEX</h2>
      <h2 className='first-line'>NEXT-DAY DIRECTION</h2>
    </div>
  )
}

const DEFAULT_WAIT_MESSAGES = ['Please wait', 'Almost there', 'Just a moment more'];

function LoadingSpinner({ label, messages = DEFAULT_WAIT_MESSAGES, interval = 3000 }) {
  const [messageIndex, setMessageIndex] = useState(0);
  const isRotating = label === undefined;

  useEffect(() => {
    if (!isRotating) return;

    setMessageIndex(0);
    const timer = setInterval(() => {
      setMessageIndex((previousIndex) => (previousIndex + 1) % messages.length);
    }, interval);

    return () => clearInterval(timer);
  }, [isRotating, messages, interval]);

  const displayText = isRotating ? messages[messageIndex] : label;

  return (
    <div
      className="loading-state"
      role="status"
      aria-live="polite"
      aria-label={displayText ? undefined : 'Loading'}
    >
      {displayText && <span className="loading-text">{displayText}</span>}
      <span
        className={`loading-dots${displayText ? '' : ' loading-dots-standalone'}`}
        aria-hidden="true"
      >
        <span className="dot"></span>
        <span className="dot"></span>
        <span className="dot"></span>
      </span>
    </div>
  );
}

function OhlcvData({
  data,
  setData,
  setNextData,
  setPrediction,
  predictionHistory,
  setPredictionHistory,
  setActualDirection,
  isLoading,
  setIsLoading,
})  {
  const [stock_date, setDate] = useState('');
  const [error, setError] = useState('');
  const [error_message, setErrorMessage] = useState('');
  const API_URL = import.meta.env.VITE_API_URL;
  const today = new Date().toISOString().split('T')[0];

  const toLocalISODate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    // Prevent submitting a date that's already been predicted.
    const isDuplicateDate = predictionHistory.some(
      (item) => item.date === stock_date
    );

    if (isDuplicateDate) {
      setError('Duplicate Date');
      setErrorMessage('You already submitted a prediction for this date. Please choose a different date.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          stock_date
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        setError(err.error || "Something went wrong.") ;
        setErrorMessage(err.message || "Please try again.");
        return
      }

      const result = await response.json();
      setData(result.data);
      setNextData(result.next_data);
      setPrediction(result.results);
      setActualDirection(result.actual ?? null);

      setPredictionHistory((previousHistory) => [
        ...previousHistory,
        {
          id: `${result.data.Date}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          date: result.data.Date,
          knnPrediction: result.results.KNN.Prediction,
          svmPrediction: result.results.SVM.Prediction,
          actual: result.actual
        }
      ]);
    } catch (error) {
      setError(error.error)
      setErrorMessage(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="ohlcv-container">
    <div className="data-box">
    {error_message && (
          <div className="error-alert">
            <span className="error-icon">⚠️</span>

            <div>
              <strong>{error}</strong>
              <p>{error_message}</p>
            </div>

            <button
              type="button"
              onClick={() => setErrorMessage('')}
              className="close-alert"
            >x
            </button>
          </div>
        )}
    <form onSubmit={handleSubmit} className="box-header">
      <div className="box-title">OHLCV DATA</div>
      <div className="form-controls">
        <DatePicker
          id="date"
          name="stock_date"
          selected={stock_date ? new Date(stock_date + 'T00:00:00') : null}
          onChange={(date) => {
            if (!date || isNaN(date)) return;

            const day = date.getDay();

            // 0 = Sunday, 6 = Saturday
            if (day === 0 || day === 6) {
              return;
            }

            setDate(toLocalISODate(date));
          }}
          filterDate={(date) => date.getDay() !== 0 && date.getDay() !== 6}
          minDate={new Date('2024-01-04')}
          maxDate={new Date('2026-07-16')}
          dateFormat="MM/dd/yy"
          placeholderText="MM/DD/YY"
          showMonthDropdown
          showYearDropdown
          dropdownMode="select"
          yearDropdownItemNumber={new Date().getFullYear() - 2016 + 1}
          scrollableYearDropdown
        />
        <input type="submit" value={isLoading ? 'Loading...' : 'Submit'} disabled={isLoading} />
      </div>
    </form>

        <div className="table-responsive">
          <table className="ohlcv-table">
            <thead>
              <tr>
                <th className="ohlcv-header">Date</th>
                <th>Open</th>
                <th>High</th>
                <th>Low</th>
                <th>Close</th>
                <th>Volume</th>
              </tr>
            </thead>
            <tbody>
              {data ? (
                <tr>
                  <td>{data.Date}</td>
                  <td>{Number(data.Open).toFixed(2)}</td>
                  <td>{Number(data.High).toFixed(2)}</td>
                  <td>{Number(data.Low).toFixed(2)}</td>
                  <td>{Number(data.Close).toFixed(2)}</td>
                  <td>{Number(data.Volume).toFixed(2)}</td>
                </tr>
              ) : (
                <tr>
                  <td>--/--/----</td>
                  <td>0.00</td>
                  <td>0.00</td>
                  <td>0.00</td>
                  <td>0.00</td>
                  <td>0</td>
                </tr>
              )}

            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function PredictionResults({ nextData, prediction, isLoading, actualDirection }) {
  // Which model(s), if any, predicted the direction that actually happened.
  const matchingModels = actualDirection
    ? ['KNN', 'SVM'].filter((model) => prediction?.[model]?.Prediction === actualDirection)
    : [];

return ( <div className="pr-card"> <h2 className="pr-title">PREDICTION RESULTS</h2>
  {isLoading ? (
    <LoadingSpinner />
  ) : prediction ? (
    <div className="prediction-comparison">

      {/* KNN */}
      <div className="prediction-model">
        <h3>K-Nearest Neighbors</h3>

        <div className="pr-symbol">
          <img
            src={
              prediction.KNN?.Prediction === "Higher"
                ? stockUp
                : stockDown
            }
            className="stock-symbol"
          />
        </div>

        <h3>
          {prediction.KNN?.Prediction}
        </h3>

        <div className="pr-sellbuy">
          This suggests that investors should{" "}
          {prediction.KNN?.Prediction === "Higher"
            ? "buy"
            : "sell"}.
        </div>

        {actualDirection && (
          <p style={{ fontWeight: 'bold', color: prediction.KNN?.Prediction === actualDirection ? 'green' : 'red' }}>
            {prediction.KNN?.Prediction === actualDirection
              ? 'Matched the actual next-day direction'
              : 'Did not match the actual next-day direction'}
          </p>
        )}
      </div>


      {/* SVM */}
      <div className="prediction-model">
        <h3>Support Vector Machines</h3>

        <div className="pr-symbol">
          <img
            src={
              prediction.SVM?.Prediction === "Higher"
                ? stockUp
                : stockDown
            }
            className="stock-symbol"
          />
        </div>

        <h3>
          {prediction.SVM?.Prediction}
        </h3>

        <div className="pr-sellbuy">
          This suggests that investors should{" "}
          {prediction.SVM?.Prediction === "Higher"
            ? "buy"
            : "sell"}.
        </div>

        {actualDirection && (
          <p style={{ fontWeight: 'bold', color: prediction.SVM?.Prediction === actualDirection ? 'green' : 'red' }}>
            {prediction.SVM?.Prediction === actualDirection
              ? 'Matched the actual next-day direction'
              : 'Did not match the actual next-day direction'}
          </p>
        )}
      </div>

    </div>
  ) : (
    <div className="pr-warning">
      Prediction results will show here.
    </div>
  )}


  {/* NEXT TRADING DAY */}
  <div>
    <h2 className="pr-nextTradingDay">ACTUAL NEXT TRADING DAY</h2>

    <div className="pr-table-container">
      <table className="pr-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Open</th>
            <th>High</th>
            <th>Low</th>
            <th>Close</th>
            <th>Volume</th>
          </tr>
        </thead>

        <tbody>
          {isLoading ? (
            <tr>
              <td colSpan={6} className="table-loading-cell">
                <LoadingSpinner label="" />
              </td>
            </tr>
          ) : nextData ? (
            <tr>
              <td>{nextData.Date}</td>
              <td>{Number(nextData.Open).toFixed(2)}</td>
              <td>{Number(nextData.High).toFixed(2)}</td>
              <td>{Number(nextData.Low).toFixed(2)}</td>
              <td>{Number(nextData.Close).toFixed(2)}</td>
              <td>{Number(nextData.Volume).toFixed(2)}</td>
            </tr>
          ) : (
            <tr>
              <td>--/--/----</td>
              <td>0.00</td>
              <td>0.00</td>
              <td>0.00</td>
              <td>0.00</td>
              <td>0</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>

    {!isLoading && actualDirection && (
      <div style={{ marginTop: '10px', fontWeight: 'bold', color: 'white' }}>
        {matchingModels.length === 0 &&
          'No algorithm matched the actual next-day direction.'}
        {matchingModels.length === 1 &&
          `${matchingModels[0]} matched the actual next-day direction.`}
        {matchingModels.length === 2 &&
          'Both KNN and SVM matched the actual next-day direction.'}
      </div>
    )}
  </div>

</div>

);
}

const HISTORY_PAGE_SIZE = 10;

function PredictionHistory({ predictionHistory }) {
  const [sortMode, setSortMode] = useState('submitted'); // 'submitted' | 'date-asc' | 'date-desc'
  const [currentPage, setCurrentPage] = useState(1);

  const sortedHistory = useMemo(() => {
    if (sortMode === 'date-asc') {
      return [...predictionHistory].sort((a, b) => a.date.localeCompare(b.date));
    }
    if (sortMode === 'date-desc') {
      return [...predictionHistory].sort((a, b) => b.date.localeCompare(a.date));
    }
    // Default: latest submitted at the top, first submitted at the bottom.
    return [...predictionHistory].reverse();
  }, [predictionHistory, sortMode]);

  const totalPages = Math.max(1, Math.ceil(sortedHistory.length / HISTORY_PAGE_SIZE));
  const activePage = Math.min(currentPage, totalPages);
  const pageStart = (activePage - 1) * HISTORY_PAGE_SIZE;
  const pageItems = sortedHistory.slice(pageStart, pageStart + HISTORY_PAGE_SIZE);

  const handleSortToggle = () => {
    setCurrentPage(1);
    setSortMode((previous) => (previous === 'date-asc' ? 'date-desc' : 'date-asc'));
  };

  const handleResetSort = () => {
    setCurrentPage(1);
    setSortMode('submitted');
  };

  const goToPage = (page) => {
    setCurrentPage(Math.min(Math.max(page, 1), totalPages));
  };

  const sortIndicator =
    sortMode === 'date-asc' ? '▲' : sortMode === 'date-desc' ? '▼' : '↕';

  // Which algorithm(s), if any, matched the actual next-day direction for a given row.
  const getMatchLabel = (item) => {
    if (!item.actual) return 'Pending';

    const knnMatch = item.knnPrediction === item.actual;
    const svmMatch = item.svmPrediction === item.actual;

    if (knnMatch && svmMatch) return 'Both';
    if (knnMatch) return 'KNN';
    if (svmMatch) return 'SVM';
    return 'None';
  };

  // Per-model correct-prediction counts out of the number of dates selected so far.
  const totalDatesSelected = predictionHistory.length;
  const knnCorrectCount = predictionHistory.filter(
    (item) => item.actual && item.knnPrediction === item.actual
  ).length;
  const svmCorrectCount = predictionHistory.filter(
    (item) => item.actual && item.svmPrediction === item.actual
  ).length;

  return (
    <div className="history-card">
      <h2 className="history-title">PREDICTION HISTORY</h2>

      <div className="history-score">
        KNN: {knnCorrectCount} / {totalDatesSelected} matched 
        <br />
        SVM: {svmCorrectCount} / {totalDatesSelected} matched
      </div>

      {predictionHistory.length === 0 ? (
        <div className="pr-warning">
          Prediction history will show here.
        </div>
      ) : (
        <>
          <div className="table-responsive">
            <table className="history-table">
              <thead>
                <tr>
                  <th
                    className="sortable-header"
                    onClick={handleSortToggle}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') handleSortToggle();
                    }}
                    aria-label={`Sort by date, currently ${
                      sortMode === 'date-asc'
                        ? 'ascending'
                        : sortMode === 'date-desc'
                        ? 'descending'
                        : 'latest submitted first'
                    }`}
                  >
                    Date
                    <span className="sort-indicator" aria-hidden="true">{sortIndicator}</span>
                  </th>
                  <th>KNN Prediction</th>
                  <th>SVM Prediction</th>
                  <th>Next-Day Actual Direction</th>
                  <th>Which Algorithm Matches</th>
                </tr>
              </thead>

              <tbody>
                {pageItems.map((item) => (
                  <tr key={item.id ?? `${item.date}-${item.knnPrediction}-${item.svmPrediction}`}>
                    <td>{item.date}</td>

                    <td>
                      {item.knnPrediction}
                    </td>

                    <td>
                      {item.svmPrediction}
                    </td>

                    <td>
                      {item.actual || "Pending"}
                    </td>

                    <td>
                      {getMatchLabel(item)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="history-pagination">
            <button
              type="button"
              className="page-btn"
              onClick={() => goToPage(activePage - 1)}
              disabled={activePage === 1}
            >
              Previous
            </button>

            <span className="page-indicator">
              Page {activePage} of {totalPages}
            </span>

            <button
              type="button"
              className="page-btn"
              onClick={() => goToPage(activePage + 1)}
              disabled={activePage === totalPages}
            >
              Next
            </button>

            {sortMode !== 'submitted' && (
              <button type="button" className="page-btn reset-sort-btn" onClick={handleResetSort}>
                Reset sort
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function App() {
  const [data, setData] = useState(null);
  const [nextData, setNextData] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [predictionHistory, setPredictionHistory] = useState([]);
  const [actualDirection, setActualDirection] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('results');
  const [darkMode, setDarkMode] = useState(false);
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode);
  }, [darkMode]);

  if (showSplash) {
    return (
      <OpeningScreen
        appName="PSEi Predictor"
        tagline="predicting next-day direction"
        duration={2800}
        onFinish={() => setShowSplash(false)}
      />
    );
  }

  return (
    <>
      <div className="dark-toggle-wrapper">
        <button className="dark-toggle" onClick={() => setDarkMode(!darkMode)}>
          <img src={darkMode ? sun : moon} alt="" />
        </button>
      </div>

      <OpeningBanner />
      <OhlcvData
        data = {data}
        setData={setData}
        setNextData={setNextData}
        setPrediction={setPrediction}
        predictionHistory={predictionHistory}
        setPredictionHistory={setPredictionHistory}
        setActualDirection={setActualDirection}
        isLoading={isLoading}
        setIsLoading={setIsLoading}
      />

      <div className="tab-bar">
        <div>
          <button
            className={`tab-label ${activeTab === 'results' ? 'active' : ''}`}
            onClick={() => setActiveTab('results')}
          >
            Results
          </button>
          <button
            className={`tab-label ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
        </div>
      </div>

      {activeTab === 'results' && (
        <>

            <PredictionResults
              nextData={nextData}
              prediction={prediction}
              isLoading={isLoading}
              actualDirection={actualDirection}
            />


        </>
      )}

      {activeTab === 'history' && (
        <div className="pr-card">
          <PredictionChart predictionHistory={predictionHistory} />
          <PredictionHistory predictionHistory={predictionHistory} />
        </div>
      )}
    </>
  )

}
export default App