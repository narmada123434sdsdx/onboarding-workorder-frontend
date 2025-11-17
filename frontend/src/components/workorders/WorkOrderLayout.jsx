import React from "react";
import { Routes, Route } from "react-router-dom";
import Sidebar from "./Sidebar";
import ChildWorkorder from "./ChildWorkorder";
import SearchWorkOrder from "./SearchWorkorder";

// import "./css/sidebar.css";  // if needed for sidebar
import WorkorderTypePage from "./Workorder_type";
import WorkorderAreaPage from "./Workorder_Area";
import CreateWorkOrder from "./CreateWorkorder";
import MappingPage from "./MappingPage";
import WorkOrders from "./WorkOrder";
import WorkOrderDetails from "./WorkOrderDetails";
import Contractor from "./Contractor";

export default function WorkOrderLayout() {
  return (
    <div className="workorder-layout">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Right Content Area */}
      <div className="workorder-content">
        <Routes>
          <Route path="/" element={<WorkOrders/>} />
          <Route path="/create-workorder" element={<CreateWorkOrder />} />
          <Route path="/child-workorder" element={<ChildWorkorder />} />
          <Route path="/mapping-workorder" element={<MappingPage />} />
          <Route path="/workorder-type" element={<WorkorderTypePage />} />
          <Route path="/workorder-area" element={<WorkorderAreaPage />} />                 
          <Route path="/list" element={<WorkOrders/>} />
          <Route path="/search-workorder" element={<SearchWorkorder/>} />  
          <Route path="/contractor" element={<Contractor />} />
          <Route path="/workorders/:id" element={<WorkOrderDetails />} />
        </Routes>
      </div>
    </div>
  );
}
