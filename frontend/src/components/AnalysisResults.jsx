import { 
  TrendingUp, Target, MessageSquare, Tag, 
  AlertCircle, Lightbulb, Star, Award 
} from 'lucide-react';

export default function AnalysisResults({ results }) {
  const getScoreColor = (score) => {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'bg-red-900/30 text-red-400 border-red-800',
      medium: 'bg-yellow-900/30 text-yellow-400 border-yellow-800',
      low: 'bg-blue-900/30 text-blue-400 border-blue-800',
    };
    return colors[priority] || colors.low;
  };

  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <div className="card bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-800">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold flex items-center">
            <Award className="w-6 h-6 mr-2 text-blue-400" />
            Overall Score
          </h2>
          <div className={`score-badge ${getScoreColor(results.overall_score)} text-2xl font-bold px-6 py-2`}>
            {results.overall_score}/100
          </div>
        </div>
        <p className="text-gray-300">{results.professional_feedback}</p>
      </div>

      {/* Category Scores */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Target className="w-5 h-5 mr-2 text-green-400" />
          Detailed Breakdown
        </h2>
        
        <div className="space-y-4">
          {results.category_scores.map((category, index) => (
            <div key={index} className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-200 capitalize">
                  {category.category.replace('_', ' ')}
                </h3>
                <span className={`score-badge ${getScoreColor(category.score)}`}>
                  {category.score}/100
                </span>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                <div
                  className={`h-2 rounded-full ${
                    category.score >= 80 ? 'bg-green-500' :
                    category.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${category.score}%` }}
                />
              </div>
              
              <p className="text-sm text-gray-400">{category.feedback}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ATS Keywords */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Tag className="w-5 h-5 mr-2 text-yellow-400" />
          ATS Keyword Analysis
        </h2>
        
        <div className="space-y-4">
          {/* Matched Keywords */}
          {results.ats_keywords.matched.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-green-400 mb-2 flex items-center">
                <Target className="w-4 h-4 mr-1" />
                Matched Keywords ({results.ats_keywords.matched.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {results.ats_keywords.matched.map((keyword, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-green-900/30 text-green-400 border border-green-800 rounded-full text-sm"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Missing Keywords */}
          {results.missing_keywords.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-red-400 mb-2 flex items-center">
                <AlertCircle className="w-4 h-4 mr-1" />
                Missing Keywords
              </h3>
              <div className="space-y-2">
                {results.missing_keywords.map((item, i) => (
                  <div
                    key={i}
                    className="bg-gray-800 border border-gray-700 rounded-lg p-3"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-200">{item.keyword}</span>
                      <span className={`text-xs px-2 py-1 rounded border ${getPriorityColor(item.priority)}`}>
                        {item.priority}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">{item.context}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recommended Projects */}
      {results.recommended_projects.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Star className="w-5 h-5 mr-2 text-purple-400" />
            Top Recommended Projects
          </h2>
          
          <p className="text-sm text-gray-400 mb-4">
            These projects best match the job requirements based on AI analysis:
          </p>
          
          <div className="space-y-2">
            {results.recommended_projects.map((project, i) => (
              <div
                key={i}
                className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-800/50 rounded-lg p-4"
              >
                <div className="flex items-center space-x-3">
                  <span className="flex items-center justify-center w-8 h-8 bg-purple-600 text-white font-bold rounded-full">
                    {i + 1}
                  </span>
                  <span className="font-medium text-gray-200">{project}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Enhanced Descriptions */}
      {results.enhanced_descriptions && results.enhanced_descriptions.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Lightbulb className="w-5 h-5 mr-2 text-yellow-400" />
            Enhanced Project Descriptions
          </h2>
          
          <div className="space-y-6">
            {results.enhanced_descriptions.map((desc, i) => (
              <div key={i} className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-medium text-gray-200 mb-3">Enhancement {i + 1}</h3>
                
                {/* Original */}
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-1">Original:</p>
                  <p className="text-sm text-gray-400 bg-gray-900/50 p-3 rounded border border-gray-700">
                    {desc.original}
                  </p>
                </div>
                
                {/* Enhanced */}
                <div className="mb-4">
                  <p className="text-xs text-green-500 mb-1">Enhanced:</p>
                  <p className="text-sm text-gray-200 bg-green-900/10 p-3 rounded border border-green-800">
                    {desc.enhanced}
                  </p>
                </div>
                
                {/* Improvements */}
                <div>
                  <p className="text-xs text-blue-400 mb-2">Improvements:</p>
                  <ul className="space-y-1">
                    {desc.improvements.map((improvement, j) => (
                      <li key={j} className="text-sm text-gray-400 flex items-start">
                        <span className="text-blue-400 mr-2">•</span>
                        {improvement}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ranked Projects */}
      {results.projects.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-blue-400" />
            All Projects by Relevance
          </h2>
          
          <div className="space-y-3">
            {results.projects.map((project, i) => (
              <div
                key={i}
                className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-200">{project.title}</h3>
                  {project.relevance_score && (
                    <span className={`score-badge ${getScoreColor(project.relevance_score)}`}>
                      {project.relevance_score.toFixed(0)}%
                    </span>
                  )}
                </div>
                
                <p className="text-sm text-gray-400 mb-3">{project.description}</p>
                
                <div className="flex flex-wrap gap-1">
                  {project.technologies.map((tech, j) => (
                    <span
                      key={j}
                      className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}