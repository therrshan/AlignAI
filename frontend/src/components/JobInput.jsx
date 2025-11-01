import { Briefcase } from 'lucide-react';

export default function JobInput({ value, onChange }) {
  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <Briefcase className="w-5 h-5 mr-2 text-purple-400" />
        Job Description
      </h2>
      
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste the job description here...&#10;&#10;Include requirements, responsibilities, and preferred qualifications for best results."
        className="textarea-field"
        rows="12"
      />
      
      <p className="text-xs text-gray-500 mt-2">
        💡 Tip: Include the full job posting for better analysis
      </p>
    </div>
  );
}