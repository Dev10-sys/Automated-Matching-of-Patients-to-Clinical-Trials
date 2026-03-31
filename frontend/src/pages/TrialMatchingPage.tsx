import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

interface FilterField {
  id: string;
  label: string;
  type: 'number' | 'text' | 'boolean';
}

interface SelectedFilter {
  field: FilterField;
  value: any;
}

interface TrialResult {
  trial_id: string;
  trial_name: string;
  match_score: number;
  criteria_summary: string;
  trial_link: string;
}

const TrialMatchingPage = () => {
  const [availableFilters, setAvailableFilters] = useState<FilterField[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<SelectedFilter[]>([]);
  const [results, setResults] = useState<TrialResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch available filters from backend
    fetch(`${API_BASE}/filters`)
      .then(res => res.json())
      .then(data => setAvailableFilters(data))
      .catch(err => {
        console.error("Error loading filters:", err);
        setError("Could not connect to backend. Make sure the API server is running on localhost:8000.");
      });
  }, []);

  const addFilter = (filter: FilterField) => {
    if (selectedFilters.some(sf => sf.field.id === filter.id)) return;
    setSelectedFilters([...selectedFilters, { field: filter, value: filter.type === 'boolean' ? false : '' }]);
    setSearchTerm('');
    setIsSearching(false);
  };

  const removeFilter = (id: string) => {
    setSelectedFilters(selectedFilters.filter(sf => sf.field.id !== id));
  };

  const handleValueChange = (id: string, value: any) => {
    setSelectedFilters(selectedFilters.map(sf => 
      sf.field.id === id ? { ...sf, value } : sf
    ));
  };

  const handleMatch = async () => {
    setIsLoading(true);
    setResults([]);
    setError(null);
    try {
      const patientData = {
        filters: selectedFilters.reduce((acc, sf) => ({ ...acc, [sf.field.id]: sf.value }), {})
      };
      
      const response = await fetch(`${API_BASE}/match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patientData)
      });
      
      if (!response.ok) throw new Error("Match request failed");
      
      const data = await response.json();
      setResults(data.results);
    } catch (err: any) {
      console.error(err);
      setError("An error occurred while finding matching trials. Please check backend logs.");
    } finally {
      setIsLoading(false);
    }
  };

  const filteredSearchOptions = availableFilters.filter(f => 
    f.label.toLowerCase().includes(searchTerm.toLowerCase()) && 
    !selectedFilters.some(sf => sf.field.id === f.id)
  );

  return (
    <div className="trial-matching-container">
      <header className="header">
        <h1>Patient Matching Hub</h1>
        <p>A clinical trial enrollment dashboard for medical professionals.</p>
      </header>

      {error && <div className="error-banner" style={{background: '#fee2e2', color: '#991b1b', padding: '12px', borderRadius: '8px', marginBottom: '20px'}}>{error}</div>}

      <div className="matching-layout">
        <aside className="controls-card">
          <section>
            <h3 style={{marginTop: 0}}>Quick Filter Search</h3>
            <div className="search-input-wrapper">
              <input 
                type="text" 
                className="search-input"
                placeholder="Type filter name (e.g. Age, Diagnosis...)"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setIsSearching(true);
                }}
                onFocus={() => setIsSearching(true)}
              />
              {isSearching && searchTerm && (
                <div className="search-results">
                  {filteredSearchOptions.length > 0 ? (
                    filteredSearchOptions.map(f => (
                      <div key={f.id} className="search-result-item" onClick={() => addFilter(f)}>
                        {f.label}
                      </div>
                    ))
                  ) : (
                    <div className="search-result-item" style={{color: '#94a3b8'}}>No filters found</div>
                  )}
                </div>
              )}
            </div>
          </section>

          <section>
            <h3>Selected Patient Filters</h3>
            <div className="selected-filters-list">
              {selectedFilters.length === 0 ? (
                <div style={{color: '#94a3b8', textAlign: 'center', margin: '40px 0'}}>
                  Select filters to start entering patient data.
                </div>
              ) : (
                selectedFilters.map(sf => (
                  <div key={sf.field.id} className="filter-item">
                    <div className="filter-item-header">
                      <span>{sf.field.label}</span>
                      <span className="remove-filter" onClick={() => removeFilter(sf.field.id)}>Remove</span>
                    </div>
                    {sf.field.type === 'boolean' ? (
                      <select 
                        className="filter-input"
                        value={sf.value}
                        onChange={(e) => handleValueChange(sf.field.id, e.target.value === 'true')}
                      >
                        <option value="false">No / False</option>
                        <option value="true">Yes / True</option>
                      </select>
                    ) : (
                      <input 
                        type={sf.field.type === 'number' ? 'number' : 'text'}
                        className="filter-input"
                        placeholder={`Enter ${sf.field.label.toLowerCase()}`}
                        value={sf.value}
                        onChange={(e) => handleValueChange(sf.field.id, sf.field.type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
                      />
                    )}
                  </div>
                ))
              )}
            </div>
          </section>

          <button 
            className="match-btn" 
            disabled={selectedFilters.length === 0 || isLoading}
            onClick={handleMatch}
          >
            {isLoading ? 'Running Match Engine...' : 'Find Matching Trials'}
          </button>
        </aside>

        <main className="results-card">
          <h2 style={{marginTop: 0, marginBottom: '24px'}}>Trial Match Results</h2>
          {isLoading ? (
            <div className="loading-spinner">Loading matches...</div>
          ) : results.length > 0 ? (
            <table className="results-table">
              <thead>
                <tr>
                  <th>Trial ID</th>
                  <th>Match Score</th>
                  <th>Criteria Summary</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {results.map(res => (
                  <tr key={res.trial_id}>
                    <td>
                      <div style={{fontWeight: 700}}>{res.trial_id}</div>
                      <div style={{fontSize: '0.8rem', color: '#64748b'}}>NCT ID</div>
                    </td>
                    <td>
                      <span className={`match-score-badge ${res.match_score > 0.7 ? 'score-high' : res.match_score > 0.4 ? 'score-medium' : 'score-low'}`}>
                        {(res.match_score * 100).toFixed(0)}% Match
                      </span>
                    </td>
                    <td style={{fontSize: '0.85rem', color: '#475569'}}>
                      {res.criteria_summary}
                    </td>
                    <td>
                      <a href={res.trial_link} target="_blank" rel="noopener noreferrer" className="trial-link">View Protocol</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              {error ? "There was a problem searching trials." : "Select filters on the left and run matching to see results."}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default TrialMatchingPage;
