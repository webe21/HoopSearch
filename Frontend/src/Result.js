// Result.js
import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import SearchBox from './SearchBox';
import logo from './img/hoopsearch.png';
import axios from 'axios';

const Result = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchResults, setSearchResults] = useState(location.state || {});
  const [expandedMatchId, setExpandedMatchId] = useState(null);  // Track the ID of the expanded match
  const [expandedMatchData, setExpandedMatchData] = useState(null);  // Store the expanded match data
  const [teamTab, setTeamTab] = useState('home');

  const handleSearch = (data) => {
    navigate('/results', { state: data });
    setSearchResults(data);
  };

  // Function to fetch match details from the backend
  const fetchMatchDetails = async (matchId) => {
    try {
      const response = await axios.post('http://localhost:8000/api/match_details', { match_id: matchId });
      setExpandedMatchId(matchId);  // Set the currently expanded match ID
      setExpandedMatchData(response.data);  // Store the fetched match details
    } catch (error) {
      console.error("Error fetching match details:", error);
    }
  };  

  const toggleReadMore = (matchId) => {
    if (expandedMatchId === matchId) {
      setExpandedMatchId(null); // Collapse if already expanded
    } else {
      fetchMatchDetails(matchId); // Fetch and expand the clicked match
      setExpandedMatchId(matchId); // Set the clicked match as expanded
    }
  };  

  // Check for valid player statistics data by verifying it's not the "no data" message
  const hasValidPlayerStatistics = searchResults.playerStatisticsResult &&
    searchResults.playerStatisticsResult.player_averages &&
    searchResults.playerStatisticsResult.player_averages.message !== "Tidak ada tag B-PER dalam teks.";

  // Check for valid match data by verifying it's not the "no data" message
  const hasValidMatchData = searchResults.matchStatisticsResult &&
    searchResults.matchStatisticsResult.match_data &&
    searchResults.matchStatisticsResult.match_data.message !== "Tidak ada tag B-ORG dalam teks.";

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', backgroundColor: '#ffffff', minHeight: '100vh' }}>
      {/* Navbar with SearchBox */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '10px 0',
        backgroundColor: '#ffffff',
        borderBottom: '3px solid #ff0000'
      }}>
        <img src={logo} alt="Logo" style={{ height: '75px', marginRight: '10px' }} />
        <SearchBox setResults={handleSearch} />
      </div>

      {/* Player Statistics - Display only if valid data exists */}
      {hasValidPlayerStatistics && (
        <div style={{ paddingTop: '20px', width: '80%', margin: '0 auto' }}>
          <h3>Statistik Pemain:</h3>
          <div>
            {Object.entries(searchResults.playerStatisticsResult.player_averages).map(([player, stats], index) => (
              <div key={index} style={{
                border: '1px solid #ddd',
                padding: '15px',
                margin: '10px 0',
                borderRadius: '5px',
                backgroundColor: '#ffffff',
                boxShadow: '0px 0px 10px rgba(0, 0, 0, 0.1)',
                textAlign: 'center'
              }}>
                {/* Player Name */}
                <p style={{ fontWeight: 'bold', fontSize: '40px', marginBottom: '10px' }}>{player}</p>

                {/* Total Points and Total Games */}
                <div style={{ fontSize: '16px', color: '#333', marginBottom: '20px' }}>
                  <p><strong>Total Point:</strong> {stats.total_points}</p>
                  <p><strong>Total Pertandingan:</strong> {stats.total_game}</p>
                </div>

                {/* Circular Statistics in Two Rows */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'center' }}>
                  {/* Top Row - First 7 items */}
                  <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', marginBottom: '10px' }}>
                    {Object.entries(stats).slice(0, 7).map(([key, value]) => (
                      key !== 'total_points' && key !== 'total_game' && (
                        <div key={key} className="stat-circle">
                          <div className="stat-value">{value}</div>
                          <div className="stat-key">{key.toUpperCase()}</div>
                        </div>
                      )
                    ))}
                  </div>
                  {/* Bottom Row - Next 7 items */}
                  <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', marginBottom: '10px' }}>
                    {Object.entries(stats).slice(7, 14).map(([key, value]) => (
                      key !== 'total_points' && key !== 'total_game' && (
                        <div key={key} className="stat-circle">
                          <div className="stat-value">{value}</div>
                          <div className="stat-key">{key.toUpperCase()}</div>
                        </div>
                      )
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Match Data - Display only if valid data exists */}
      {hasValidMatchData && (
        <div style={{ paddingTop: '20px', width: '80%', margin: '0 auto' }}>
          <h3>Statistik Permainan:</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {Object.entries(searchResults.matchStatisticsResult.match_data).map(([team, matches]) => (
              Array.isArray(matches) ? (
                matches.map((match, idx) => (
                  <div key={idx} style={{
                    border: '1px solid #ddd',
                    padding: '15px',
                    borderRadius: '5px',
                    backgroundColor: '#ffffff',
                    boxShadow: '0px 0px 10px rgba(0, 0, 0, 0.1)',
                    textAlign: 'center',
                    marginBottom: '20px'
                  }}>
                    <p style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '5px' }}>
                      {match.home_team} {match.home_score} - {match.away_score} {match.away_team}
                    </p>
                    <p style={{ fontSize: '14px', color: '#555' }}>{match.date}</p>
                    <button 
                      onClick={() => toggleReadMore(match.match_id)} 
                      style={{
                        backgroundColor: '#ff9900',
                        color: 'white',
                        border: 'none',
                        padding: '8px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        marginTop: '10px'
                      }}
                    >
                      {expandedMatchId === match.match_id ? "Show Less" : "Read More"}
                    </button>

                    {/* Display Tabs for Home and Away Team Details */}
                    {expandedMatchId === match.match_id && expandedMatchData && (
                      <div style={{ marginTop: '20px', width: '100%' }}>
                        <div style={{
                          display: 'flex',
                          justifyContent: 'left',
                          borderBottom: '1px solid #ddd',
                          marginBottom: '10px'
                        }}>
                          <button 
                            onClick={() => setTeamTab('home')}
                            style={{
                              padding: '10px 20px',
                              cursor: 'pointer',
                              fontWeight: teamTab === 'home' ? 'bold' : 'normal',
                              borderBottom: teamTab === 'home' ? '3px solid #ff9900' : 'none'
                            }}
                          >
                            Home Team
                          </button>
                          <button 
                            onClick={() => setTeamTab('away')}
                            style={{
                              padding: '10px 20px',
                              cursor: 'pointer',
                              fontWeight: teamTab === 'away' ? 'bold' : 'normal',
                              borderBottom: teamTab === 'away' ? '3px solid #ff9900' : 'none'
                            }}
                          >
                            Away Team
                          </button>
                        </div>

                        {/* Display the Table for Selected Team */}
                        {teamTab === 'home' ? (
                          <div>
                            <h4 style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '10px' }}>Home Team: {expandedMatchData.home_team.name}</h4>
                            <p>Score: {expandedMatchData.home_team.score}</p>
                            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '10px', textAlign: 'left'}}>
                              <thead>
                                <tr>
                                  <th>Name</th>
                                  <th>PTS</th>
                                  <th>REB</th>
                                  <th>AST</th>
                                  <th>MIN</th>
                                  <th>FGM</th>
                                  <th>FGA</th>
                                  <th>2PM</th>
                                  <th>2PA</th>
                                  <th>3PM</th>
                                  <th>3PA</th>
                                  <th>FTM</th>
                                  <th>FTA</th>
                                  <th>+/−</th>
                                  <th>OR</th>
                                  <th>DR</th>
                                  <th>PF</th>
                                  <th>ST</th>
                                  <th>TO</th>
                                </tr>
                              </thead>
                              <tbody>
                                {expandedMatchData.home_team.players.map((player, playerIdx) => (
                                  <tr key={playerIdx} style={{ textAlign: 'left' }}>
                                    <td>{player.name}</td>
                                    <td>{player.points}</td>
                                    <td>{player.rebounds}</td>
                                    <td>{player.assists}</td>
                                    <td>{player.minutes_played}</td>
                                    <td>{player.fgm}</td>
                                    <td>{player.fga}</td>
                                    <td>{player.two_pm}</td>
                                    <td>{player.two_pa}</td>
                                    <td>{player.three_pm}</td>
                                    <td>{player.three_pa}</td>
                                    <td>{player.ftm}</td>
                                    <td>{player.fta}</td>
                                    <td>{player.plus_minus}</td>
                                    <td>{player.offensive_rebounds}</td>
                                    <td>{player.defensive_rebounds}</td>
                                    <td>{player.fouls}</td>
                                    <td>{player.steals}</td>
                                    <td>{player.turnovers}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div>
                            <h4 style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '10px' }}>Away Team: {expandedMatchData.away_team.name}</h4>
                            <p>Score: {expandedMatchData.away_team.score}</p>
                            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                              <thead>
                                <tr>
                                  <th>Name</th>
                                  <th>PTS</th>
                                  <th>REB</th>
                                  <th>AST</th>
                                  <th>MIN</th>
                                  <th>FGM</th>
                                  <th>FGA</th>
                                  <th>2PM</th>
                                  <th>2PA</th>
                                  <th>3PM</th>
                                  <th>3PA</th>
                                  <th>FTM</th>
                                  <th>FTA</th>
                                  <th>+/−</th>
                                  <th>OR</th>
                                  <th>DR</th>
                                  <th>PF</th>
                                  <th>ST</th>
                                  <th>TO</th>
                                </tr>
                              </thead>
                              <tbody>
                                {expandedMatchData.away_team.players.map((player, playerIdx) => (
                                  <tr key={playerIdx} style={{ textAlign: 'left' }}>
                                    <td>{player.name}</td>
                                    <td>{player.points}</td>
                                    <td>{player.rebounds}</td>
                                    <td>{player.assists}</td>
                                    <td>{player.minutes_played}</td>
                                    <td>{player.fgm}</td>
                                    <td>{player.fga}</td>
                                    <td>{player.two_pm}</td>
                                    <td>{player.two_pa}</td>
                                    <td>{player.three_pm}</td>
                                    <td>{player.three_pa}</td>
                                    <td>{player.ftm}</td>
                                    <td>{player.fta}</td>
                                    <td>{player.plus_minus}</td>
                                    <td>{player.offensive_rebounds}</td>
                                    <td>{player.defensive_rebounds}</td>
                                    <td>{player.fouls}</td>
                                    <td>{player.steals}</td>
                                    <td>{player.turnovers}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p key={team} style={{ color: '#888' }}>No match data available for {team}.</p>
              )
            ))}
          </div>
        </div>
      )}

      {/* Related Articles */}
      <div style={{ paddingTop: '20px', width: '80%', margin: '0 auto' }}>
        <h3>Artikel Terkait:</h3>
        <div>
          {searchResults.similarTitlesResult && searchResults.similarTitlesResult.similar_titles && searchResults.similarTitlesResult.similar_titles.length > 0 ? (
            searchResults.similarTitlesResult.similar_titles.map((item, index) => (
              <div key={index} style={{
                border: '1px solid #ddd',
                padding: '15px',
                margin: '10px 0',
                borderRadius: '5px',
                backgroundColor: '#ffffff',
                boxShadow: '0px 0px 10px rgba(0, 0, 0, 0.1)'
              }}>
                <p style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '5px' }}>
                  {item.title}
                </p>
                <p style={{ fontSize: '14px', color: '#555', marginBottom: '5px' }}>
                  {item.summary}
                </p>
                <a href={item.link} target="_blank" rel="noopener noreferrer" style={{ color: '#ff9900', fontSize: '14px', textDecoration: 'none' }}>
                  {item.link}
                </a>
              </div>
            ))
          ) : (
            <p style={{ color: '#888' }}>Mohon maaf artikel yang anda cari tidak ada.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Result;
