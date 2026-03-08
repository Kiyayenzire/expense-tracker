

// src/App.jsx

import { Routes, Route, useLocation } from "react-router-dom";
import { Box } from "@mui/material";

import Dashboard from "./pages/Dashboard";
import Expenses from "./pages/Expenses";
import Login from "./pages/Login";
import Reports from "./pages/Reports";
import EmailCheck from "./pages/EmailCheck";
import Register from "./pages/Register";
import ActivateAccount from "./pages/ActivateAccount";

import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {

  const location = useLocation();

  const isPublicRoute =
    location.pathname === "/login" ||
    location.pathname === "/register" ||
    location.pathname === "/check-email" ||
    location.pathname.startsWith("/activate/");

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>

      {!isPublicRoute && <Navbar />}

      <Box sx={{ p: 3 }}>

          <Routes>

            <Route path="/check-email" element={<EmailCheck />} />

            <Route path="/register" element={<Register />} />

            <Route path="/activate/:token" element={<ActivateAccount />} />

            <Route path="/login" element={<Login />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/expenses"
              element={
                <ProtectedRoute>
                  <Expenses />
                </ProtectedRoute>
              }
            />

            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <Reports />
                </ProtectedRoute>
              }
            />

          </Routes>

        </Box>

      </Box>
  );

}


