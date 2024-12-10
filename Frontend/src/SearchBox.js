// SearchBox.js
import React, { useState } from 'react';
import axios from 'axios';
import loadingGif from './img/basketball-sports.gif'; 

const SearchBox = ({ setResults }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false); // New loading state

  const handleFindSimilarTitlesSearch = async (searchQuery) => {
    try {
      const response = await axios.post('http://localhost:8000/api/find_similar_titles', { sentence: searchQuery });
      console.log("find_similar_titles Response:", response.data);
      const { original_sentence, simplified_sentence, tagged_output, similar_titles } = response.data;

      return {
        original_sentence,
        simplified_sentence,
        tagged_output,
        similar_titles: similar_titles.filter(title => title.similarity_score > 0.4)
      };
    } catch (error) {
      console.error("Error fetching similar titles:", error);
      return null;
    }
  };

  const handlePlayerStatisticsSearch = async (searchQuery) => {
    try {
      const response = await axios.post('http://localhost:8000/api/player_statistics', { text: searchQuery });
      console.log("player_statistics Response:", response.data);
      return response.data;
    } catch (error) {
      console.error("Error fetching player statistics:", error);
      return null;
    }
  };

  const handleMatchStatisticsSearch = async (searchQuery) => {
    try {
      const response = await axios.post('http://localhost:8000/api/match_statistics', { text: searchQuery });
      console.log("match_statistics Response:", response.data);
      return response.data;
    } catch (error) {
      console.error("Error fetching match statistics:", error);
      return null;
    }
  };

  const handleSearch = async (searchQuery = query) => {
    setLoading(true); // Start loading
    try {
      const [similarTitlesResult, playerStatisticsResult, matchStatisticsResult] = await Promise.all([
        handleFindSimilarTitlesSearch(searchQuery),
        handlePlayerStatisticsSearch(searchQuery),
        handleMatchStatisticsSearch(searchQuery)
      ]);

      console.log("Combined Results:", { similarTitlesResult, playerStatisticsResult, matchStatisticsResult });

      setResults({
        similarTitlesResult,
        playerStatisticsResult,
        matchStatisticsResult
      });

      setQuery(searchQuery);
    } catch (error) {
      console.error("Error in combined search:", error);
    } finally {
      setLoading(false); // Stop loading
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Cari disini"
          style={{
            padding: '12px 16px',
            width: '300px',
            border: '2px solid #ff0000',
            borderRadius: '25px 0 0 25px',
            fontSize: '16px',
            outline: 'none',
            boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.1)',
          }}
        />
        <button
          onClick={() => handleSearch()}
          style={{
            padding: '12px 20px',
            backgroundColor: '#ff9900',
            color: 'white',
            border: '2px solid #ff0000',
            borderRadius: '0 25px 25px 0',
            fontSize: '16px',
            fontWeight: 'bold',
            cursor: 'pointer',
            boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.1)',
            transition: 'background-color 0.3s',
          }}
          onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#e68a00'}
          onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#ff9900'}
        >
          Cari
        </button>
      </div>
      {loading && (
        <div className="loading-overlay">
          <img src={loadingGif} alt="Loading animation" className="loading-gif" />
          <p className="loading-text">Loading...</p>
        </div>
      )}
    </div>
  );
};

export default SearchBox;
