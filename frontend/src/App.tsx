import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./features/auth/AuthProvider";
import { useAuth } from "./features/auth/useAuth";
import { AppLayout } from "./components/layout/AppLayout";
import { OffloadPage } from "./features/offload/OffloadPage";
import { ShippingPage } from "./features/shipping/ShippingPage";
import { COAPage } from "./features/coa/COAPage";
import { DailyMLPage } from "./features/daily-analysis/DailyMLPage";
import { DailyMSLPage } from "./features/daily-analysis/DailyMSLPage";
import { DailyAttributePage } from "./features/daily-analysis/DailyAttributePage";
import { RiskPage } from "./features/risk/RiskPage";
import { DataManagementPage } from "./features/data-mgmt/DataManagementPage";
import { AdminPage } from "./features/admin/AdminPage";
import { LoginPage } from "./pages/LoginPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/offload" replace />} />
        <Route path="/offload" element={<OffloadPage />} />
        <Route path="/shipping" element={<ShippingPage />} />
        <Route path="/coa" element={<COAPage />} />
        <Route path="/analysis/ml" element={<DailyMLPage />} />
        <Route path="/analysis/msl" element={<DailyMSLPage />} />
        <Route path="/analysis/attribute" element={<DailyAttributePage />} />
        <Route path="/risk" element={<RiskPage />} />
        <Route path="/data-management" element={<DataManagementPage />} />
        <Route path="/admin/users" element={<AdminPage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
