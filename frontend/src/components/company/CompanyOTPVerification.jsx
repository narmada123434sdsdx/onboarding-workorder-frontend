import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./css/CompanyOTPVerification.css";
import { BASE_URLS } from "../../api/api";

function CompanyOTPVerification({setContractor}) {
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email || "";

  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleVerify = async (e) => {
  e.preventDefault();
  setError("");
  setMessage("");
  setLoading(true);

  try {
    const res = await fetch(`${BASE_URLS.user}/api/contractor/verify_otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp }),
    });

    const data = await res.json();
    if (res.ok) {
      setMessage("OTP verified successfully!");
      localStorage.setItem("contractor", JSON.stringify(data.contractor));
      setContractor(data.contractor);
      console.log(data.contractor);
      navigate("/contractor/dashboard/home");
    } else {
      setError(data.error || "Invalid OTP");
    }
  } catch (err) {
    setError("Verification failed. Please try again.");
  } finally {
    setLoading(false);
  }
};

  const handleResend = async () => {
    setError("");
    setMessage("");
    try {
      const res = await fetch(`${BASE_URLS.user}api/contractor/resend_otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      setMessage(data.message || "OTP resent successfully!");
    } catch {
      setError("Failed to resend OTP.");
    }
  };

  return (
    <div className="otp-container">
      <div className="otp-card">
        <h2>OTP Verification</h2>
        <p>We’ve sent an OTP to <strong>{email}</strong></p>

        {message && <p className="success-text">{message}</p>}
        {error && <p className="error-text">{error}</p>}

        <form onSubmit={handleVerify}>
          <input
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            placeholder="Enter OTP"
            maxLength={6}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? "Verifying..." : "Verify OTP"}
          </button>
        </form>

        <button className="resend-btn" onClick={handleResend}>
          Resend OTP
        </button>
      </div>
    </div>
  );
}

export default CompanyOTPVerification;
