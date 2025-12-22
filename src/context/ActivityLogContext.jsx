import React, { createContext, useContext, useState } from 'react';

const ActivityLogContext = createContext();

export const ActivityLogProvider = ({ children }) => {
  const [logs, setLogs] = useState([]);

  const addLog = (logEntry) => {
    const newLog = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ...logEntry
    };
    setLogs(prev => [newLog, ...prev]);
    console.log('Activity Log:', newLog);
  };

  return (
    <ActivityLogContext.Provider value={{ logs, addLog }}>
      {children}
    </ActivityLogContext.Provider>
  );
};

export const useActivityLog = () => {
  const context = useContext(ActivityLogContext);
  if (!context) {
    throw new Error('useActivityLog must be used within an ActivityLogProvider');
  }
  return context;
};

export default ActivityLogContext;
