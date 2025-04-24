import React from "react";

interface Weights {
  scenario: number;
  tech_req: number;
  tech_stack: number;
  city_size: number;
  budget: number;
}

interface WeightSlidersProps {
  weights: Weights;
  onChange: (newWeights: Weights) => void;
}

const WeightSliders: React.FC<WeightSlidersProps> = ({ weights, onChange }) => {
  const handleChange = (key: keyof Weights, value: number) => {
    onChange({ ...weights, [key]: value });
  };

  return (
    <div className="grid gap-4">
      {Object.entries(weights).map(([key, val]) => (
        <div key={key}>
          <label className="block text-sm font-medium mb-1">{key}</label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={val}
            onChange={(e) => handleChange(key as keyof Weights, parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="text-xs text-gray-500">Weight: {val.toFixed(2)}</div>
        </div>
      ))}
    </div>
  );
};

export default WeightSliders;
