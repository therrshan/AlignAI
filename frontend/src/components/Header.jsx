import { Sparkles, Cpu } from 'lucide-react';
import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Header() {
  const [llmProvider, setLlmProvider] = useState('groq');
  const [isChanging, setIsChanging] = useState(false);

  useEffect(() => {
    // Fetch current provider on mount
    axios.get(`${API_URL}/api/llm-provider`)
      .then(res => setLlmProvider(res.data.provider))
      .catch(err => console.error('Failed to fetch LLM provider:', err));
  }, []);

  const toggleProvider = async () => {
    const newProvider = llmProvider === 'groq' ? 'ollama' : 'groq';
    setIsChanging(true);
    
    try {
      const formData = new FormData();
      formData.append('provider', newProvider);
      
      await axios.post(`${API_URL}/api/llm-provider`, formData);
      setLlmProvider(newProvider);
    } catch (err) {
      console.error('Failed to change provider:', err);
      alert('Failed to change LLM provider');
    } finally {
      setIsChanging(false);
    }
  };

  return (
    <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                AlignAI
              </h1>
              <p className="text-xs text-gray-500">Intelligent Resume Optimization</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-400">
            {/* LLM Provider Toggle */}
            <button
              onClick={toggleProvider}
              disabled={isChanging}
              className="flex items-center space-x-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              title="Switch LLM Provider"
            >
              <Cpu className="w-4 h-4" />
              <span className="text-xs font-mono">
                {isChanging ? '...' : llmProvider}
              </span>
            </button>
            
            <span className="px-2 py-1 bg-gray-800 rounded text-xs font-mono">v1.0.0</span>
            <div className="h-4 w-px bg-gray-700"></div>
            <a 
              href="https://github.com/yourusername/alignai" 
              target="_blank" 
              rel="noopener noreferrer"
              className="hover:text-gray-200 transition-colors"
            >
              Docs
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}