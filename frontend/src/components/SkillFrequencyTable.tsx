import type { SkillFrequencyResponse } from "../types/api";

interface Props {
  skills: SkillFrequencyResponse[];
  onSkillClick?: (skillName: string) => void;
}

export function SkillFrequencyTable({ skills, onSkillClick }: Props) {
  if (skills.length === 0) {
    return <p data-testid="no-skills">No skills data available.</p>;
  }

  return (
    <table className="skill-frequency-table" data-testid="skill-frequency-table">
      <thead>
        <tr>
          <th>Skill</th>
          <th>Category</th>
          <th>Jobs</th>
          <th>%</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {skills.map((s) => (
          <tr
            key={s.skill_name}
            onClick={() => onSkillClick?.(s.skill_name)}
            style={{ cursor: onSkillClick ? "pointer" : "default" }}
          >
            <td>{s.skill_name}</td>
            <td>
              <span
                className={`badge ${s.category === "technical" ? "badge-technical" : "badge-soft"}`}
              >
                {s.category.replace("_", " ")}
              </span>
            </td>
            <td>{s.count}</td>
            <td>{s.percentage}%</td>
            <td>
              <div
                className="bar"
                style={{
                  width: `${s.percentage}%`,
                  height: "16px",
                  background: "#3b82f6",
                  borderRadius: "4px",
                }}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
