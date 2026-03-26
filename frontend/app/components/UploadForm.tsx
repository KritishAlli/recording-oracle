"use client";
import { useState } from "react";

function UploadForm({ meetingId }: {meetingId: number}) {

    const [file, setFile] = useState<File | null>(null);
    const [uploadStatus, setUploadStatus] = useState<string>("");

      async function handleUpload() {
        if (!file) {
            return;
        }
        const formData = new FormData();
        formData.append("file", file)
        setUploadStatus("Uploading...")

        // call our API endpoint
        const res = await fetch(
            `http://localhost:8000/meetings/${meetingId}/upload`,
            { method: "POST", body: formData}
        );
        if (res.ok) {
            const data = await res.json();
            setUploadStatus(`Uploaded! S3 key: ${data.s3_key}`);
          } else {
            setUploadStatus("Upload failed.");
          }

      }
      return (
        <div>
          <input
            type="file"
            accept="audio/*,video/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <button onClick={handleUpload}>Upload</button>
          <p>{status}</p>
        </div>
      );


}
export default UploadForm;