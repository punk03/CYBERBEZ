import { useTranslation } from 'react-i18next'
import './Settings.css'

const Settings = () => {
  const { t } = useTranslation()

  return (
    <div className="settings-page">
      <h2>{t('settings.title')}</h2>
      <p>{t('settings.coming_soon')}</p>
    </div>
  )
}

export default Settings
