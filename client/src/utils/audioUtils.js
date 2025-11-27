export const playAudioChunk = async (base64Data, audioContext) => {
  try {
    const audioData = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0))
    const audioBuffer = await audioContext.decodeAudioData(audioData.buffer)
    const source = audioContext.createBufferSource()
    source.buffer = audioBuffer
    source.connect(audioContext.destination)
    source.start()
  } catch (error) {
    console.error('Error playing audio:', error)
  }
}