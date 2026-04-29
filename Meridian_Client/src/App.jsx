import { Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import BoardPage from './pages/BoardPage'
import LoginPage from './pages/LoginPage'
import MyTasksPage from './pages/MyTasksPage'
import ProjectsPage from './pages/ProjectsPage'
import RegisterPage from './pages/RegisterPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<ProjectsPage />} />
        <Route path="/board" element={<BoardPage />} />
        <Route path="/my-tasks" element={<MyTasksPage />} />
      </Route>
    </Routes>
  )
}
