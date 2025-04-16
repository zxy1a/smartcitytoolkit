import React, { useState } from 'react';

interface Recommendation {
  score: number;
  case_name: string;
  application_scenarios: string;
  technology_stack: string[];
  city_size: string;
  budget_range: number[];
  match_reasons: string[];
}

function App() {
  const [formData, setFormData] = useState({
    applicationScenarios: '',
    tps: 1000,
    latency: 200,
    securityLevel: 'high',
    technologyStack: 'Hyperledger, IPFS',
    citySize: 'large',
    budgetRange: '[500000, 1000000]'
  });

  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;

    setFormData(prev => ({
      ...prev,
      [name]: name === 'tps' || name === 'latency'
        ? Number(value)
        : value
    }));
  };

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError('');

    try {
      const payload = {
        applicationScenarios: formData.applicationScenarios,
        technicalRequirements: JSON.stringify({
          tps: formData.tps,
          latency: formData.latency,
          security_level: formData.securityLevel
        }),
        technologyStack: formData.technologyStack,
        citySize: formData.citySize,
        budgetRange: formData.budgetRange
      };

      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Analysis failed');

      const result = await response.json();

      const validatedRecs = result.recommendations.map((rec: any) => ({
        ...rec,
        budget_range: Array.isArray(rec.budget_range)
          ? rec.budget_range.map(Number)
          : [0, 0],
        score: Number(rec.score) || 0
      }));

      setRecommendations(validatedRecs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
      <div className="w-full max-w-xl p-6 bg-white rounded-2xl shadow">
        <h2 className="text-2xl font-bold mb-4">Smart City Blockchain Tool</h2>

        {error && <div className="mb-4 text-red-500">{error}</div>}

        <div className="space-y-4">
          <div>
            <label className="block mb-1 font-medium">Application Scenarios</label>
            <textarea
              name="applicationScenarios"
              value={formData.applicationScenarios}
              onChange={handleChange}
              className="w-full p-2 border rounded"
              placeholder="Describe your application scenarios..."
              rows={4}
            />
          </div>

          <div>
            <label className="block mb-1 font-medium">Technical Requirements</label>

            <div className="grid grid-cols-2 gap-4 mb-3">
              <div>
                <label className="block text-sm mb-1">TPS</label>
                <input
                  type="number"
                  name="tps"
                  value={formData.tps}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm mb-1">Latency (ms)</label>
                <input
                  type="number"
                  name="latency"
                  value={formData.latency}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                  min="1"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm mb-1">Security Level</label>
              <select
                name="securityLevel"
                value={formData.securityLevel}
                onChange={handleChange}
                className="w-full p-2 border rounded"
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block mb-1 font-medium">
              Technology Stack (comma-separated)
              <span className="text-sm text-gray-500 ml-2">e.g. Hyperledger, IPFS, Solidity</span>
            </label>
            <input
              name="technologyStack"
              value={formData.technologyStack}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            />
          </div>

          <div>
            <label className="block mb-1 font-medium">City Size</label>
            <select
              name="citySize"
              value={formData.citySize}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            >
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </select>
          </div>

          <div>
            <label className="block mb-1 font-medium">
              Budget Range (JSON array)
              <span className="text-sm text-gray-500 ml-2">e.g. [500000, 1000000]</span>
            </label>
            <input
              name="budgetRange"
              value={formData.budgetRange}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            />
          </div>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={isLoading}
          className="mt-6 bg-green-500 text-white px-4 py-2 rounded w-full hover:bg-green-600 disabled:bg-gray-400"
        >
          {isLoading ? 'Analyzing...' : 'Analyze'}
        </button>

        {recommendations.length > 0 && (
          <div className="mt-8">
            <h3 className="text-xl font-semibold mb-4">Recommendations</h3>
            <div className="space-y-4">
              {recommendations.map((rec, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium">{rec.case_name}</h4>
                    <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      Score: {rec.score}
                    </span>
                  </div>
                  <p className="text-sm mb-2">{rec.application_scenarios}</p>
                  <div className="text-sm space-y-1">
                    <div>📍 City Size: {rec.city_size}</div>
                    <div>💰 Budget: ${rec.budget_range[0].toLocaleString()} - ${rec.budget_range[1].toLocaleString()}</div>
                    <div>🛠 Technologies: {rec.technology_stack.join(', ')}</div>
                    <div className="mt-2 text-green-600">
                      {rec.match_reasons.join(' • ')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;