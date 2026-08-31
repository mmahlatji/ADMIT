import { useState } from "react";
import { FileUploadRow } from "../../components/FileUploadRow";
import "./FileUpload.css";
import Header from "../../components/Header";
import { api } from "../../lib/api";

type UploadSlot = {
  id: string;
  label: string;
  file: File | null;
  accept?: string;
};

// const UPLOAD_ENDPOINT = "/api/uploads"; // adjust to your actual endpoint

const FILE_ACCEPT = ".xlsx,.xls, .csv";

const SLOTS: UploadSlot[] = [
  { id: "asr", label: "ASR", file: null, accept: FILE_ACCEPT },
  {
    id: "it_transcripts",
    label: "ITTranscripts",
    file: null,
    accept: FILE_ACCEPT,
  },
  { id: "motivations", label: "Motivations", file: null, accept: FILE_ACCEPT },
  { id: "uct_marks", label: "UCTMarks", file: null, accept: FILE_ACCEPT },
];

export function FileUpload() {
  const [files, setFiles] = useState<Record<string, File | null>>(
    Object.fromEntries(SLOTS.map((s) => [s.id, null])),
  );
  const [uploading, setUploading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSelect = (id: string, file: File) => {
    setFiles((prev) => ({ ...prev, [id]: file }));
  };

  const anySelected = SLOTS.some((s) => files[s.id] !== null);

  const handleUploadAll = async () => {
    setUploading(true);
    setErrors({});
    try {
      //gets the files that where actually uploaded
      const slotsToUpload = SLOTS.filter((s) => files[s.id] !== null);

      const uploadSlot = (slot: UploadSlot) => {
        const formData = new FormData();
        formData.append("file", files[slot.id]!);
        return api.request(`/imports/${slot.id}`, {
          method: "POST",
          body: formData,
        });
      };

      // ASR has to finish before the others start. It is the only source that
      // creates applicants, and marks/motivations/transcripts all look one up
      // by campus_id and flag the row when it is missing. Uploading everything
      // at once raced them against ASR and produced spurious "no applicant
      // found" rows in matching review.
      const asr = slotsToUpload.filter((s) => s.id === "asr");
      const rest = slotsToUpload.filter((s) => s.id !== "asr");

      const results = [
        ...(await Promise.allSettled(asr.map(uploadSlot))),
        ...(await Promise.allSettled(rest.map(uploadSlot))),
      ];
      const orderedSlots = [...asr, ...rest];

      const newErrors: Record<string, string> = {};
      results.forEach((result, i) => {
        if (result.status === "rejected") {
          newErrors[orderedSlots[i].id] =
            result.reason?.message ?? "Upload failed";
        }
      });
      setErrors(newErrors);

      if (Object.keys(newErrors).length === 0) {
        alert("Files uploaded succesfully");
        // navigate("/workspace")
      }
    } catch (error) {
      console.error(error);
      setErrors({ _global: "Something went wrong." });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload-page">
      <Header />
      <div className="file-upload-body">
        <div className="file-upload-container">
          <h3 className="file-upload-title">File Upload: </h3>
          {SLOTS.map((slot) => (
            <FileUploadRow
              key={slot.id}
              slot={{ ...slot, file: files[slot.id] }}
              onSelect={handleSelect}
              error={errors[slot.id]}
            />
          ))}
          {errors._global && (
            <p className="file-upload-error">{errors._global}</p>
          )}
          <div className="button-container">
            <button
              type="button"
              disabled={!anySelected || uploading}
              onClick={handleUploadAll}
              className="file-upload-submit"
            >
              {uploading ? "Uploading..." : "Upload"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
