import { Navigate, Route, Routes } from 'react-router-dom';

import LandingPage from './components/LandingPage/LandingPage';
import BoardPage from './components/Board/BoardPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/board/:publicBoardId" element={<BoardPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
