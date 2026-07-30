import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import Dashboard from './pages/Dashboard';

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('theme') === 'dark' || 
      (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  // Protected Route Wrapper
  const ProtectedRoute = ({ children }) => {
    const token = localStorage.getItem('token');
    if (!token) {
      return <Navigate to="/login" replace />;
    }
    return children;
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing darkMode={darkMode} toggleDarkMode={toggleDarkMode} />} />
        <Route path="/login" element={<Login darkMode={darkMode} toggleDarkMode={toggleDarkMode} />} />
        <Route path="/signup" element={<Signup darkMode={darkMode} toggleDarkMode={toggleDarkMode} />} />
        <Route path="/forgot-password" element={<ForgotPassword darkMode={darkMode} toggleDarkMode={toggleDarkMode} />} />
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
            </ProtectedRoute>
          } 
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
