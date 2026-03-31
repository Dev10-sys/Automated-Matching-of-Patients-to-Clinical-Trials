import React, { useState, useEffect } from 'react';

interface Filter {
  id: string;
  label: string;
  type: string;
}

interface Trial {
  trial_id: string;
  trial_name: string;
  match_score: number;
  criteria_summary: string;
  trial_link: string;
  status?: string;
}

const API_BASE = '';

const TrialMatchingPage: React.FC = () => {
  const [availableFilters, setAvailableFilters] = useState<Filter[]>([]);
  const [selectedFilterIds, setSelectedFilterIds] = useState<string[]>([]);
  const [filterValues, setFilterValues] = useState<Record<string, any>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<Trial[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/filters`)
      .then(res => res.json())
      .then(data => setAvailableFilters(data))
      .catch(err => {
        console.error('Failed to fetch filters:', err);
        setError('Could not load filters from server.');
      });
  }, []);

  const addFilter = (filter: Filter) => {
    if (!selectedFilterIds.includes(filter.id)) {
      setSelectedFilterIds([...selectedFilterIds, filter.id]);
    }
    setSearchTerm('');
  };

  const removeFilter = (id: string) => {
    setSelectedFilterIds(selectedFilterIds.filter(f => f !== id));
    const newValues = { ...filterValues };
    delete newValues[id];
    setFilterValues(newValues);
  };

  const handleInputChange = (id: string, value: any) => {
    setFilterValues({ ...filterValues, [id]: value });
  };

  const runMatching = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filters: filterValues }),
      });
      
      if (!response.ok) throw new Error('Matching request failed');
      
      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError('An error occurred while finding matching trials. Please check backend logs.');
    } finally {
      setLoading(false);
    }
  };

  const filteredOptions = availableFilters.filter(f => 
    f.label.toLowerCase().includes(searchTerm.toLowerCase()) && 
    !selectedFilterIds.includes(f.id)
  );

  return (
    <div className="trial-matching-container">
      <header className="header">
        <h1>Clinical Trial Matching Dashboard</h1>
        <p>Filter-based patient-to-trial matching interface for GEARBOx</p>
      </header>

      <div className="info-box">
        <div className="info-step"><span className="step-num">1</span> Search and add patient filters</div>
        <div className="info-step"><span className="step-num">2</span> Enter patient data</div>
        <div className="info-step"><span className="step-num">3</span> Run trial matching</div>
        <div className="info-step"><span className="step-num">4</span> View matching trials</div>
      </div>

      <main className="matching-layout">
        <aside className="controls-card">
          <div className="search-section">
            <h3 style={{ marginBottom: '15px' }}>Filter Selection</h3>
            <div style={{ position: 'relative' }}>
              <input 
                type="text" 
                className="search-input"
                placeholder="Search attributes (e.g. Age, Diagnosis...)"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              {searchTerm && (
                <div className="search-results">
                  {filteredOptions.length > 0 ? (
                    filteredOptions.map(f => (
                      <div key={f.id} className="search-result-item" onClick={() => addFilter(f)}>
                        + {f.label}
                      </div>
                    ))
                  ) : (
                    <div className="search-result-item">No filters found</div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="selected-filters-section" style={{ marginTop: '40px' }}>
            <h3 style={{ marginBottom: '15px' }}>Patient Attributes</h3>
            {selectedFilterIds.length === 0 ? (
              <p className="empty-state" style={{ padding: '20px' }}>No attributes selected. Search above to begin.</p>
            ) : (
              <div className="selected-filters-list">
                {selectedFilterIds.map(id => {
                  const filter = availableFilters.find(f => f.id === id);
                  if (!filter) return null;
                  return (
                    <div key={id} className="filter-item">
                      <div className="filter-item-header">
                        <span>{filter.label}</span>
                        <span className="remove-filter" onClick={() => removeFilter(id)}>Remove</span>
                      </div>
                      <input 
                        type={filter.type}
                        className="filter-input"
                        placeholder={`Enter ${filter.label.toLowerCase()}`}
                        onChange={(e) => handleInputChange(id, filter.type === 'number' ? parseFloat(e.target.value) : e.target.value)}
                      />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <button 
            className="match-btn" 
            onClick={runMatching}
            disabled={loading || selectedFilterIds.length === 0}
          >
            {loading ? 'Processing...' : 'Run Matching'}
          </button>
        </aside>

        <section className="results-card">
          <h3 style={{ marginBottom: '25px' }}>Matching Clinical Trials</h3>
          
          {error && <div style={{ color: 'red', marginBottom: '20px', padding: '15px', background: '#ffebeb', borderRadius: '8px' }}>{error}</div>}

          {loading ? (
            <div className="loading-spinner">
              <span>Finding matching trials...</span>
            </div>
          ) : results.length > 0 ? (
            <table className="results-table">
              <thead>
                <tr>
                  <th>Trial ID</th>
                  <th>Trial Title</th>
                  <th>Match Score</th>
                  <th>Eligibility Summary</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {results.map(trial => (
                  <tr key={trial.trial_id}>
                    <td style={{ fontWeight: 600 }}>{trial.trial_id}</td>
                    <td>
                      <a href={trial.trial_link} target="_blank" rel="noreferrer" className="trial-link">
                        {trial.trial_name}
                      </a>
                    </td>
                    <td>
                      <span className={`match-score-badge ${
                        trial.match_score > 0.7 ? 'score-high' : 
                        trial.match_score > 0.4 ? 'score-medium' : 'score-low'
                      }`}>
                        {(trial.match_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: '#475569' }}>
                      {trial.criteria_summary}
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: '4px', background: '#e2e8f0' }}>
                        {trial.status || 'Recruiting'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <p>Select patient attributes and run matching to view eligible clinical trials.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default TrialMatchingPage;
