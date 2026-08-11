import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import stockDown from './assets/stock_down.png'
import stockUp from './assets/stock_up.png'
import './App.css'
import './OpeningBanner.css'
import Admin from './Admin'

function OpeningBanner(){
  return (
    <div className="open-banner">
      <h2 className='open-line'>PREDICTING THE PHILIPPINE STOCK EXCHANGE INDEX</h2>
    </div>
  )
}

function Candlestick(){
  return (
    <div className='chart-card'>
      <h2 className='chart-title'>PSEI CANDLESTICK CHART</h2>
      <iframe
        src="/psei_chart.html"
        width="100%"
        height="600"
        title="PSEI stock price chart"
        className="chart-frame"
      />
      <div className="chart-legend">
        <span className="legend-title">LEGEND:</span>
        <span className="legend-item bearish">
          <span className="dot color-red"></span>Bearish
        </span>
        <span className="legend-item bullish">
          <span className="dot color-green"></span>Bullish
        </span>
      </div>
    </div>
  )
}
function OhlcvData({
  data,
  setData,
  setNextData,
  setPrediction,
})  {
  const [algo, setAlgo] = useState('KNN');
  const [stock_date, setDate] = useState('');
  const API_URL = import.meta.env.VITE_API_URL;
  const today = new Date().toISOString().split('T')[0];


  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${API_URL}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          stock_date,
          algorithm: algo,
        }),
      });

      if (!response.ok) {
        const err = await response.json()
        alert(err.error)
        return
      }

      const result = await response.json();
      setData(result.data);
      setNextData(result.next_data);
      setPrediction(result.results);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  return (
    <div className="ohlcv-container">
      <div className="Model-container">
        <span className="label-text">Select prediction algorithm:</span>
        <button 
          className={algo === 'KNN' ? 'active-Button' : 'inactive-Button'} 
          onClick={() => setAlgo('KNN')}
          type = "button"
        >
          KNN
        </button>
        <button 
          className={algo === 'SVM' ? 'active-Button' : 'inactive-Button'} 
          onClick={() => setAlgo('SVM')}
          type = "button"
        >
          SVM
        </button>
      </div>

      <div className="data-box">
        <form onSubmit={handleSubmit} className="box-header">
          <div className="box-title">OHLCV DATA</div>
          <div className="form-controls">
            <input 
              type="date" 
              id="date"
              name="stock_date" 
              value={stock_date} 
              min="2016-01-01"
              max={today}
              onChange={(e) => {
                const selectedDate = new Date(e.target.value);
                const day = selectedDate.getDay();
            
                // 0 = Sunday, 6 = Saturday
                if (day === 0 || day === 6) {
                  return;
                }
            
                setDate(e.target.value);
              }}
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

function PredictionResults({nextData, prediction}){
  return (
    <div className='pr-card'>
      <h2 className='pr-title'>PREDICTION RESULTS</h2>
      {prediction ? (
        <div> 
          <div className='pr-symbol'><img src={prediction?.Prediction == "Higher" ? stockUp : stockDown} className="stock-symbol"/></div>
          <div className='pr-sellbuy'>This suggests that investors should {prediction?.Prediction == "Higher" ? "buy" : "sell"}.</div>
        </div>
      ) : (
        <div className='pr-warning'>Prediction results will show here.</div>
      )}
      

      <div>
        <h2 className='pr-nextTradingDay'>NEXT TRADING DAY</h2>
        <div className='pr-table-container'>
          <table className='pr-table'>
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
              </tr>) : (
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
  )
}
function App() {
  const [data, setData] = useState(null);
  const [nextData, setNextData] = useState(null);
  const [prediction, setPrediction] = useState(null);

  return (
    <>
      <OpeningBanner />
      <Candlestick />
      <OhlcvData 
        data = {data}
        setData={setData}
        setNextData={setNextData}
        setPrediction={setPrediction}
      />
      <PredictionResults 
        nextData = {nextData}
        prediction={prediction}
      />
    </>
  )

    //return(<Admin />)
}
export default App
