import { FolderGit2, CheckCircle2, Circle } from 'lucide-react';

export default function ProjectSelector({ projects, selectedProjects, onToggleProject }) {
  if (!projects || projects.length === 0) return null;

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <FolderGit2 className="w-5 h-5 mr-2 text-green-400" />
        Select Projects to Enhance
      </h2>
      
      <p className="text-sm text-gray-500 mb-4">
        Choose up to 3 projects to receive AI-enhanced descriptions
      </p>
      
      <div className="space-y-3">
        {projects.map((project, index) => {
          const isSelected = selectedProjects.includes(project.title);
          const isDisabled = !isSelected && selectedProjects.length >= 3;
          
          return (
            <button
              key={index}
              onClick={() => !isDisabled && onToggleProject(project.title)}
              disabled={isDisabled}
              className={`w-full text-left p-4 rounded-lg border transition-all ${
                isSelected
                  ? 'bg-blue-900/20 border-blue-600'
                  : isDisabled
                  ? 'bg-gray-800/50 border-gray-800 opacity-50 cursor-not-allowed'
                  : 'bg-gray-800 border-gray-700 hover:border-gray-600'
              }`}
            >
              <div className="flex items-start space-x-3">
                {isSelected ? (
                  <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <Circle className="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" />
                )}
                
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-200 mb-1">{project.title}</h3>
                  <p className="text-sm text-gray-400 line-clamp-2 mb-2">
                    {project.description}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {project.technologies.slice(0, 5).map((tech, i) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded"
                      >
                        {tech}
                      </span>
                    ))}
                    {project.technologies.length > 5 && (
                      <span className="text-xs px-2 py-1 text-gray-500">
                        +{project.technologies.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}