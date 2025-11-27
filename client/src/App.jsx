import React, { useState, useRef, useCallback } from 'react'
import Controls from './components/Controls'
import Transcript from './components/Transcript'
import VoiceSelector from './components/VoiceSelector'
import DebugPanel from './components/DebugPanel'
import { useAudioRecorder } from './hooks/useAudioRecorder'
import { createWebSocketClient } from './utils/ws-client'
import './index.css'

function App() {
  const [transcripts, setTranscripts] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [selectedVoice, setSelectedVoice] = useState('falcon_en_us')
  const [logs, setLogs] = useState([])
  const audioContextRef = useRef(null)
  const wsClientRef = useRef(null)

  const addLog = useCallback((message) => {
    setLogs(prev => [...prev, `${new Date().toISOString()}: ${message}`])
  }, [])

  const handleTranscript = useCallback((data) => {
    setTranscripts(prev => [...prev, {
      text: data.text,
      isFinal: data.is_final,
      timestamp: new Date().toISOString(),
      speaker: 'user'
    }])
  }, [])

  const handleAudioChunk = useCallback(async (data) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
      }

      const audioData = Uint8Array.from(atob(data.payload), c => c.charCodeAt(0))
      const audioBuffer = await audioContextRef.current.decodeAudioData(audioData.buffer)
      const source = audioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContextRef.current.destination)
      source.start()
      
      // Add agent transcript when audio plays
      setTranscripts(prev => [...prev, {
        text: 'Agent response',
        isFinal: true,
        timestamp: new Date().toISOString(),
        speaker: 'agent'
      }])
    } catch (error) {
      addLog(`Audio playback error: ${error.message}`)
    }
  }, [addLog])

  const handleConnect = useCallback(() => {
    try {
      wsClientRef.current = createWebSocketClient({
        onMessage: (data) => {
          switch (data.type) {
            case 'transcript':
              handleTranscript(data)
              break
            case 'audio_chunk':
              handleAudioChunk(data)
              break
            case 'status':
              setIsRecording(data.status === 'recording')
              break
            case 'error':
              addLog(`Server error: ${data.message}`)
              break
          }
        },
        onOpen: () => {
          setIsConnected(true)
          addLog('WebSocket connected')
        },
        onClose: () => {
          setIsConnected(false)
          setIsRecording(false)
          addLog('WebSocket disconnected')
        },
        onError: (error) => {
          addLog(`WebSocket error: ${error.message}`)
        }
      })
    } catch (error) {
      addLog(`Connection error: ${error.message}`)
    }
  }, [handleTranscript, handleAudioChunk, addLog])

  const handleDisconnect = useCallback(() => {
    if (wsClientRef.current) {
      wsClientRef.current.close()
      wsClientRef.current = null
    }
  }, [])

  const handleStartRecording = useCallback(() => {
    if (wsClientRef.current && isConnected) {
      wsClientRef.current.sendConfig(selectedVoice, 'en-US')
      wsClientRef.current.start()
      addLog('Started recording')
    }
  }, [isConnected, selectedVoice, addLog])

  const handleStopRecording = useCallback(() => {
    if (wsClientRef.current && isConnected) {
      wsClientRef.current.stop()
      addLog('Stopped recording')
    }
  }, [isConnected, addLog])

  const { startRecording, stopRecording, isRecording: audioRecording } = useAudioRecorder({
    onAudioData: (audioData) => {
      if (wsClientRef.current && isConnected && isRecording) {
        wsClientRef.current.sendAudio(audioData)
      }
    }
  })

  const handleRecordToggle = useCallback(() => {
    if (audioRecording) {
      stopRecording()
      handleStopRecording()
    } else {
      startRecording()
      handleStartRecording()
    }
  }, [audioRecording, startRecording, stopRecording, handleStartRecording, handleStopRecording])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Voice Chat Agent</h1>
        <div className="connection-status">
          Status: <span className={isConnected ? 'connected' : 'disconnected'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </header>

      <main className="app-main">
        <div className="control-panel">
          <VoiceSelector
            selectedVoice={selectedVoice}
            onVoiceChange={setSelectedVoice}
            disabled={!isConnected}
          />
          
          <Controls
            isConnected={isConnected}
            isRecording={audioRecording}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
            onRecordToggle={handleRecordToggle}
          />
        </div>

        <Transcript transcripts={transcripts} />

        <DebugPanel logs={logs} onClearLogs={() => setLogs([])} />
      </main>
    </div>
  )
}

export default App