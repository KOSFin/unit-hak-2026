import { Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';

import Layout from './components/Layout/Layout';

function LandingPage() {
  return <div>Landing</div>;
}

function BoardPage() {
  const { publicBoardId } = useParams();
  return <div>Board {publicBoardId}</div>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/board/:publicBoardId" element={<BoardPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
