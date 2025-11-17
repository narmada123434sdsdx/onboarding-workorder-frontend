import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { FaUserCircle, FaBell, FaMapMarkerAlt, FaTools, FaStar, FaChartLine, FaClipboardList, FaStarHalfAlt, FaCalendarAlt,
  FaDollarSign,
  FaClock,
  FaCheckCircle,
  FaUsers,
  FaTrophy,
  FaArrowUp,
  FaEye,
} from "react-icons/fa";
import "bootstrap/dist/css/bootstrap.min.css";
import { useState, useRef, useEffect } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, LineChart, Line, XAxis, YAxis, CartesianGrid,} from "recharts";
import "./css/ProviderHome.css";
import { BASE_URLS } from "../api/api";

function ProviderHome() {
  const navigate = useNavigate();
  const location = useLocation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const [userName, setUserName] = useState("Provider");

  const [unreadCount, setUnreadCount] = useState(0);
  const [userEmail, setUserEmail] = useState('');

  // Sample data
  const stats = {
    locationCount: 5,
    serviceCount: 12,
    averageRate: 4.6,
    performanceRating: 4.8,
    workOrderCount: 23,
    completedOrders: 187,
    monthlyRevenue: 45280,
    revenueGrowth: 12.5,
    activeClients: 34,
    responseTime: "2.3hrs",
    completionRate: 96,
  };

  const revenueData = [
    { month: "Jun", revenue: 38500 },
    { month: "Jul", revenue: 41200 },
    { month: "Aug", revenue: 39800 },
    { month: "Sep", revenue: 43500 },
    { month: "Oct", revenue: 44100 },
    { month: "Nov", revenue: 45280 },
  ];

  const ratingData = [
    { name: "5 Stars", value: 68, color: "#198754" },
    { name: "4 Stars", value: 22, color: "#0d6efd" },
    { name: "3 Stars", value: 7, color: "#ffc107" },
    { name: "2 Stars", value: 2, color: "#fd7e14" },
    { name: "1 Star", value: 1, color: "#dc3545" },
  ];

  const recentOrders = [
    { id: "WO-2024-1234", client: "Tech Corp", service: "IT Support", status: "In Progress", priority: "High" },
    { id: "WO-2024-1235", client: "BuildCo Inc", service: "Maintenance", status: "Pending", priority: "Medium" },
    { id: "WO-2024-1236", client: "Retail Plus", service: "Cleaning", status: "Completed", priority: "Low" },
  ];

  // SAFE USERNAME LOADING
  useEffect(() => {
    const loadUserName = () => {
      try {
        const stored = localStorage.getItem("user");
        console.log(" local storage ",stored);
        if (!stored) return "Provider";

        let parsed;
        try {
          parsed = JSON.parse(stored);
        } catch {
          return String(stored).trim() || "Provider";
        }

        const email = parsed?.email || parsed?.email_id || null;
        if (email) setUserEmail(email);

        const name =
          parsed?.name ||
          parsed?.fullName ||
          parsed?.username ||
          (parsed?.email ? parsed.email.split("@")[0] : null) ||
          "Provider";

        return String(name).trim();
      } catch (err) {
        console.error("Failed to load user:", err);
        return "Provider";
      }
    };

    setUserName(loadUserName());
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("provider_token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  useEffect(() => {
  if (!userEmail) return;

  const fetchUnreadCount = async () => {
    try {
      const res = await fetch(
        `${BASE_URLS.user}/api/unread_count?email=${encodeURIComponent(userEmail)}`
      );
      if (res.ok) {
        const data = await res.json();
        setUnreadCount(data.count || 0);
      }
    } catch (err) {
      console.error("Error fetching unread count:", err);
    }
  };

    // Fetch initially
    fetchUnreadCount();

    // Optional: refresh every 60 seconds
    const interval = setInterval(fetchUnreadCount, 60000);

    return () => clearInterval(interval);
  }, [userEmail]);


  const toggleDropdown = () => setDropdownOpen((prev) => !prev);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p>{`${payload[0].name}: ${payload[0].value}%`}</p>
        </div>
      );
    }
    return null;
  };

  const getStatusClass = (status) => {
    switch (status) {
      case "In Progress": return "status-progress";
      case "Pending": return "status-pending";
      case "Completed": return "status-completed";
      default: return "";
    }
  };

  const getPriorityClass = (priority) => {
    switch (priority) {
      case "High": return "priority-high";
      case "Medium": return "priority-medium";
      case "Low": return "priority-low";
      default: return "";
    }
  };

  return (
    <div className="provider-dashboard-page d-flex flex-column">
      {/* NAVBAR */}
      <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm sticky-top">
        <div className="container-fluid px-4">
          <Link className="navbar-brand fw-bold text-primary d-flex align-items-center" to="/provider_homeme">
            <div className="brand-icon">OS</div>
            <span className="ms-2">Ontract Services</span>
          </Link>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav ms-auto align-items-center">
              <li className="nav-item"><Link className="nav-link px-3" to="/provider_home">Home</Link></li>
              <li className="nav-item">
                <Link to="/provider_home/notifications" className="nav-link position-relative px-3">
                  <FaBell size={20} className="text-primary" />
                  {/* <span className="notification-badge">1</span> */}
                  {unreadCount > 0 && (
                    <span className="notification-badge">{unreadCount}</span>
                  )}
                </Link>
              </li>
              <li className="nav-item dropdown ms-2" ref={dropdownRef}>
                <button
                  className="btn border-0 bg-transparent d-flex align-items-center gap-2"
                  onClick={toggleDropdown}
                >
                  <FaUserCircle size={32} className="text-primary" />
                  <span className="d-none d-lg-inline text-dark">{userName}</span>
                </button>
                {dropdownOpen && (
                  <ul className="dropdown-menu dropdown-menu-end show mt-2">
                    <li><Link className="dropdown-item" to="/provider_home/profile"><FaUserCircle className="me-2" />Profile</Link></li>
                    <li><Link className="dropdown-item" to="/provider_home/workorder"><FaClipboardList className="me-2" />Work Orders</Link></li>
                    <li><hr className="dropdown-divider" /></li>
                    <li><button className="dropdown-item text-danger" onClick={handleLogout}>Logout</button></li>
                  </ul>
                )}
              </li>
            </ul>
          </div>
        </div>
      </nav>

      {/* MAIN DASHBOARD */}
      {location.pathname === "/provider_home" && (
        <main className="dashboard-container">
          <div className="container-fluid px-4 py-4">
            {/* Welcome */}
            <div className="welcome-section mb-4">
              <div>
                <h2 className="welcome-title">Welcome</h2>
                <p className="welcome-subtitle">Here's what's happening with your business today</p>
              </div>
              <div className="quick-actions d-none d-md-flex gap-3">
                <Link to="/provider_home/services" className="btn btn-outline-primary btn-action">
                  <FaTools className="me-2" /> Manage Services
                </Link>
                <Link to="/provider_home/workorder" className="btn btn-primary btn-action">
                  <FaClipboardList className="me-2" /> Work Orders
                </Link>
              </div>
            </div>

            {/* KEY METRICS */}
            <div className="metrics-grid mb-4">
              <div className="metric-card revenue-card" key="revenue">
                <div className="metric-icon-wrapper revenue-icon"><FaDollarSign /></div>
                <div className="metric-content">
                  <p className="metric-label">Monthly Revenue</p>
                  <h3 className="metric-value">${stats.monthlyRevenue.toLocaleString()}</h3>
                  <div className="metric-change positive">
                    <FaArrowUp size={12} />
                    <span>{stats.revenueGrowth}% from last month</span>
                  </div>
                </div>
              </div>

              <div className="metric-card clients-card" key="clients">
                <div className="metric-icon-wrapper clients-icon"><FaUsers /></div>
                <div className="metric-content">
                  <p className="metric-label">Active Clients</p>
                  <h3 className="metric-value">{stats.activeClients}</h3>
                  <p className="metric-subtext">Businesses served this month</p>
                </div>
              </div>

              <div className="metric-card completed-card" key="completed">
                <div className="metric-icon-wrapper completed-icon"><FaCheckCircle /></div>
                <div className="metric-content">
                  <p className="metric-label">Completed Orders</p>
                  <h3 className="metric-value">{stats.completedOrders}</h3>
                  <p className="metric-subtext">Total lifetime completions</p>
                </div>
              </div>

              <div className="metric-card response-card" key="response">
                <div className="metric-icon-wrapper response-icon"><FaClock /></div>
                <div className="metric-content">
                  <p className="metric-label">Avg Response Time</p>
                  <h3 className="metric-value">{stats.responseTime}</h3>
                  <p className="metric-subtext">Faster than 85% providers</p>
                </div>
              </div>
            </div>

            {/* MAIN ROW */}
            <div className="row g-4 mb-4">
              {/* Revenue Chart */}
              <div className="col-lg-8">
                <div className="dashboard-card">
                  <div className="card-header-custom">
                    <div>
                      <h5 className="card-title-custom">Revenue Overview</h5>
                      <p className="card-subtitle-custom">Your earnings over the last 6 months</p>
                    </div>
                    <button className="btn btn-sm btn-outline-secondary">
                      <FaEye className="me-1" />View Details
                    </button>
                  </div>
                  <div className="card-body-custom">
                    <ResponsiveContainer width="100%" height={280}>
                      <LineChart data={revenueData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
                        <XAxis dataKey="month" stroke="#6c757d" />
                        <YAxis stroke="#6c757d" />
                        <Tooltip
                          contentStyle={{
                            background: '#fff',
                            border: '1px solid #e9ecef',
                            borderRadius: '8px',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                          }}
                        />
                        <Line type="monotone" dataKey="revenue" stroke="#0d6efd" strokeWidth={3} dot={{ fill: '#0d6efd', r: 5 }} activeDot={{ r: 7 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Performance */}
              <div className="col-lg-4">
                <div className="dashboard-card performance-highlight-card">
                  <div className="card-header-custom">
                    <h5 className="card-title-custom">
                      <FaTrophy className="me-2 text-warning" /> Performance Score
                    </h5>
                  </div>
                  <div className="card-body-custom text-center">
                    <div className="performance-score-circle">
                      <div className="score-value">{stats.performanceRating}</div>
                      <div className="score-max">/5.0</div>
                    </div>
                    <p className="performance-label">Excellent Performance</p>
                    <div className="performance-stats-mini">
                      <div className="mini-stat"><FaStar className="text-warning" /><span>{stats.averageRate} Avg Rating</span></div>
                      <div className="mini-stat"><FaCheckCircle className="text-success" /><span>{stats.completionRate}% Completion</span></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* BOTTOM ROW */}
            <div className="row g-4">
              {/* Service Coverage */}
              <div className="col-lg-4">
                <div className="dashboard-card">
                  <div className="card-header-custom">
                    <h5 className="card-title-custom">Service Coverage</h5>
                  </div>
                  <div className="card-body-custom">
                    <div className="service-stat-item" key="location">
                      <div className="service-stat-icon location-icon"><FaMapMarkerAlt /></div>
                      <div className="service-stat-content">
                        <h4>{stats.locationCount}</h4>
                        <p>Service Locations</p>
                      </div>
                    </div>
                    <div className="service-stat-item" key="services">
                      <div className="service-stat-icon services-icon"><FaTools /></div>
                      <div className="service-stat-content">
                        <h4>{stats.serviceCount}</h4>
                        <p>Active Services</p>
                      </div>
                    </div>
                    <div className="service-stat-item mb-0" key="rating">
                      <div className="service-stat-icon rating-icon"><FaStar /></div>
                      <div className="service-stat-content">
                        <h4>{stats.averageRate} <FaStarHalfAlt size={14} /></h4>
                        <p>Customer Rating</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Rating Distribution */}
              <div className="col-lg-4">
                <div className="dashboard-card">
                  <div className="card-header-custom">
                    <h5 className="card-title-custom">Rating Distribution</h5>
                  </div>
                  <div className="card-body-custom chart-body">
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={ratingData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={85}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {ratingData.length > 0 ? (
                            ratingData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))
                          ) : (
                            <Cell key="empty" fill="#e9ecef" />
                          )}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="rating-legend">
                      {ratingData.map((item, idx) => (
                        <div key={`legend-${idx}`} className="legend-item">
                          <span className="legend-color" style={{ background: item.color }}></span>
                          <span>{item.name}: {item.value}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Orders */}
              <div className="col-lg-4">
                <div className="dashboard-card">
                  <div className="card-header-custom">
                    <h5 className="card-title-custom">Recent Orders</h5>
                    <Link to="/provider_home/workorder" className="view-all-link">View All</Link>
                  </div>
                  <div className="card-body-custom p-0">
                    <div className="orders-list">
                      {recentOrders.map((order) => (
                        <div key={order.id} className="order-item">
                          <div className="order-header">
                            <span className="order-id">{order.id}</span>
                            <span className={`order-priority ${getPriorityClass(order.priority)}`}>
                              {order.priority}
                            </span>
                          </div>
                          <p className="order-client">{order.client}</p>
                          <div className="order-footer">
                            <span className="order-service">{order.service}</span>
                            <span className={`order-status ${getStatusClass(order.status)}`}>
                              {order.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="card-footer-custom">
                      <div className="pending-badge">
                        <FaCalendarAlt className="me-2" />
                        {stats.workOrderCount} pending actions required
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      )}

      <Outlet />

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

export default ProviderHome;