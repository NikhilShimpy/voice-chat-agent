import React from 'react'

const VOICES = [
  { id: 'falcon_en_us', name: 'Falcon (US English)' },
  { id: 'falcon_en_uk', name: 'Falcon (UK English)' },
  { id: 'falcon_en_au', name: 'Falcon (Australian English)' }
]

const VoiceSelector = ({ selectedVoice, onVoiceChange, disabled }) => {
  return (
    <div className="voice-selector">
      <label htmlFor="voice-select">Select Voice:</label>
      <select
        id="voice-select"
        value={selectedVoice}
        onChange={(e) => onVoiceChange(e.target.value)}
        disabled={disabled}
      >
        {VOICES.map(voice => (
          <option key={voice.id} value={voice.id}>
            {voice.name}
          </option>
        ))}
      </select>
    </div>
  )
}

export default VoiceSelector