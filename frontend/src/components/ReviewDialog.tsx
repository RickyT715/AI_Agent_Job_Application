import { useState } from "react";

interface ReviewDialogProps {
  fieldsFilled: Record<string, string>;
  screenshotB64: string | null;
  onApprove: () => void;
  onReject: () => void;
  onEdit: (edits: Record<string, string>) => void;
}

export function ReviewDialog({
  fieldsFilled,
  screenshotB64,
  onApprove,
  onReject,
  onEdit,
}: ReviewDialogProps) {
  const [editMode, setEditMode] = useState(false);
  const [editedFields, setEditedFields] = useState<Record<string, string>>({ ...fieldsFilled });

  const handleFieldChange = (key: string, value: string) => {
    setEditedFields((prev) => ({ ...prev, [key]: value }));
  };

  const handleEditSubmit = () => {
    onEdit(editedFields);
    setEditMode(false);
  };

  return (
    <div className="review-dialog" role="dialog" aria-label="Review Application">
      <h2>Review Application</h2>

      {screenshotB64 && (
        <img
          src={`data:image/png;base64,${screenshotB64}`}
          alt="Application screenshot"
          className="screenshot"
          data-testid="screenshot"
        />
      )}

      <div className="filled-fields">
        <h3>Filled Fields</h3>
        {Object.entries(editMode ? editedFields : fieldsFilled).map(([key, value]) => (
          <div key={key} className="field-row">
            <label>{key}</label>
            {editMode ? (
              <input
                value={value}
                onChange={(e) => handleFieldChange(key, e.target.value)}
                aria-label={key}
              />
            ) : (
              <span>{value}</span>
            )}
          </div>
        ))}
      </div>

      <div className="review-actions">
        {editMode ? (
          <button onClick={handleEditSubmit}>Submit Changes</button>
        ) : (
          <>
            <button onClick={onApprove} data-testid="approve-btn">Approve</button>
            <button onClick={onReject} data-testid="reject-btn">Reject</button>
            <button onClick={() => setEditMode(true)} data-testid="edit-btn">Edit</button>
          </>
        )}
      </div>
    </div>
  );
}
