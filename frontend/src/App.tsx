import React, { useState } from 'react';

function App() {
  const [formData, setFormData] = useState({
    applicationScenarios: '',
    technicalRequirements: '',
    technologyStack: '',
    citySize: '',
    budgetRange: '',
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    await fetch('http://localhost:8000/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    alert('Submitted!');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
      <div className="w-full max-w-xl p-6 bg-white rounded-2xl shadow">
        <h2 className="text-2xl font-bold mb-4">Smart City Blockchain Tool</h2>
        <textarea name="applicationScenarios" onChange={handleChange} placeholder="Application Scenarios" className="mb-2 w-full p-2 border rounded" />
        <textarea name="technicalRequirements" onChange={handleChange} placeholder="Technical Requirements" className="mb-2 w-full p-2 border rounded" />
        <input name="technologyStack" onChange={handleChange} placeholder="Technology Stack" className="mb-2 w-full p-2 border rounded" />
        <input name="citySize" onChange={handleChange} placeholder="City Size" className="mb-2 w-full p-2 border rounded" />
        <input name="budgetRange" onChange={handleChange} placeholder="Budget Range" className="mb-4 w-full p-2 border rounded" />
        <button onClick={handleSubmit} className="bg-blue-500 text-white px-4 py-2 rounded w-full">Submit</button>
      </div>
    </div>
  );
}

export default App;
