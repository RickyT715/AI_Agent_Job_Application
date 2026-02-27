import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

interface ScoreRadarChartProps {
  breakdown: Record<string, number>;
}

const DIMENSIONS = ["skills", "experience", "education", "location", "salary"];

export function ScoreRadarChart({ breakdown }: ScoreRadarChartProps) {
  const data = DIMENSIONS.map((dim) => ({
    dimension: dim.charAt(0).toUpperCase() + dim.slice(1),
    score: breakdown[dim] ?? 0,
  }));

  return (
    <div data-testid="radar-chart" style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="dimension" />
          <PolarRadiusAxis domain={[0, 10]} />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#2563eb"
            fill="#3b82f6"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
