import { useState, useEffect } from 'react';
import { Lock, Eye, EyeOff, LogOut } from 'lucide-react';

export default function WorkspaceManager({ onWorkspaceChange }) {
  const [workspacePassword, setWorkspacePassword] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Check localStorage for existing workspace
    const stored = localStorage.getItem('alignai_workspace_password');
    if (stored) {
      setWorkspacePassword(stored);
      setIsLoggedIn(true);
      onWorkspaceChange(stored);
    }
  }, []);

  const handleLogin = () => {
    if (inputValue.trim().length < 4) {
      alert('Workspace password must be at least 4 characters');
      return;
    }

    const password = inputValue.trim();
    setWorkspacePassword(password);
    localStorage.setItem('alignai_workspace_password', password);
    onWorkspaceChange(password);
    setIsLoggedIn(true);
    setInputValue('');
  };

  const handleLogout = () => {
    if (confirm('Log out of this workspace? Your projects will remain safe.')) {
      setWorkspacePassword('');
      setIsLoggedIn(false);
      localStorage.removeItem('alignai_workspace_password');
      onWorkspaceChange('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLogin();
    }
  };

  if (isLoggedIn) {
    return (
      <div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 border border-purple-700/50 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-purple-600 p-2 rounded-lg">
              <Lock className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Workspace Active</p>
              <div className="flex items-center space-x-2">
                <code className="text-sm font-mono text-purple-300">
                  {showPassword ? workspacePassword : '•'.repeat(workspacePassword.length)}
                </code>
                <button
                  onClick={() => setShowPassword(!showPassword)}
                  className="p-1 hover:bg-purple-800/30 rounded transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4 text-gray-400" />
                  ) : (
                    <Eye className="w-4 h-4 text-gray-400" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center space-x-2 text-sm px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Switch Workspace</span>
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          💡 Your projects are stored securely under this workspace password
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
      <div className="max-w-md mx-auto text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-purple-600 rounded-full mb-4">
          <Lock className="w-6 h-6 text-white" />
        </div>
        
        <h3 className="text-xl font-semibold mb-2">Enter Workspace Password</h3>
        <p className="text-sm text-gray-400 mb-6">
          Create or enter your workspace password to access your projects
        </p>

        <div className="space-y-4">
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter workspace password (min 4 characters)"
              className="input-field pr-12"
              autoFocus
            />
            <button
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-700 rounded transition-colors"
            >
              {showPassword ? (
                <EyeOff className="w-5 h-5 text-gray-400" />
              ) : (
                <Eye className="w-5 h-5 text-gray-400" />
              )}
            </button>
          </div>

          <button
            onClick={handleLogin}
            disabled={inputValue.trim().length < 4}
            className="btn-primary w-full"
          >
            Access Workspace
          </button>
        </div>

        <div className="mt-6 p-4 bg-blue-900/20 border border-blue-800 rounded-lg text-left">
          <p className="text-xs text-blue-300 mb-2">
            <strong>How it works:</strong>
          </p>
          <ul className="text-xs text-gray-400 space-y-1">
            <li>• Your password acts as your unique workspace ID</li>
            <li>• All your projects are stored under this password</li>
            <li>• Use the same password on any device to access your data</li>
            <li>• No account needed - just remember your password!</li>
          </ul>
        </div>
      </div>
    </div>
  );
}