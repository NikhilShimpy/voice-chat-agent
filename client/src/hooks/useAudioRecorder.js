import { useState, useRef, useCallback } from 'react'

export const useAudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef(null)
  const audioContextRef = useRef(null)
  const streamRef = useRef(null)
  const processorRef = useRef(null)

  const startRecording = useCallback(async (onAudioData) => {
    try {
      console.log('Requesting microphone access...')
      
      // Get microphone access with optimal settings for ASR
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })
      
      streamRef.current = stream
      
      // Set up AudioContext for processing
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      })
      
      const source = audioContextRef.current.createMediaStreamSource(stream)
      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1)
      
      processor.onaudioprocess = (event) => {
        if (!isRecording) return
        
        const inputData = event.inputBuffer.getChannelData(0)
        // Convert Float32 to PCM16
        const pcmData = convertFloat32ToPCM16(inputData)
        
        // Send audio data to callback
        if (onAudioData) {
          onAudioData(pcmData)
        }
      }
      
      source.connect(processor)
      processor.connect(audioContextRef.current.destination)
      processorRef.current = processor
      
      setIsRecording(true)
      console.log('Audio recording started successfully')
      
    } catch (error) {
      console.error('Error starting recording:', error)
      if (error.name === 'NotAllowedError') {
        throw new Error('Microphone access denied. Please allow microphone permissions.')
      } else if (error.name === 'NotFoundError') {
        throw new Error('No microphone found. Please check your audio devices.')
      } else {
        throw new Error(`Failed to start recording: ${error.message}`)
      }
    }
  }, [isRecording])

  const stopRecording = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    setIsRecording(false)
    console.log('Audio recording stopped')
  }, [])

  const convertFloat32ToPCM16 = (float32Array) => {
    const pcm16 = new Int16Array(float32Array.length)
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]))
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
    }
    return pcm16
  }

  return {
    startRecording,
    stopRecording,
    isRecording
  }
}