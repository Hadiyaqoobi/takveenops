import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getProjects } from '../api';

const ProjectContext = createContext(null);

export function ProjectProvider({ children }) {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(
    () => localStorage.getItem('takvenops_project') || 'default'
  );

  const loadProjects = useCallback(async () => {
    try {
      const list = await getProjects();
      setProjects(list);
      if (list.length > 0 && !list.find(p => p.id === currentProject)) {
        setCurrentProject(list[0].id);
      }
    } catch (e) {
      // Not logged in yet or server down — ignore
    }
  }, [currentProject]);

  useEffect(() => { loadProjects(); }, []);

  const selectProject = useCallback((projectId) => {
    localStorage.setItem('takvenops_project', projectId);
    setCurrentProject(projectId);
  }, []);

  const currentProjectData = projects.find(p => p.id === currentProject) || null;

  return (
    <ProjectContext.Provider value={{ projects, currentProject, currentProjectData, selectProject, loadProjects }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error('useProject must be used within ProjectProvider');
  return ctx;
}
