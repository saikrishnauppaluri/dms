type MessageHandler = (data: any) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private handlers: Map<string, MessageHandler[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000

  connect() {
    const wsUrl = import.meta.env.VITE_WS_URL ||
      `ws://${window.location.hostname}:${window.location.port}/ws`

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.attemptReconnect()
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      setTimeout(() => this.connect(), this.reconnectDelay)
    }
  }

  private handleMessage(message: any) {
    const { type, data } = message

    const handlers = this.handlers.get(type)
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }

    // Also trigger 'all' handlers
    const allHandlers = this.handlers.get('all')
    if (allHandlers) {
      allHandlers.forEach(handler => handler(message))
    }
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, [])
    }
    this.handlers.get(type)!.push(handler)
  }

  off(type: string, handler: MessageHandler) {
    const handlers = this.handlers.get(type)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  send(type: string, data?: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }))
    }
  }
}

export const wsService = new WebSocketService()
export default wsService
