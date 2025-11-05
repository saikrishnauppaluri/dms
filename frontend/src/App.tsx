import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Missions from './pages/Missions'
import Drones from './pages/Drones'
import Events from './pages/Events'
import Scenarios from './pages/Scenarios'
import Layout from './components/Layout'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/missions" element={<Missions />} />
        <Route path="/drones" element={<Drones />} />
        <Route path="/events" element={<Events />} />
        <Route path="/scenarios" element={<Scenarios />} />
      </Routes>
    </Layout>
  )
}

export default App
