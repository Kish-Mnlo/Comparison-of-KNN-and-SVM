import { useState } from 'react';
import './Admin.css';

function Admin() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL;

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    setMessage('');
    setError('');

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      setFile(null);
      setError('Please select a CSV file.');
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a CSV file first.');
      return;
    }

    setUploading(true);
    setMessage('');
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/admin/update-data`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        setError(result.error || 'Failed to update the dataset.');
        return;
      }

      setMessage(result.message || 'Dataset updated successfully.');
      setFile(null);

      document.getElementById('csv-file').value = '';
    } catch (error) {
      console.error('Error uploading CSV:', error);
      setError('Could not connect to the server.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-card">

        <h1>ADMIN DASHBOARD</h1>

        <h2>PSEI DATA MANAGEMENT</h2>

        <p className="admin-description">
          Upload a CSV file containing the latest PSEI market data.
        </p>

        <form onSubmit={handleUpload}>

          <div className="file-section">
            <label htmlFor="csv-file">
              Select PSEI CSV File
            </label>

            <input
              id="csv-file"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
            />
          </div>

          {file && (
            <p className="selected-file">
              Selected file: <strong>{file.name}</strong>
            </p>
          )}

          <button
            type="submit"
            disabled={!file || uploading}
            className="upload-button"
          >
            {uploading ? 'UPLOADING...' : 'UPDATE PSEI DATA'}
          </button>

        </form>

        {message && (
          <div className="success-message">
            ✓ {message}
          </div>
        )}

        {error && (
          <div className="error-message">
            ✕ {error}
          </div>
        )}

      </div>
    </div>
  );
}

export default Admin;