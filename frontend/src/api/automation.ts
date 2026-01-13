import apiClient from './client'

export interface AutomationStatus {
  circuit_breakers: Record<string, any>
  quarantined_devices: number
  blocked_traffic: number
  pending_approvals: number
}

export interface Approval {
  id: string
  action: string
  action_params: Record<string, any>
  reason: string
  severity: string
  status: string
  created_at: string
  expires_at: string
}

export const automationApi = {
  executeAutomation: async (detection: Record<string, any>, autoApprove = false) => {
    const response = await apiClient.post('/automation/execute', {
      detection,
      auto_approve: autoApprove,
    })
    return response.data
  },

  getPendingApprovals: async (): Promise<{ approvals: Approval[]; count: number }> => {
    const response = await apiClient.get('/automation/approvals')
    return response.data
  },

  approveAction: async (approvalId: string, approver: string, comment?: string) => {
    const response = await apiClient.post(`/automation/approvals/${approvalId}/approve`, {
      approval_id: approvalId,
      approver,
      comment,
    })
    return response.data
  },

  rejectAction: async (approvalId: string, rejector: string, reason?: string) => {
    const response = await apiClient.post(`/automation/approvals/${approvalId}/reject`, {
      approval_id: approvalId,
      approver: rejector,
      comment: reason,
    })
    return response.data
  },

  getStatus: async (): Promise<AutomationStatus> => {
    const response = await apiClient.get('/automation/status')
    return response.data
  },
}
