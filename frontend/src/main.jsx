import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
// ❌ Remove BrowserRouter
// import { BrowserRouter, Route, Routes } from 'react-router-dom';

// ✅ Use HashRouter instead
import { HashRouter, Route, Routes } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HashRouter>
      <Routes>
        {/* User site */}
        <Route path="/*" element={<App />} />
      </Routes>
    </HashRouter>
  </React.StrictMode>,
);
