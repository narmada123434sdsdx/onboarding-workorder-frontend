// App.jsx
import React, { useEffect } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import "./App.css";

/* ============================
   Onboarding (Individuals)
=============================== */
import Home from "./components/Home";
import Login from "./components/Login";
import Signup from "./components/Signup";
import OTPVerification from "./components/OTPVerification";
import ActivateAccount from "./components/ActivateAccount";
import ProviderProfile from "./components/ProviderProfile";
import ProviderServices from "./components/ProviderServices";
import ProviderHome from "./components/ProviderHome";
import ForgotPassword from "./components/ForgotPassword";
import Notifications from "./components/Notifications";

/* ============================
   Contractor (Company)
=============================== */
import CompanyLogin from "./components/company/CompanyLogin";
import CompanySignup from "./components/company/CompanySignup";
import CompanyActivateAccount from "./components/company/CompanyActivateAccount";
import CompanyOTPVerification from "./components/company/CompanyOTPVerification";
import CompanyDashboardHome from "./components/company/CompanyDashboardHome";
import CompanyProfile from "./components/company/CompanyProfile";
import CompanyServices from "./components/company/CompanyServices";
import CompanyNotifications from "./components/company/CompanyNotifications";
import CompanyApp from "./components/company/CompanyApp";

/* ============================
   Admin
=============================== */
import AdminLogin from "./components/AdminLogin";
import AdminApp from "./components/AdminApp";

/* ============================
   Work Order Module
=============================== */
import WorkOrderLayout from "./components/workorders/WorkOrderLayout";

/* ============================
   MAIN LAYOUT
=============================== */
function Layout({ user, setUser, admin, setAdmin, contractor, setContractor }) {
  const location = useLocation();

  // Hide Navbar + footer for some routes
  const hideLayout =
    location.pathname.startsWith("/provider") ||
    location.pathname.startsWith("/admin") ||
    location.pathname.startsWith("/contractor/dashboard") ||
    location.pathname.startsWith("/workorder");

  return (
    <div className="min-h-screen d-flex flex-column">

      {/* ========== NAVBAR (hidden for admin/workorders/provider) ========== */}
      {!hideLayout && (
        <nav className="navbar navbar-expand-lg sticky-top">
          <div className="container">

            <Link className="navbar-brand fw-bold" to="/">
              Ontract Services
            </Link>

            <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
              <span className="navbar-toggler-icon"></span>
            </button>

            <div className="collapse navbar-collapse" id="navbarNav">
              <ul className="navbar-nav ms-auto">

                <li className="nav-item">
                  <Link className="nav-link" to="/">Home</Link>
                </li>

                {/* Login Dropdown */}
                <li className="nav-item dropdown">
                  <a className="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
                    Login
                  </a>
                  <ul className="dropdown-menu">
                    <li><Link className="dropdown-item" to="/login">Individual</Link></li>
                    <li><Link className="dropdown-item" to="/contractor/login">Contractor</Link></li>
                  </ul>
                </li>

                {/* Signup Dropdown */}
                <li className="nav-item dropdown">
                  <a className="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
                    Sign Up
                  </a>
                  <ul className="dropdown-menu">
                    <li><Link className="dropdown-item" to="/signup">Individual</Link></li>
                    <li><Link className="dropdown-item" to="/contractor/signup">Contractor</Link></li>
                  </ul>
                </li>

              </ul>
            </div>

          </div>
        </nav>
      )}

      {/* MAIN ROUTES */}
      <main className="flex-fill">
        <Routes>

          {/* ============================
              Onboarding (Public)
          ============================= */}
          <Route path="/" element={<Home user={user} />} />
          <Route path="/login" element={<Login setUser={setUser} />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/verify-otp" element={<OTPVerification setUser={setUser} />} />
          <Route path="/activate" element={<ActivateAccount setUser={setUser} />} />
          <Route path="/forgot_password" element={<ForgotPassword />} />

          {/* Provider */}
          <Route path="/provider_home/*" element={<ProviderHome user={user} />} />
          <Route path="/provider/profile" element={<ProviderProfile />} />
          <Route path="/provider/services" element={<ProviderServices />} />
          <Route path="/provider/notifications" element={<Notifications />} />

          {/* ============================
              Contractor (Company)
          ============================= */}
          <Route path="/contractor/login" element={<CompanyLogin setContractor={setContractor} />} />
          <Route path="/contractor/signup" element={<CompanySignup />} />
          <Route path="/contractor/activate" element={<CompanyActivateAccount />} />
          <Route path="/contractor/verify_otp" element={<CompanyOTPVerification />} />

          <Route path="/contractor/dashboard/*" element={<CompanyApp contractor={contractor} />} />

          {/* ============================
              Admin
          ============================= */}
          <Route path="/admin/login" element={<AdminLogin setAdmin={setAdmin} />} />
          <Route path="/admin/*" element={<AdminApp admin={admin} />} />

          {/* ============================
              ⭐ Work Order Module (Your Issue Fixed)
          ============================= */}
          <Route path="/workorder/*" element={<WorkOrderLayout />} />

          {/* Fallback */}
          <Route path="*" element={<Home />} />

        </Routes>
      </main>

      {/* FOOTER (hidden for admin/workorder/provider) */}
      {!hideLayout && (
        <footer className="bg-dark text-light text-center p-3 mt-auto">
          © 2025 Ontract Services
        </footer>
      )}

    </div>
  );
}

/* ============================
   MAIN APP EXPORT
=============================== */
export default function App() {
  const [user, setUser] = React.useState(null);
  const [admin, setAdmin] = React.useState(null);
  const [contractor, setContractor] = React.useState(null);

  useEffect(() => {
    try {
      const u = localStorage.getItem("user");
      if (u && u !== "undefined") setUser(JSON.parse(u));

      const a = localStorage.getItem("admin");
      if (a && a !== "undefined") setAdmin(JSON.parse(a));

      const c = localStorage.getItem("contractor");
      if (c && c !== "undefined") setContractor(JSON.parse(c));

    } catch (e) {
      console.error("LocalStorage parsing error:", e);
      localStorage.clear();
    }
  }, []);

  return (
    <Layout
      user={user}
      setUser={setUser}
      admin={admin}
      setAdmin={setAdmin}
      contractor={contractor}
      setContractor={setContractor}
    />
  );
}
