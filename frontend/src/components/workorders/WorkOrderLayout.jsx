import React from "react";
import { Routes, Route } from "react-router-dom";
import Sidebar from "./Sidebar";
import ChildWorkOrder from "./ChildWorkOrder";
import SearchWorkOrder from "./SearchWorkOrder";

// import "./css/sidebar.css";  // if needed for sidebar
import WorkOrderTypePage from "./Workorder_type";
import WorkOrderAreaPage from "./Workorder_Area";
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
          <Route path="/child-workorder" element={<ChildWorkOrder />} />
          <Route path="/mapping-workorder" element={<MappingPage />} />
          <Route path="/workorder-type" element={<WorkOrderTypePage />} />
          <Route path="/workorder-area" element={<WorkOrderAreaPage />} />                 
          <Route path="/list" element={<WorkOrders/>} />
          <Route path="/search-workorder" element={<SearchWorkOrder/>} />  
          <Route path="/contractor" element={<Contractor />} />
          <Route path="/workorders/:id" element={<WorkOrderDetails />} />
        </Routes>
      </div>
    </div>
  );
}
