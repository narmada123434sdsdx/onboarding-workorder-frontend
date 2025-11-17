import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./css/workorderdetails.css";
import { apiGet, apiPut, apiPost } from "../../api/api";

const WorkOrderDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [details, setDetails] = useState(null);
  const [contractors, setContractors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Fetch details + contractors
  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const data = await apiGet(`/api/workorders/${id}`);

        data.RATE = data.RATE || { total_rate: 0, type_rates: {} };
        setDetails(data);

        // Fetch contractors by AREA + TYPE
        if (data.WORKORDER_AREA && data.WORKORDER_TYPE) {
          const contractorsData = await apiGet(
            `/api/workorders/contractors/by-area-type/${encodeURIComponent(
              data.WORKORDER_AREA
            )}/${encodeURIComponent(data.WORKORDER_TYPE)}`
          );

          setContractors(Array.isArray(contractorsData) ? contractorsData : []);
        }

        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchDetails();
  }, [id]);

  // Handle contractor selection
  const handleChange = (e) => {
    const { name, value } = e.target;

    if (name === "CONTRACTOR_NAME") {
      const selected = contractors.find((c) => c.full_name === value);

      setDetails((prev) => ({
        ...prev,
        CONTRACTOR_NAME: selected?.full_name || "",
        CONTRACTOR_RATE: selected?.rate || "",
        CONTRACTOR_ID: selected?.provider_id || "",
        CONTRACTOR_EMAIL: selected?.email_id || "",
      }));
    } else {
      setDetails((prev) => ({ ...prev, [name]: value }));
    }
  };

  // Save contractor assignment
  const handleSave = async () => {
    if (!details) return;

    // Validation
    if (!details.CONTRACTOR_NAME || details.CONTRACTOR_NAME.trim() === "") {
      window.alert("⚠️ Please select a contractor before assigning.");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Update WorkOrder
      await apiPut(`/api/workorders/${id}`, details);

      // Send mail
      if (details.CONTRACTOR_ID) {
        await apiPost(`/api/workorders/send-acceptance-mail/${id}`, {
          CONTRACTOR_ID: details.CONTRACTOR_ID,
          CONTRACTOR_EMAIL: details.CONTRACTOR_EMAIL,
          CONTRACTOR_NAME: details.CONTRACTOR_NAME,
          workorder: details.WORKORDER,
        });
      }

      window.alert("Email sent to contractor for acceptance.");

      navigate("/workorder/contractor");
    } catch (err) {
      console.error(err);
      setError(err.message);
      window.alert("❌ Error: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => navigate(-1);

  if (loading) return <div className="center">Loading details...</div>;
  if (error) return <div className="center error">Error: {error}</div>;
  if (!details) return <div className="center">No details found</div>;

  return (
    <div className="workorders-container">
      {/* --- Main Card --- */}
      <div className="section-card">
        <div className="section-header left-header">
          Work Order Details - {details.WORKORDER}
        </div>

        <div className="section-content">
          <div className="wo-header-row">
            <div>Work Order</div>
            <div>Type</div>
            <div>Area</div>
          </div>
          <div className="wo-value-row">
            <div>{details.WORKORDER}</div>
            <div>{details.WORKORDER_TYPE}</div>
            <div>{details.WORKORDER_AREA}</div>
          </div>

          <div className="wo-header-row">
            <div>Status</div>
            <div>Remarks</div>
            <div>Client</div>
          </div>
          <div className="wo-value-row" style={{ gridTemplateColumns: "1fr 2fr" }}>
            <div className={`status ${details.STATUS?.toLowerCase()}`}>
              {details.STATUS}
            </div>
            <div>{details.REMARKS || "-"}</div>
            <div>{details.CLIENT || "-"}</div>
          </div>

          <div className="wo-header-row">
            <div>Contractor Name</div>
          </div>
          <div className="wo-value-row">
            <div>
              {contractors.length > 0 ? (
                <select
                  name="CONTRACTOR_NAME"
                  value={details.CONTRACTOR_NAME || ""}
                  onChange={handleChange}
                >
                  <option value="">-- Select Contractor --</option>
                  {contractors.map((c) => (
                    <option key={c.provider_id} value={c.full_name}>
                      {c.full_name} — ({c.service_locations})
                    </option>
                  ))}
                </select>
              ) : (
                <em>No contractors found for this area.</em>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* --- Action Buttons --- */}
      <div className="wo-actions-center">
        <button className="blue-btn" onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : "💾 Assign Contractor"}
        </button>
        <button className="blue-btn cancel" onClick={handleCancel}>
          ✖ Cancel
        </button>
      </div>
    </div>
  );
};

export default WorkOrderDetails;
