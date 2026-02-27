interface SkillGapAnalysisProps {
  strengths: string[];
  missingSkills: string[];
}

export function SkillGapAnalysis({ strengths, missingSkills }: SkillGapAnalysisProps) {
  return (
    <div className="skill-gap" data-testid="skill-gap">
      <div className="strengths">
        <h3>Strengths</h3>
        <ul>
          {strengths.map((s, i) => (
            <li key={i} className="strength-item">{s}</li>
          ))}
        </ul>
      </div>
      <div className="missing-skills">
        <h3>Missing Skills</h3>
        <ul>
          {missingSkills.map((s, i) => (
            <li key={i} className="missing-item">{s}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
