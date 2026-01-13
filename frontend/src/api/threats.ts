import apiClient from './client'

export interface Threat {
  threat_id: string
  attack_type: string
  severity: string
  confidence: number
  source_ip?: string
  timestamp: string
  detection_details: Record<string, any>
  automation_status?: Record<string, any>
}

export interface ThreatsResponse {
  threats: Threat[]
  total: number
  limit: number
  skip: number
}

export interface ThreatsSummary {
  total_threats: number
  attack_types: Record<string, number>
  severities: Record<string, number>
  automation_executed: number
  automation_rate: number
}

export const threatsApi = {
  getThreats: async (params?: {
    limit?: number
    skip?: number
    attack_type?: string
    severity?: string
  }): Promise<ThreatsResponse> => {
    const response = await apiClient.get('/threats', { params })
    return response.data
  },

  getThreat: async (threatId: string): Promise<Threat> => {
    const response = await apiClient.get(`/threats/${threatId}`)
    return response.data
  },

  getSummary: async (): Promise<ThreatsSummary> => {
    const response = await apiClient.get('/threats/stats/summary')
    return response.data
  },
}
