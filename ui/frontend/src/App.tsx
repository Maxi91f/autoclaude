import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import TaskList from './components/TaskList'
import Whiteboard from './components/Whiteboard'
import History from './components/History'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="tasks" element={<TaskList />} />
        <Route path="whiteboard" element={<Whiteboard />} />
        <Route path="history" element={<History />} />
      </Route>
    </Routes>
  )
}

export default App
