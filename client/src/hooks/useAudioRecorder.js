import { useState, useRef, useCallback } from 'react'

export const useAudioRecorder = ({ onAudioData }) => {
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef(null)
  const audioContextRef = useRef(null)
  const streamRef = useRef(null)

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      })
      
      streamRef.current = stream
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
        onAudioData(pcmData)
      }
      
      source.connect(processor)
      processor.connect(audioContextRef.current.destination)
      
      setIsRecording(true)
    } catch (error) {
      console.error('Error starting recording:', error)
      throw error
    }
  }, [isRecording, onAudioData])

  const stopRecording = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }
    setIsRecording(false)
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