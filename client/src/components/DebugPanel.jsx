import React from 'react'

const DebugPanel = ({ logs, onClearLogs }) => {
  return (
    <div className="debug-panel">
      <div className="debug-header">
        <h3>Debug Logs</h3>
        <button className="btn btn-clear" onClick={onClearLogs}>
          Clear
        </button>
      </div>
      <div className="debug-content">
        {logs.map((log, index) => (
          <div key={index} className="log-entry">
            {log}
          </div>
        ))}
        {logs.length === 0 && (
          <div className="no-logs">No logs yet</div>
        )}
      </div>
    </div>
  )
}

export default DebugPanel