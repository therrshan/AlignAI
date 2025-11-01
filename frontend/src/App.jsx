import { useState } from 'react';
import axios from 'axios';
import Header from './components/Header';
import WorkspaceManager from './components/WorkspaceManager';
import ResumeUpload from './components/ResumeUpload';
import JobInput from './components/JobInput';
import AnalysisResults from './components/AnalysisResults';
import LoadingState from './components/LoadingState';
import ProjectsManager from './components/ProjectsManager';
import { Sparkles, AlertCircle, FileText, Database } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('analyze');
  const [workspaceId, setWorkspaceId] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!resumeFile || !jobDescription.trim()) {
      setError('Please upload a resume and enter a job description');
      return;
    }

    if (!workspaceId) {
      setError('Workspace not initialized. Please refresh the page.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('resume_file', resumeFile);
      formData.append('job_description', jobDescription);

      const response = await axios.post(`${API_URL}/api/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-Workspace-ID': workspaceId,
        },
      });

      setAnalysisResults(response.data);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.response?.data?.detail || 'Failed to analyze resume. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResumeFile(null);
    setJobDescription('');
    setAnalysisResults(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      
      <main className="container mx-auto px-6 py-8 max-w-7xl">
        {/* Workspace Manager */}
        <div className="mb-6">
          <WorkspaceManager onWorkspaceChange={setWorkspaceId} />
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-6 bg-gray-800 p-1 rounded-lg w-fit">
          <button
            onClick={() => setActiveTab('analyze')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors flex items-center space-x-2 ${
              activeTab === 'analyze'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Analyze Resume</span>
          </button>
          <button
            onClick={() => setActiveTab('projects')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors flex items-center space-x-2 ${
              activeTab === 'projects'
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Manage Projects</span>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'analyze' ? (
          <div className="space-y-6">
            {error && (
              <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-red-400">Error</p>
                  <p className="text-sm text-red-300">{error}</p>
                </div>
              </div>
            )}

            {!analysisResults ? (
              <>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ResumeUpload
                    file={resumeFile}
                    onFileSelect={setResumeFile}
                    onFileRemove={() => setResumeFile(null)}
                  />
                  
                  <JobInput
                    value={jobDescription}
                    onChange={setJobDescription}
                  />
                </div>

                {isLoading ? (
                  <LoadingState message="Analyzing your resume with AI..." />
                ) : (
                  <div className="flex justify-center">
                    <button
                      onClick={handleAnalyze}
                      disabled={!resumeFile || !jobDescription.trim() || !workspaceId}
                      className="btn-primary flex items-center space-x-2 text-lg px-8 py-4"
                    >
                      <Sparkles className="w-5 h-5" />
                      <span>Analyze Resume</span>
                    </button>
                  </div>
                )}
              </>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <h2 className="text-3xl font-bold">Analysis Results</h2>
                  <button
                    onClick={handleReset}
                    className="btn-secondary"
                  >
                    New Analysis
                  </button>
                </div>
                
                <AnalysisResults results={analysisResults} />
              </>
            )}
          </div>
        ) : (
          <ProjectsManager workspaceId={workspaceId} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-16">
        <div className="container mx-auto px-6 py-6 text-center text-sm text-gray-500">
          <p>Powered by LLaMA 3 • Built with FastAPI & React</p>
        </div>
      </footer>
    </div>
  );
}

export default App;