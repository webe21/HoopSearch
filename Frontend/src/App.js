import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from './Home';
import Result from './Result';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/results" element={<Result />} />
    </Routes>
  );
};

export default App;
