import React, { useState, useEffect } from "react";
import Select from "react-select";
import "./css/createworkorder.css";
import Swal from "sweetalert2";
import { apiGet, apiFetch } from "../../api/api";

const CreateWorkOrder = () => {
  const [workorderTypes, setWorkorderTypes] = useState([]);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [workorderAreas, setWorkorderAreas] = useState([]);
  const [selectedArea, setSelectedArea] = useState("");
  const [typeRates, setTypeRates] = useState({});
  const [images, setImages] = useState({});
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState("");
  const [ticketAssignmentType, setTicketAssignmentType] = useState("auto");

  const [formData, setFormData] = useState({
    REQUESTED_TIME_CLOSING: "",
    REMARKS: "",
    STATUS: "OPEN",
    ADDRESS: "",            // ➕ ADDED
  });

  // ===============================
  // Fetch Workorder Types, Areas, and Clients
  // ===============================
  useEffect(() => {
    const fetchTypes = async () => {
      try {
        const data = await apiGet("/api/workorder-type");
        setWorkorderTypes(
          data.map((type) => ({
            value: type.workorder_type,
            label: type.workorder_type,
          }))
        );
      } catch (err) {
        console.error("Error fetching types:", err);
      }
    };

    const fetchAreas = async () => {
      try {
        const data = await apiGet("/api/workorder-areas");
        setWorkorderAreas(data);
      } catch (err) {
        console.error("Error fetching areas:", err);
      }
    };

    const fetchClients = async () => {
      try {
        const data = await apiGet("/api/workorders/standard-rates");
        const uniqueClients = Array.from(new Set(data.map((item) => item.client)));
        setClients(uniqueClients);
      } catch (err) {
        console.error("Error fetching clients:", err);
      }
    };

    fetchClients();
    fetchTypes();
    fetchAreas();
  }, []);

  // ===============================
  // Sync rate fields
  // ===============================
  useEffect(() => {
    const newRates = {};
    selectedTypes.forEach((type) => {
      newRates[type.value] = typeRates[type.value] || 0;
    });
    setTypeRates(newRates);
  }, [selectedTypes]);

  // ===============================
  // Handle changes
  // ===============================
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleReset = () => {
    setFormData({
      REQUESTED_TIME_CLOSING: "",
      REMARKS: "",
      STATUS: "OPEN",
      ADDRESS: "",           // ➕ RESET ADDED
    });
    setSelectedTypes([]);
    setSelectedArea("");
    setSelectedClient("");
    setImages({});
    setTypeRates({});
    setTicketAssignmentType("auto");
  };

  // ===============================
  // Handle images
  // ===============================
  const handleImageChange = (type, files) => {
    if (!files?.length) return;
    const fileArray = Array.from(files);
    setImages((prev) => ({
      ...prev,
      [type]: [...(prev[type] || []), ...fileArray],
    }));
  };

  const removeImage = (type, index) => {
    setImages((prev) => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index),
    }));
  };

  // ===============================
  // Submit logic
  // ===============================
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedTypes.length === 0) {
      Swal.fire("⚠️ Warning", "Please select at least one Work Order Type", "warning");
      return;
    }
    if (!selectedClient) {
      Swal.fire("⚠️ Warning", "Please select a client", "warning");
      return;
    }

    try {
      // Generate workorder ID
      const { workorder: workorderId } = await apiGet(
        `/api/workorders/generate?workorder_type=${selectedTypes[0].value}`
      );

      if (!workorderId) throw new Error("Failed to generate workorder number");

      // Prepare form data
      const totalRate = Object.values(typeRates).reduce(
        (sum, val) => sum + (parseFloat(val) || 0),
        0
      );

      const formDataToSend = new FormData();
      formDataToSend.append("WORKORDER", workorderId);
      formDataToSend.append(
        "WORKORDER_TYPE",
        selectedTypes.map((t) => t.value).join(",")
      );
      formDataToSend.append("WORKORDER_AREA", selectedArea);
      formDataToSend.append("STATUS", "OPEN");
      formDataToSend.append(
        "RATE",
        JSON.stringify({ type_rates: typeRates, total_rate: totalRate })
      );
      formDataToSend.append("CLIENT", selectedClient);
      formDataToSend.append(
        "REQUESTED_TIME_CLOSING",
        formData.REQUESTED_TIME_CLOSING
      );
      formDataToSend.append("REMARKS", formData.REMARKS);

      // ➕ ADD ADDRESS TO PAYLOAD
      formDataToSend.append("ADDRESS", formData.ADDRESS);

      formDataToSend.append("ticket_assignment_type", ticketAssignmentType);

      // Attach images
      for (const [type, fileArray] of Object.entries(images)) {
        fileArray.forEach((file) => {
          formDataToSend.append(`images[${type}][]`, file);
        });
      }

      await apiFetch("/api/workorders/", {
        method: "POST",
        body: formDataToSend,
      });

      Swal.fire({
        title: "✅ Workorder Created Successfully",
        html: `<b>Workorder Number:</b> ${workorderId}`,
        icon: "success",
        confirmButtonText: "OK",
        confirmButtonColor: "#3085d6",
      });

      handleReset();
    } catch (err) {
      console.error("Error creating workorder:", err);
      Swal.fire("❌ Error", err.message, "error");
    }
  };

  // ===============================
  // Render UI
  // ===============================
  return (
    <div className="page-container full-page">
      <strong className="workorder-title">CREATE WORK ORDER</strong>

      <form onSubmit={handleSubmit} className="workorder-form">
        
        {/* === Combined Work Order Type + Area === */}
        <div className="form-group full-width combined-row">
          <div className="combined-header">
            <div className="header-item">Work Order Type</div>
            <div className="header-item">Work Order Area</div>
          </div>

          <div className="combined-body">
            <div className="form-group required-wrapper select-area-wrapper">
              <Select
                options={workorderTypes}
                value={selectedTypes}
                onChange={setSelectedTypes}
                isMulti
                closeMenuOnSelect={false}
                placeholder="Select Work Order Types..."
                classNamePrefix="react-select"
                menuPortalTarget={document.body}
              />
              <span className="required-star">★</span>
            </div>

            <div className="form-group required-wrapper select-area-wrapper">
              <select
                value={selectedArea}
                onChange={(e) => setSelectedArea(e.target.value)}
                required
              >
                <option value="">Select Area</option>
                {workorderAreas.map((area) => (
                  <option key={area.id} value={area.workorder_area}>
                    {area.workorder_area}
                  </option>
                ))}
              </select>
              <span className="required-star">★</span>
            </div>
          </div>
        </div>

        {/* === Client + Assignment Type === */}
        <div className="form-group full-width combined-row">
          <div className="combined-header">
            <div className="header-item">Client</div>
            <div className="header-item">Assignment Type</div>
          </div>

          <div className="combined-body">
            <div className="form-group required-wrapper">
              <select
                value={selectedClient}
                onChange={(e) => setSelectedClient(e.target.value)}
                required
              >
                <option value="">Select Client</option>
                {clients.map((client, idx) => (
                  <option key={idx} value={client}>
                    {client}
                  </option>
                ))}
              </select>
              <span className="required-star">★</span>
            </div>

            <div className="form-group required-wrapper">
              <select
                value={ticketAssignmentType}
                onChange={(e) => setTicketAssignmentType(e.target.value)}
                required
              >
                <option value="auto">Auto</option>
                <option value="manual">Manual</option>
              </select>
              <span className="required-star">★</span>
            </div>
          </div>
        </div>

        {/* === Requested Time Closing + Remarks === */}
        <div className="form-group full-width combined-row">
          <div className="combined-header">
            <div className="header-item">Requested Time Closing</div>
            <div className="header-item">Remarks</div>
          </div>

          <div className="combined-body">
            <div className="form-group required-wrapper">
              <input
                type="datetime-local"
                name="REQUESTED_TIME_CLOSING"
                value={formData.REQUESTED_TIME_CLOSING}
                onChange={handleChange}
                required
              />
              <span className="required-star">★</span>
            </div>

            <div className="form-group required-wrapper">
              <input
                type="text"
                name="REMARKS"
                value={formData.REMARKS}
                onChange={handleChange}
                required
              />
              <span className="required-star">★</span>
            </div>
          </div>
        </div>

        {/* === WORK ORDER ADDRESS (NEW FIELD) === */}
        <div className="form-group full-width combined-row">
          <div className="combined-header">
            <div className="header-item">Work Order Address</div>
          </div>

          <div className="combined-body">
            <div className="form-group required-wrapper">
              <input
                type="text"
                name="ADDRESS"
                value={formData.ADDRESS}
                onChange={handleChange}
                placeholder="Enter full work order address..."
                required
              />
              <span className="required-star">★</span>
            </div>
          </div>
        </div>

        {/* === Upload Images Section === */}
        {selectedTypes.length > 0 && (
          <div className="form-group full-width combined-row">
            <div className="combined-header single-header">
              <div className="header-item">Upload Images</div>
            </div>

            <div className="combined-body image-upload-body">
              {selectedTypes.map((type) => (
                <div key={type.value} className="rate-input">
                  <div className="type-header">
                    <span className="type-label">{type.value}</span>
                    <span className="image-count">
                      ({images[type.value]?.length || 0} image
                      {images[type.value]?.length !== 1 ? "s" : ""})
                    </span>
                  </div>

                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={(e) => handleImageChange(type.value, e.target.files)}
                    className="file-input"
                  />

                  {images[type.value]?.length > 0 && (
                    <div className="image-preview-list">
                      {images[type.value].map((file, idx) => (
                        <div key={idx} className="image-preview-item">
                          <img
                            src={URL.createObjectURL(file)}
                            alt={file.name}
                            className="preview-thumbnail"
                          />
                          <div className="file-info">
                            <span className="file-name">{file.name}</span>
                            <button
                              type="button"
                              className="remove-btn"
                              onClick={() => removeImage(type.value, idx)}
                            >
                              ❌
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* === Buttons === */}
        <div className="form-actions">
          <button type="submit" className="btn-primary">
            Create Workorder
          </button>
          <button type="button" className="btn-reset" onClick={handleReset}>
            Reset
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateWorkOrder;
