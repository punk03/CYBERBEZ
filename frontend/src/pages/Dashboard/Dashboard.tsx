import { useQuery } from '@tanstack/react-query'
import { threatsApi } from '../../api/threats'
import { automationApi } from '../../api/automation'
import { useTranslation } from 'react-i18next'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './Dashboard.css'

const Dashboard = () => {
  const { t } = useTranslation()

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['threats-summary'],
    queryFn: () => threatsApi.getSummary(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: automationStatus, isLoading: automationLoading } = useQuery({
    queryKey: ['automation-status'],
    queryFn: () => automationApi.getStatus(),
    refetchInterval: 30000,
  })

  const { data: recentThreats } = useQuery({
    queryKey: ['recent-threats'],
    queryFn: () => threatsApi.getThreats({ limit: 10 }),
    refetchInterval: 30000,
  })

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8']

  const attackTypeData = summary
    ? Object.entries(summary.attack_types).map(([name, value]) => ({
        name,
        value,
      }))
    : []

  const severityData = summary
    ? Object.entries(summary.severities).map(([name, value]) => ({
        name,
        value,
      }))
    : []

  if (summaryLoading || automationLoading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card">
          <h3>{t('dashboard.total_threats')}</h3>
          <p className="stat-value">{summary?.total_threats || 0}</p>
        </div>
        <div className="stat-card">
          <h3>{t('dashboard.automation_executed')}</h3>
          <p className="stat-value">{summary?.automation_executed || 0}</p>
        </div>
        <div className="stat-card">
          <h3>{t('dashboard.quarantined_devices')}</h3>
          <p className="stat-value">{automationStatus?.quarantined_devices || 0}</p>
        </div>
        <div className="stat-card">
          <h3>{t('dashboard.pending_approvals')}</h3>
          <p className="stat-value">{automationStatus?.pending_approvals || 0}</p>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>{t('dashboard.attack_types')}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={attackTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {attackTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>{t('dashboard.severity_distribution')}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={severityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="recent-threats">
        <h3>{t('dashboard.recent_threats')}</h3>
        <table className="threats-table">
          <thead>
            <tr>
              <th>{t('dashboard.time')}</th>
              <th>{t('dashboard.attack_type')}</th>
              <th>{t('dashboard.severity')}</th>
              <th>{t('dashboard.source_ip')}</th>
              <th>{t('dashboard.confidence')}</th>
            </tr>
          </thead>
          <tbody>
            {recentThreats?.threats.slice(0, 10).map((threat) => (
              <tr key={threat.threat_id}>
                <td>{new Date(threat.timestamp).toLocaleString()}</td>
                <td>{threat.attack_type}</td>
                <td>
                  <span className={`severity-badge severity-${threat.severity}`}>
                    {threat.severity}
                  </span>
                </td>
                <td>{threat.source_ip || '-'}</td>
                <td>{(threat.confidence * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Dashboard
