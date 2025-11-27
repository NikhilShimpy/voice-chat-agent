import React, { useEffect, useRef } from 'react'

const Transcript = ({ transcripts }) => {
  const transcriptEndRef = useRef(null)

  const scrollToBottom = () => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [transcripts])

  return (
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
            {!transcript.isFinal && <span className="typing-indicator">...</span>}
          </div>
        ))}
        <div ref={transcriptEndRef} />
      </div>
    </div>
  )
}

export default Transcript