import React from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip, ResponsiveContainer
} from 'recharts';

interface MatchRadarProps {
  scores: {
    metric: string;
    value: number;
  }[];
}

const MatchRadar: React.FC<MatchRadarProps> = ({ scores }) => {
  const labeledScores = scores.map(item => ({
    ...item,
    metric: item.metric === 'tech_req' ? 'requirements' : item.metric
  }));

  return (
    <div className="w-full h-64">
      <ResponsiveContainer>
        <RadarChart outerRadius="80%" data={labeledScores}>
          <PolarGrid />
          <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} tickLine={false} />
          <PolarRadiusAxis angle={30} domain={[0, 1]} tick={false} />
          <Radar
            name="Match Score"
            dataKey="value"
            stroke="#4f46e5"
            fill="#6366f1"
            fillOpacity={0.6}
            isAnimationActive={true}
          />
          <Tooltip formatter={(value: number, name: string) => [`${(value * 100).toFixed(0)}%`, name]} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MatchRadar;
