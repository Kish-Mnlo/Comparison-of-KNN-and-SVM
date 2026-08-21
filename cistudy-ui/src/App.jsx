import { useState, useEffect } from 'react'
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import stockDown from './assets/stock_down.png'
import stockUp from './assets/stock_up.png'
import sun from './assets/sun.png'
import moon from'./assets/moon.png'
import './App.css'
import './OpeningBanner.css'
import Admin from './Admin'
import PredictionChart from './PredictionChart.jsx'
import './PredictionChart.css'
import OpeningScreen from './Openingscreen.jsx'

function OpeningBanner(){
  return (
    <div className="open-banner">
      <h2 className='open-line'>PREDICTING THE PHILIPPINE STOCK EXCHANGE INDEX</h2>
      <h2 className='first-line'>NEXT-DAY DIRECTION</h2>
    </div>
  )
}

function OhlcvData({
  data,
  setData,
  setNextData,
  setPrediction,
   setPredictionHistory,
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

      setPredictionHistory((previousHistory) => [
        ...previousHistory,
        {
          date: result.data.Date,
          knnPrediction: result.results.KNN.Prediction,
          knnConfidence:
            result.results.KNN.Prediction === "Higher"
              ? result.results.KNN.Probability_Higher
              : result.results.KNN.Probability_Lower,
          svmPrediction: result.results.SVM.Prediction,
          svmConfidence:
            result.results.SVM.Prediction === "Higher"
              ? result.results.SVM.Probability_Higher
              : result.results.SVM.Probability_Lower,
          actual: result.actual
        }
      ]);
    } catch (error) {
      setError(error.error)
      setErrorMessage(error.message);
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
          minDate={new Date('2016-02-01')}
          maxDate={new Date(today)}
          dateFormat="MM/dd/yy"
          placeholderText="MM/DD/YY"
          showMonthDropdown
          showYearDropdown
          dropdownMode="select"
          yearDropdownItemNumber={new Date().getFullYear() - 2016 + 1}
          scrollableYearDropdown
        />
        <input type="submit" value="Submit" />
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

function PredictionResults({ nextData, prediction }) {
return ( <div className="pr-card"> <h2 className="pr-title">PREDICTION RESULTS</h2>
  {prediction ? (
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

        <p>
          Probability Higher:{" "}
          {prediction.KNN?.Probability_Higher}
        </p>

        <p>
          Probability Lower:{" "}
          {prediction.KNN?.Probability_Lower}
        </p>
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

        <p>
          Probability Higher:{" "}
          {prediction.SVM?.Probability_Higher}
        </p>

        <p>
          Probability Lower:{" "}
          {prediction.SVM?.Probability_Lower}
        </p>
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
          {nextData ? (
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
  </div>

</div>

);
}

function PredictionHistory({ predictionHistory }) {
  return (
    <div className="history-card">
      <h2 className="history-title">PREDICTION HISTORY</h2>

      {predictionHistory.length === 0 ? (
        <div className="pr-warning">
          Prediction history will show here.
        </div>
      ) : (
        <div className="table-responsive">
          <table className="history-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>KNN Prediction</th>
                <th>KNN Confidence</th>
                <th>SVM Prediction</th>
                <th>SVM Confidence</th>
                <th>Actual</th>
              </tr>
            </thead>

            <tbody>
              {predictionHistory.map((item, index) => (
                <tr key={index}>
                  <td>{item.date}</td>

                  <td>
                    {item.knnPrediction}
                  </td>

                  <td>
                    {item.knnConfidence}
                  </td>

                  <td>
                    {item.svmPrediction}
                  </td>

                  <td>
                    {item.svmConfidence}
                  </td>

                  <td>
                    {item.actual || "Pending"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function App() {
  const [data, setData] = useState(null);
  const [nextData, setNextData] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [predictionHistory, setPredictionHistory] = useState([]);
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
        setPredictionHistory={setPredictionHistory}
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

    //return(<Admin />)
}
export default App
