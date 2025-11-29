import React, { useState, useRef, useCallback, useEffect } from 'react'
import './index.css'
import { useAudioRecorder } from './hooks/useAudioRecorder'

function App() {
  const [isConnected, setIsConnected] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [transcripts, setTranscripts] = useState([])
  const [logs, setLogs] = useState([])
  const [selectedVoice, setSelectedVoice] = useState('en_us_001')
  const [availableVoices, setAvailableVoices] = useState([])
  const [capabilities, setCapabilities] = useState({})
  const wsRef = useRef(null)
  const audioContextRef = useRef(null)

  const addLog = useCallback((message) => {
    console.log(message)
    setLogs(prev => [...prev.slice(-20), `${new Date().toLocaleTimeString()}: ${message}`])
  }, [])

  const addTranscript = useCallback((text, speaker = 'user', isFinal = true) => {
    setTranscripts(prev => [...prev, {
      text,
      speaker,
      isFinal,
      timestamp: new Date().toLocaleTimeString()
    }])
  }, [])

  // Real audio recorder hook
  const { startRecording: startAudioRecording, stopRecording: stopAudioRecording, isRecording: audioRecording } = useAudioRecorder()

  // Handle audio data from microphone
  const handleAudioData = useCallback((audioData) => {
    if (wsRef.current && isConnected && isRecording) {
      // Send audio data as binary
      wsRef.current.send(audioData)
    }
  }, [isConnected, isRecording])

  // Initialize audio context
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  // Test backend connection
  const testBackendConnection = useCallback(async () => {
    try {
      addLog('Testing backend HTTP connection...')
      const response = await fetch('http://localhost:8000/')
      const data = await response.json()
      addLog(`✅ Backend HTTP OK: ${data.message}`)
      setCapabilities(data.features || {})
    } catch (error) {
      addLog(`❌ Backend HTTP failed: ${error.message}`)
    }
  }, [addLog])

  // Main WebSocket connection for the app
  const connectWebSocket = useCallback(() => {
    try {
      const wsUrl = import.meta.env.VITE_BACKEND_WS_URL || 'ws://localhost:8000/ws'
      addLog(`Connecting to WebSocket: ${wsUrl}`)
      
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        addLog('✅ WebSocket connected successfully!')
        setIsConnected(true)
        // Send initial configuration
        ws.send(JSON.stringify({
          type: 'config',
          voice: selectedVoice,
          lang: 'en-US'
        }))
      }
      
      ws.onmessage = async (event) => {
        try {
          // Handle JSON messages
          const data = JSON.parse(event.data)
          addLog(`Received: ${data.type}`)
          
          switch (data.type) {
            case 'transcript':
              addTranscript(data.text, data.speaker || 'user', data.is_final)
              break
              
            case 'audio_chunk':
              addLog('🎵 Received TTS audio response')
              await handleAudioChunk(data.payload)
              break
              
            case 'status':
              setIsRecording(data.status === 'recording')
              if (data.message) {
                addLog(data.message)
              }
              if (data.capabilities) {
                setCapabilities(data.capabilities)
              }
              break
              
            case 'error':
              addLog(`❌ Error: ${data.message}`)
              break
              
            default:
              addLog(`Unknown message: ${JSON.stringify(data)}`)
          }
        } catch (error) {
          addLog(`Error parsing message: ${error}`)
        }
      }
      
      ws.onclose = () => {
        addLog('❌ WebSocket disconnected')
        setIsConnected(false)
        setIsRecording(false)
      }
      
      ws.onerror = (error) => {
        addLog(`❌ WebSocket error: ${error}`)
      }
      
      wsRef.current = ws
      
    } catch (error) {
      addLog(`❌ Connection failed: ${error.message}`)
    }
  }, [addLog, addTranscript, selectedVoice])

  const handleAudioChunk = async (base64Data) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
      }

      // Convert base64 to ArrayBuffer
      const binaryString = atob(base64Data)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // Decode and play audio
      const audioBuffer = await audioContextRef.current.decodeAudioData(bytes.buffer)
      const source = audioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContextRef.current.destination)
      source.start()
      
      addLog('🔊 Playing TTS audio')
      
    } catch (error) {
      addLog(`❌ Audio playback error: ${error.message}`)
    }
  }

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const startRecording = useCallback(async () => {
    if (wsRef.current && isConnected) {
      try {
        if (!capabilities.asr) {
          addLog('❌ ASR not available - check your API keys')
          return
        }
        
        // Start audio recording
        await startAudioRecording(handleAudioData)
        // Send start message to server
        wsRef.current.send(JSON.stringify({ type: 'start' }))
        addLog('🎤 Started audio recording - speak now!')
        setIsRecording(true)
        addTranscript('Listening...', 'system', true)
      } catch (error) {
        addLog(`❌ Failed to start audio recording: ${error.message}`)
        if (error.message.includes('Permission')) {
          addLog('Please allow microphone access in your browser')
        }
      }
    }
  }, [isConnected, startAudioRecording, handleAudioData, addLog, addTranscript, capabilities.asr])

  const stopRecording = useCallback(() => {
    if (wsRef.current && isConnected) {
      stopAudioRecording()
      wsRef.current.send(JSON.stringify({ type: 'stop' }))
      addLog('⏹️ Stopped audio recording')
      setIsRecording(false)
      addTranscript('Processing...', 'system', true)
    }
  }, [isConnected, stopAudioRecording, addLog, addTranscript])

  const handleRecordToggle = useCallback(() => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }, [isRecording, startRecording, stopRecording])

  // Load available voices on component mount
  useEffect(() => {
    const loadVoices = async () => {
      try {
        const response = await fetch('http://localhost:8000/config')
        const data = await response.json()
        setAvailableVoices(data.supported_voices || [])
      } catch (error) {
        addLog(`Failed to load voices: ${error.message}`)
        // Set default voices
        setAvailableVoices([
          { id: 'en_us_001', name: 'Falcon US English', language: 'en-US' },
          { id: 'en_uk_001', name: 'Falcon UK English', language: 'en-GB' },
          { id: 'en_au_001', name: 'Falcon Australian English', language: 'en-AU' }
        ])
      }
    }
    
    loadVoices()
  }, [addLog])

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎙️ Voice Chat Agent</h1>
        <div className="connection-status">
          Status: <span className={isConnected ? 'connected' : 'disconnected'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          {audioRecording && <span style={{color: '#e74c3c', marginLeft: '10px'}}>● Live Audio</span>}
        </div>
      </header>

      <main className="app-main">
        <div className="control-panel">
          <div className="capabilities">
            <h3>Capabilities</h3>
            <div className="capability-list">
              <div className={`capability ${capabilities.asr ? 'enabled' : 'disabled'}`}>
                🎤 ASR: {capabilities.asr ? 'Enabled' : 'Disabled'}
              </div>
              <div className={`capability ${capabilities.tts ? 'enabled' : 'disabled'}`}>
                🔊 TTS: {capabilities.tts ? 'Enabled' : 'Disabled'}
              </div>
              <div className={`capability ${capabilities.llm ? 'enabled' : 'disabled'}`}>
                🤖 LLM: {capabilities.llm ? 'Enabled' : 'Disabled'}
              </div>
            </div>
          </div>

          <div className="connection-tests">
            <h3>Connection</h3>
            <button className="btn btn-test" onClick={testBackendConnection}>
              Test Backend
            </button>
            {!isConnected ? (
              <button className="btn btn-connect" onClick={connectWebSocket}>
                Connect
              </button>
            ) : (
              <button className="btn btn-disconnect" onClick={disconnectWebSocket}>
                Disconnect
              </button>
            )}
          </div>

          <div className="voice-selector">
            <label>Select Voice:</label>
            <select 
              value={selectedVoice} 
              onChange={(e) => {
                setSelectedVoice(e.target.value)
                if (wsRef.current && isConnected) {
                  wsRef.current.send(JSON.stringify({
                    type: 'config',
                    voice: e.target.value,
                    lang: 'en-US'
                  }))
                }
              }}
              disabled={!isConnected}
            >
              {availableVoices.map(voice => (
                <option key={voice.id} value={voice.id}>
                  {voice.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="controls">
            <button
              className={`btn btn-record ${isRecording ? 'recording' : ''}`}
              onClick={handleRecordToggle}
              disabled={!isConnected || !capabilities.asr}
            >
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
            
            <div className={`recording-indicator ${isRecording ? 'active' : ''}`}>
              ● {isRecording ? 'Recording Audio - Speak Now' : 'Ready to Record'}
            </div>
            
            {!capabilities.asr && (
              <div className="warning">
                ⚠️ ASR not available - check your API keys in .env file
              </div>
            )}
            {!capabilities.tts && (
              <div className="warning">
                ⚠️ TTS not available - check your Murf API key in .env file
              </div>
            )}
          </div>
        </div>

        <div className="transcript">
          <h3>Conversation</h3>
          <div className="transcript-messages">
            {transcripts.map((transcript, index) => (
              <div
                key={index}
                className={`message ${transcript.speaker} ${transcript.isFinal ? 'final' : 'partial'}`}
              >
                <span className="speaker">{transcript.speaker}:</span>
                <span className="text">{transcript.text}</span>
                <span className="time">{transcript.timestamp}</span>
              </div>
            ))}
            {transcripts.length === 0 && (
              <div className="no-messages">
                <p>No messages yet.</p>
                <p>1. Click "Connect" to establish connection</p>
                <p>2. Click "Start Recording" and speak</p>
                <p>3. Wait for agent response</p>
              </div>
            )}
          </div>
        </div>

        <div className="debug-panel">
          <div className="debug-header">
            <h3>Activity Logs</h3>
            <button className="btn btn-clear" onClick={() => setLogs([])}>
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
              <div className="no-logs">No activity yet. Connect to see logs.</div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App