import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { threatsApi } from '../../api/threats'
import { useTranslation } from 'react-i18next'
import './Threats.css'

const Threats = () => {
  const { t } = useTranslation()
  const [page, setPage] = useState(1)
  const [attackTypeFilter, setAttackTypeFilter] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const limit = 20

  const { data, isLoading } = useQuery({
    queryKey: ['threats', page, attackTypeFilter, severityFilter],
    queryFn: () =>
      threatsApi.getThreats({
        limit,
        skip: (page - 1) * limit,
        attack_type: attackTypeFilter || undefined,
        severity: severityFilter || undefined,
      }),
    refetchInterval: 30000,
  })

  if (isLoading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="threats-page">
      <div className="filters">
        <select
          value={attackTypeFilter}
          onChange={(e) => {
            setAttackTypeFilter(e.target.value)
            setPage(1)
          }}
        >
          <option value="">{t('threats.all_attack_types')}</option>
          <option value="ddos">DDoS</option>
          <option value="malware">Malware</option>
          <option value="scada_attack">SCADA Attack</option>
          <option value="insider_threat">Insider Threat</option>
          <option value="network_intrusion">Network Intrusion</option>
          <option value="apt">APT</option>
          <option value="ransomware">Ransomware</option>
          <option value="zero_day">Zero-Day</option>
        </select>

        <select
          value={severityFilter}
          onChange={(e) => {
            setSeverityFilter(e.target.value)
            setPage(1)
          }}
        >
          <option value="">{t('threats.all_severities')}</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <div className="threats-list">
        {data?.threats.map((threat) => (
          <div key={threat.threat_id} className="threat-card">
            <div className="threat-header">
              <h3>{threat.attack_type}</h3>
              <span className={`severity-badge severity-${threat.severity}`}>
                {threat.severity}
              </span>
            </div>
            <div className="threat-details">
              <p>
                <strong>{t('threats.source_ip')}:</strong> {threat.source_ip || '-'}
              </p>
              <p>
                <strong>{t('threats.confidence')}:</strong>{' '}
                {(threat.confidence * 100).toFixed(1)}%
              </p>
              <p>
                <strong>{t('threats.timestamp')}:</strong>{' '}
                {new Date(threat.timestamp).toLocaleString()}
              </p>
              {threat.automation_status?.success && (
                <p className="automation-success">
                  ✓ {t('threats.automation_executed')}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="pagination">
        <button
          disabled={page === 1}
          onClick={() => setPage(page - 1)}
        >
          {t('common.previous')}
        </button>
        <span>
          {t('common.page')} {page} {t('common.of')} {Math.ceil((data?.total || 0) / limit)}
        </span>
        <button
          disabled={!data || page * limit >= data.total}
          onClick={() => setPage(page + 1)}
        >
          {t('common.next')}
        </button>
      </div>
    </div>
  )
}

export default Threats
