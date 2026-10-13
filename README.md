To run the dockerfile:

1. ```
   docker build -t psei-backend
   docker run -p 5000:5000 psei-backend
   ```
2. Then go to http://localhost:5000/

To run the frontend:
Please have these installed:
NPM, React/Vite, and VSCode

1. Clone the github repository and open it using VSCode.
2. Create a new terminal with command prompt.
3. ```
   cd cistudy-ui
   ```
4. ```
   npm install
   npm run dev
   ```

To run the backend:
Please have these installed:
Python, VSCode

1. While the front-end is running, create a new terminal with command prompt in VSCode.
2. ```
   cd backend-flask
   pip install requirements.txt
   py PSEIdata.py
   ```
