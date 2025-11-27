export class WebSocketClient {
  constructor(url, callbacks) {
    this.url = url
    this.callbacks = callbacks
    this.ws = null
    this.isConnected = false
  }

  connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)
        
        this.ws.onopen = () => {
          this.isConnected = true
          this.callbacks.onOpen?.()
          resolve()
        }
        
        this.ws.onclose = () => {
          this.isConnected = false
          this.callbacks.onClose?.()
        }
        
        this.ws.onerror = (error) => {
          this.callbacks.onError?.(error)
          reject(error)
        }
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.callbacks.onMessage?.(data)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  sendAudio(audioData) {
    if (this.ws && this.isConnected) {
      this.ws.send(audioData)
    }
  }

  sendConfig(voice, lang) {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify({
        type: 'config',
        voice: voice,
        lang: lang
      }))
    }
  }

  start() {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify({ type: 'start' }))
    }
  }

  stop() {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify({ type: 'stop' }))
    }
  }

  close() {
    if (this.ws) {
      this.ws.close()
    }
  }
}

export const createWebSocketClient = (callbacks) => {
  const url = import.meta.env.VITE_BACKEND_WS_URL
  const client = new WebSocketClient(url, callbacks)
  client.connect()
  return client
}