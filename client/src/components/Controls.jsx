import React from 'react'

const Controls = ({ 
  isConnected, 
  isRecording, 
  onConnect, 
  onDisconnect, 
  onRecordToggle 
}) => {
  return (
    <div className="controls">
      {!isConnected ? (
        <button 
          className="btn btn-connect"
          onClick={onConnect}
        >
          Connect
        </button>
      ) : (
        <button 
          className="btn btn-disconnect"
          onClick={onDisconnect}
        >
          Disconnect
        </button>
      )}
      
      <button
        className={`btn btn-record ${isRecording ? 'recording' : ''}`}
        onClick={onRecordToggle}
        disabled={!isConnected}
      >
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>
      
      <div className={`recording-indicator ${isRecording ? 'active' : ''}`}>
        ● Recording
      </div>
    </div>
  )
}

export default Controls