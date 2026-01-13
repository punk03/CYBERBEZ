import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { automationApi } from '../../api/automation'
import { useTranslation } from 'react-i18next'
import './Automation.css'

const Automation = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['automation-status'],
    queryFn: () => automationApi.getStatus(),
    refetchInterval: 30000,
  })

  const { data: approvals, isLoading: approvalsLoading } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: () => automationApi.getPendingApprovals(),
    refetchInterval: 10000,
  })

  const approveMutation = useMutation({
    mutationFn: ({ approvalId, approver, comment }: { approvalId: string; approver: string; comment?: string }) =>
      automationApi.approveAction(approvalId, approver, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      queryClient.invalidateQueries({ queryKey: ['automation-status'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ approvalId, rejector, reason }: { approvalId: string; rejector: string; reason?: string }) =>
      automationApi.rejectAction(approvalId, rejector, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
    },
  })

  const handleApprove = (approvalId: string) => {
    approveMutation.mutate({
      approvalId,
      approver: 'admin', // In production, get from auth context
      comment: 'Approved via dashboard',
    })
  }

  const handleReject = (approvalId: string) => {
    const reason = prompt(t('automation.rejection_reason'))
    if (reason) {
      rejectMutation.mutate({
        approvalId,
        rejector: 'admin',
        reason,
      })
    }
  }

  if (statusLoading || approvalsLoading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="automation-page">
      <div className="automation-status">
        <h3>{t('automation.status')}</h3>
        <div className="status-grid">
          <div className="status-item">
            <span className="status-label">{t('automation.quarantined_devices')}:</span>
            <span className="status-value">{status?.quarantined_devices || 0}</span>
          </div>
          <div className="status-item">
            <span className="status-label">{t('automation.blocked_traffic')}:</span>
            <span className="status-value">{status?.blocked_traffic || 0}</span>
          </div>
          <div className="status-item">
            <span className="status-label">{t('automation.pending_approvals')}:</span>
            <span className="status-value">{status?.pending_approvals || 0}</span>
          </div>
        </div>
      </div>

      <div className="pending-approvals">
        <h3>{t('automation.pending_approvals')}</h3>
        {approvals?.approvals.length === 0 ? (
          <p className="no-approvals">{t('automation.no_pending_approvals')}</p>
        ) : (
          <div className="approvals-list">
            {approvals?.approvals.map((approval) => (
              <div key={approval.id} className="approval-card">
                <div className="approval-header">
                  <h4>{approval.action}</h4>
                  <span className={`severity-badge severity-${approval.severity}`}>
                    {approval.severity}
                  </span>
                </div>
                <p className="approval-reason">{approval.reason}</p>
                <p className="approval-time">
                  {t('automation.created_at')}: {new Date(approval.created_at).toLocaleString()}
                </p>
                <div className="approval-actions">
                  <button
                    className="btn-approve"
                    onClick={() => handleApprove(approval.id)}
                    disabled={approveMutation.isPending}
                  >
                    {t('automation.approve')}
                  </button>
                  <button
                    className="btn-reject"
                    onClick={() => handleReject(approval.id)}
                    disabled={rejectMutation.isPending}
                  >
                    {t('automation.reject')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Automation
