import apiClient from './client'

export interface LogEntry {
  _id: string
  timestamp: string
  source: string
  host: string
  service: string
  level: string
  message: string
  raw: string
  metadata: Record<string, any>
}

export interface LogsResponse {
  logs: LogEntry[]
  total: number
  limit: number
  skip: number
}

export const logsApi = {
  getLogs: async (params?: {
    limit?: number
    skip?: number
    source?: string
  }): Promise<LogsResponse> => {
    const response = await apiClient.get('/logs', { params })
    return response.data
  },

  sendLog: async (log: {
    log: string
    source?: string
    format?: string
    metadata?: Record<string, any>
  }): Promise<{ success: boolean; message: string; log_id?: string }> => {
    const response = await apiClient.post('/logs', log)
    return response.data
  },
}
