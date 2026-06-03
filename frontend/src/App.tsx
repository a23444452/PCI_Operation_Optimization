import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { msalConfig } from "./lib/msal-config";
import { AuthProvider } from "./features/auth/AuthProvider";
import { ProtectedRoute } from "./features/auth/ProtectedRoute";
import { AppLayout } from "./components/layout/AppLayout";
import { OffloadPage } from "./features/offload/OffloadPage";
import { ShippingPage } from "./features/shipping/ShippingPage";
import { COAPage } from "./features/coa/COAPage";
import { DailyMLPage } from "./features/daily-analysis/DailyMLPage";
import { DailyMSLPage } from "./features/daily-analysis/DailyMSLPage";
import { DailyAttributePage } from "./features/daily-analysis/DailyAttributePage";
import { RiskPage } from "./pages/RiskPage";
import { DataManagementPage } from "./pages/DataManagementPage";
import { UsersPage } from "./pages/UsersPage";
import { LoginPage } from "./pages/LoginPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

const msalInstance = new PublicClientApplication(msalConfig);

export default function App() {
  return (
    <MsalProvider instance={msalInstance}>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
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
                <Route path="/admin/users" element={<UsersPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </QueryClientProvider>
      </AuthProvider>
    </MsalProvider>
  );
}
