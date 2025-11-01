import { Upload, FileText, X } from 'lucide-react';

export default function ResumeUpload({ file, onFileSelect, onFileRemove }) {
  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.pdf')) {
      onFileSelect(droppedFile);
    }
  };

  const handleFileInput = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  };

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <FileText className="w-5 h-5 mr-2 text-blue-400" />
        Upload Resume
      </h2>
      
      {!file ? (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed border-gray-700 rounded-lg p-12 text-center hover:border-blue-500 transition-colors cursor-pointer"
        >
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileInput}
            className="hidden"
            id="resume-upload"
          />
          <label htmlFor="resume-upload" className="cursor-pointer">
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-500" />
            <p className="text-lg font-medium text-gray-300 mb-2">
              Drop your resume here
            </p>
            <p className="text-sm text-gray-500">
              or click to browse (PDF files only)
            </p>
          </label>
        </div>
      ) : (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileText className="w-8 h-8 text-blue-400" />
            <div>
              <p className="font-medium text-gray-200">{file.name}</p>
              <p className="text-sm text-gray-500">
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </div>
          </div>
          <button
            onClick={onFileRemove}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      )}
    </div>
  );
}