import { Loader2 } from 'lucide-react';

export default function LoadingState({ message = "Analyzing your resume..." }) {
  return (
    <div className="card flex flex-col items-center justify-center py-16">
      <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
      <p className="text-lg font-medium text-gray-300">{message}</p>
      <p className="text-sm text-gray-500 mt-2">This may take a few moments</p>
      
      <div className="mt-8 space-y-2 text-sm text-gray-600">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          <span>Parsing resume structure...</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-75"></div>
          <span>Analyzing job alignment...</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-150"></div>
          <span>Ranking projects by relevance...</span>
        </div>
      </div>
    </div>
  );
}