// src/pages/CompanyApp.jsx
import React, { useEffect, useState, useRef } from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { FaUserCircle, FaBell, FaClipboardList } from "react-icons/fa";
import "bootstrap/dist/css/bootstrap.min.css";
import "./css/CompanyApp.css";
import { BASE_URLS } from "../../api/api";

function CompanyApp() {
  const navigate = useNavigate();
  const location = useLocation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [userName, setUserName] = useState("Company");

  // Safely get contractor (company) from localStorage
  let storedContractor = null;
  try {
    const stored = localStorage.getItem("contractor");
    if (stored && stored !== "undefined" && stored !== "null") {
      storedContractor = JSON.parse(stored);
    }
  } catch (err) {
    console.error("Error parsing contractor from localStorage:", err);
  }

  const contractor = location.state?.contractor || storedContractor;
  console.log(contractor);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!contractor) navigate("/contractor/login");
  }, [contractor, navigate]);

  const email = contractor?.head_email || "Unknown";

  // Safely load username
  useEffect(() => {
    console.log("data",contractor);
    if (contractor?.company_name) {
      setUserName(contractor.company_name);
    } else {
      setUserName("Company");
    }
  }, [contractor]);

  // Fetch unread notification count
  const fetchUnreadCount = async () => {
    if (!email || email === "Unknown") return;
    try {
      const res = await fetch(
        `${BASE_URLS.user}/api/contractor/contractor_unread_count?email=${encodeURIComponent(email)}`
      );
      if (res.ok) {
        const data = await res.json();
        console.log(data.count);
        setUnreadCount(data.count || 0);
      }
    } catch (err) {
      console.error("Failed to fetch unread count:", err);
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [email]);

  // Logout
  const handleLogout = () => {
    localStorage.removeItem("contractor");
    navigate("/contractor/login");
  };

  // Dropdown behavior
  const toggleDropdown = () => setDropdownOpen((prev) => !prev);
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="company-dashboard-page d-flex flex-column">
      {/* NAVBAR */}
      <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm sticky-top">
        <div className="container-fluid px-4">
          {/* Brand */}
          <Link
            className="navbar-brand fw-bold text-primary d-flex align-items-center"
            to="/contractor/dashboard/home"
          >
            <div className="brand-icon">OS</div>
            <span className="ms-2">Ontract Services </span>
          </Link>

          {/* Navbar Toggle (for mobile) */}
          <button
            className="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarCompany"
          >
            <span className="navbar-toggler-icon"></span>
          </button>

          {/* Navbar Items */}
          <div className="collapse navbar-collapse" id="navbarCompany">
            <ul className="navbar-nav ms-auto align-items-center">
              <li className="nav-item">
                <Link className="nav-link px-3" to="/contractor/dashboard/home">
                  Home
                </Link>
              </li>
              <li className="nav-item">
                <Link
                  to="/contractor/dashboard/notifications"
                  className="nav-link position-relative px-3"
                >
                  <FaBell size={20} className="text-primary" />
                  {unreadCount > 0 && (
                    <span className="notification-badge">{unreadCount}</span>
                  )}
                </Link>
              </li>

              {/* Dropdown */}
              <li className="nav-item dropdown ms-2" ref={dropdownRef}>
                <button
                  className="btn border-0 bg-transparent d-flex align-items-center gap-2"
                  onClick={toggleDropdown}
                >
                  <FaUserCircle size={32} className="text-primary" />
                  <span className="d-none d-lg-inline text-dark">
                    {userName}
                  </span>
                </button>
                {dropdownOpen && (
                  <ul className="dropdown-menu dropdown-menu-end show mt-2">
                    <li>
                      <Link
                        className="dropdown-item"
                        to="/contractor/dashboard/profile"
                      >
                        <FaUserCircle className="me-2" />
                        Profile
                      </Link>
                    </li>
                    <li>
                      <Link
                        className="dropdown-item"
                        to="/contractor/dashboard/services"
                      >
                        <FaClipboardList className="me-2" />
                        Services
                      </Link>
                    </li>
                    <li>
                      <hr className="dropdown-divider" />
                    </li>
                    <li>
                      <button
                        className="dropdown-item text-danger"
                        onClick={handleLogout}
                      >
                        Logout
                      </button>
                    </li>
                  </ul>
                )}
              </li>
            </ul>
          </div>
        </div>
      </nav>

      {/* MAIN CONTENT AREA */}
      <div className="dashboard-content container-fluid mt-4 flex-grow-1">
        <Outlet
          context={{ email, contractor, refreshNotifications: fetchUnreadCount }}
        />
      </div>

      {/* FOOTER */}
      <footer className="dashboard-footer">
        <div className="container-fluid px-4">
          <div className="footer-content">
            <p>© 2025 Ontract Services. All Rights Reserved.</p>
            <div className="footer-links">
              <a href="#">Help Center</a>
              <a href="#">Privacy Policy</a>
              <a href="#">Terms of Service</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default CompanyApp;