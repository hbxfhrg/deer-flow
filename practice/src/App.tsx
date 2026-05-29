import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { HomePage, ChatPage, StartPage, ScenePage, CoursePage, ProfilePage, ResultPage, LoginPage } from './pages';
import { api } from './api';
import './index.css';

// 认证保护路由
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  if (!api.auth.isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// 已登录时重定向到首页
const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  if (api.auth.isLoggedIn()) {
    return <Navigate to="/" replace />;
  }
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <div className="h-screen w-full">
        <Routes>
          {/* 登录页面 - 公共路由 */}
          <Route 
            path="/login" 
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            } 
          />

          {/* 首页 - 需要登录 */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            } 
          />

          {/* 开始页面 */}
          <Route 
            path="/start" 
            element={
              <ProtectedRoute>
                <StartPage />
              </ProtectedRoute>
            } 
          />

          {/* 场景页面 */}
          <Route 
            path="/scene" 
            element={
              <ProtectedRoute>
                <ScenePage />
              </ProtectedRoute>
            } 
          />

          {/* 课程页面 */}
          <Route 
            path="/course" 
            element={
              <ProtectedRoute>
                <CoursePage />
              </ProtectedRoute>
            } 
          />

          {/* 聊天页面 */}
          <Route 
            path="/chat" 
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            } 
          />

          {/* 结果页面 */}
          <Route 
            path="/result/:id" 
            element={
              <ProtectedRoute>
                <ResultPage />
              </ProtectedRoute>
            } 
          />

          {/* 个人中心 */}
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } 
          />

          {/* 其他路径重定向到首页 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;