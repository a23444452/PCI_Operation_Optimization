import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppLayout } from "./components/layout/AppLayout";
import { OffloadPage } from "./pages/OffloadPage";
import { ShippingPage } from "./pages/ShippingPage";
import { COAPage } from "./pages/COAPage";
import { DailyMLPage } from "./pages/DailyMLPage";
import { DailyMSLPage } from "./pages/DailyMSLPage";
import { DailyAttributePage } from "./pages/DailyAttributePage";
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

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AppLayout />}>
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
  );
}
