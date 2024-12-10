// Home.js
import React from 'react';
import SearchBox from './SearchBox';
import { useNavigate } from 'react-router-dom';
import logo from './img/hoopsearch.png';

const Home = () => {
  const navigate = useNavigate();

  const handleSearch = (data) => {
    navigate('/results', { state: data });
  };

  return (
    <div style={{ textAlign: 'center', fontFamily: 'Arial, sans-serif', paddingTop: '50px', backgroundColor: '#ffffff', minHeight: '100vh' }}>
      <header style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
        <img src={logo} alt="Hoop Search IBL" style={{ width: '300px', borderRadius: '10px' }} />
        <SearchBox setResults={handleSearch} />
      </header>
    </div>
  );
};

export default Home;
