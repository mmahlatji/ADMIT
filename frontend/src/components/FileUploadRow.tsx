import { useRef } from "react";
import { Plus } from "lucide-react";
import "./FileUploadRow.css";

type UploadSlot = {
  id: string;
  label: string; // e.g. "Transcript", "ID Document"
  file: File | null;
  accept?: string; // e.g. ".pdf,.docx"
};

export function FileUploadRow({
  slot,
  onSelect,
  error,
}: {
  slot: UploadSlot;
  onSelect: (id: string, file: File) => void;
  error?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="file-upload-row">
      <div className="file-upload-info">
        <span className="file-upload-label">{slot.label}</span>
        <span className="file-upload-filename">
          {slot.file ? slot.file.name : "No file selected"}
        </span>
        {error && <span className="file-upload-row-error">{error}</span>}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={slot.accept}
        className="file-upload-hidden-input"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onSelect(slot.id, file);
        }}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        aria-label={`Upload ${slot.label}`}
        className="file-upload-add-button"
      >
        <Plus size={16} />
      </button>
    </div>
  );
}
