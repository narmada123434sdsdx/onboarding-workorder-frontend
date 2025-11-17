import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import "./css/sidebar.css";

const Sidebar = () => {
  const [hoveredMenu, setHoveredMenu] = useState(null);
  const [isOpen, setIsOpen] = useState(false);

    // ✅ Automatically close on mobile screens at first render
  useEffect(() => {
    if (window.innerWidth > 768) {
      setIsOpen(true);
    }
  }, []);

  const getSymbol = (menu) => (hoveredMenu === menu ? "▼" : "▸");

  const handleLinkClick = () => {
    if (window.innerWidth <= 768) setIsOpen(false);
  };

  return (
    <div className="sidebar-container">
      <div className="hamburger" onClick={() => setIsOpen(!isOpen)}>
        ☰
      </div>

      <aside className={`sidebar ${isOpen ? "open" : "closed"}`}>
        {/* Work Orders Setup */}
        <div
          className="menu-section"
          onMouseEnter={() => setHoveredMenu("setup")}
          onMouseLeave={() => setHoveredMenu(null)}
        >
          <div className="menu-title">
            <span>Work Orders Setup</span>
            <span className="menu-symbol">{getSymbol("setup")}</span>
          </div>

          {hoveredMenu === "setup" && (
            <div className="submenu">
              <NavLink
                to="/admin/workorder/workorder-type"
                onClick={handleLinkClick}
              >
                Work Type
              </NavLink>
              <NavLink
                to="/admin/workorder/workorder-area"
                onClick={handleLinkClick}
              >
                Work Area
              </NavLink>
            </div>
          )}
        </div>

        <div className="sidebar-divider"></div>

        {/* Work Orders */}
        <div
          className="menu-section"
          onMouseEnter={() => setHoveredMenu("orders")}
          onMouseLeave={() => setHoveredMenu(null)}
        >
          <div className="menu-title">
            <span>Work Orders</span>
            <span className="menu-symbol">{getSymbol("orders")}</span>
          </div>

          {hoveredMenu === "orders" && (
            <div className="submenu">
              <NavLink to="/admin/workorder/create-workorder" onClick={handleLinkClick}>
                Parent Work Order
              </NavLink>
              <NavLink to="/admin/workorder/child-workorder" onClick={handleLinkClick}>
                Child Work Order
              </NavLink>
              <NavLink to="/admin/workorder/mapping-workorder" onClick={handleLinkClick}>
                Mapping Work Orders
              </NavLink>
              <NavLink to="/admin/workorder/list" onClick={handleLinkClick}>
                List Work Orders
              </NavLink>
              <NavLink to="/admin/workorder/contractor" onClick={handleLinkClick}>
                Assign WO To Contractor
              </NavLink>
              <NavLink to="/admin/workorder/search-workorder" onClick={handleLinkClick}>
                Workorder Search
              </NavLink>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
};

export default Sidebar;
