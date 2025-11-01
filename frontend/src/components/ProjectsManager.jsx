import { useState, useEffect } from 'react';
import { FolderGit2, Upload, Trash2, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ProjectsManager({ workspaceId }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    if (workspaceId) {
      fetchProjects();
    }
  }, [workspaceId]);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/projects`, {
        headers: {
          'X-Workspace-ID': workspaceId
        }
      });
      setProjects(response.data.projects || []);
    } catch (err) {
      console.error('Error fetching projects:', err);
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile || !workspaceId) return;

    setUploading(true);
    setMessage(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      await axios.post(`${API_URL}/api/upload-projects`, formData, {
        headers: {
          'X-Workspace-ID': workspaceId
        }
      });
      setMessage({ type: 'success', text: 'Projects uploaded successfully!' });
      setUploadFile(null);
      fetchProjects();
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Upload failed' });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (projectTitle) => {
    if (!confirm(`Delete project "${projectTitle}"?`)) return;

    try {
      await axios.delete(`${API_URL}/api/projects/${encodeURIComponent(projectTitle)}`, {
        headers: {
          'X-Workspace-ID': workspaceId
        }
      });
      setMessage({ type: 'success', text: 'Project deleted' });
      fetchProjects();
    } catch (err) {
      setMessage({ type: 'error', text: 'Delete failed' });
    }
  };

  if (!workspaceId) {
    return (
      <div className="card text-center py-8">
        <p className="text-gray-400">Loading workspace...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="card border-2 border-purple-800/50">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Upload className="w-5 h-5 mr-2 text-purple-400" />
          Upload Projects Database
        </h2>

        {message && (
          <div className={`mb-4 p-3 rounded-lg border flex items-center space-x-2 ${
            message.type === 'success' 
              ? 'bg-green-900/20 border-green-800 text-green-400' 
              : 'bg-red-900/20 border-red-800 text-red-400'
          }`}>
            {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            <span>{message.text}</span>
          </div>
        )}

        <div className="space-y-3">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setUploadFile(e.target.files[0])}
            className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700"
          />
          {uploadFile && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="btn-primary w-full"
            >
              {uploading ? 'Uploading...' : 'Upload & Store in Vector DB'}
            </button>
          )}
        </div>
      </div>

      {/* Projects List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold flex items-center">
            <FolderGit2 className="w-5 h-5 mr-2 text-green-400" />
            Stored Projects ({projects.length})
          </h2>
          <button
            onClick={fetchProjects}
            disabled={loading}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-5 h-5 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {loading ? (
          <p className="text-gray-500 text-center py-8">Loading projects...</p>
        ) : projects.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No projects stored yet. Upload a PDF to get started.</p>
        ) : (
          <div className="space-y-4">
            {projects.map((project, index) => (
              <div key={index} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-200">{project.project_title || 'Untitled Project'}</h3>
                  <button
                    onClick={() => handleDelete(project.project_title)}
                    className="p-1 hover:bg-red-900/30 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </button>
                </div>
                <pre className="text-sm text-gray-400 whitespace-pre-wrap font-mono bg-gray-900 p-3 rounded">
                  {project.text}
                </pre>
                <div className="mt-2 text-xs text-gray-600">
                  Similarity Score: {(project.score * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}