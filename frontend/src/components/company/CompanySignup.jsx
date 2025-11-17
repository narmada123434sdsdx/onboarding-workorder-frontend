import React, { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import ReCAPTCHA from "react-google-recaptcha";
import "./css/CompanySignup.css";
import { BASE_URLS } from "../../api/api";

function CompanySignup() {
  const [companyName, setCompanyName] = useState("");
  const [registrationNumber, setRegistrationNumber] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [captchaToken, setCaptchaToken] = useState(null);
  const recaptchaRef = useRef();
  const navigate = useNavigate();

  // ✅ Test reCAPTCHA key
  const RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI";

  const validateForm = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    // ✅ Company Name validation
    if (!companyName.trim()) {
      errors.companyName = "Company Name is required.";
    } else if (!/^[A-Za-z0-9&.,\- ]+$/.test(companyName)) {
      errors.companyName = "Only letters, numbers, spaces, &, ., and - are allowed.";
    }

    if (!registrationNumber.trim()) {
      errors.registrationNumber = "Business Registration Number is required.";
    } else if (!/^BR[0-9]{6,8}$/.test(registrationNumber)) {
      errors.registrationNumber = "Start with BR followed by 6-8 digits";
    }

    if (!email.trim()) {
      errors.email = "Email is required.";
    } else if (!emailRegex.test(email)) {
      errors.email = "Please enter a valid email.";
    }

    if (!phoneNumber.trim()) {
      errors.phoneNumber = "Phone number is required.";
    } else if (!/^\d+$/.test(phoneNumber)) {
      errors.phoneNumber = "Phone number must contain only digits.";
    } else if (phoneNumber.length !== 10) {
      errors.phoneNumber = "Please enter exactly 10 digits.";
    }

    if (!password.trim()) {
      errors.password = "Password is required.";
    } else {
      if (password.length < 8) {
        errors.password = "Password must be at least 8 characters.";
      } else if (!/[A-Z]/.test(password)) {
        errors.password = "Password must contain an uppercase letter.";
      } else if (!/[a-z]/.test(password)) {
        errors.password = "Password must contain a lowercase letter.";
      } else if (!/[0-9]/.test(password)) {
        errors.password = "Password must contain a digit.";
      } else if (!/[^A-Za-z0-9]/.test(password)) {
        errors.password = "Password must contain a special character.";
      }
    }

    if (!confirmPassword.trim()) {
      errors.confirmPassword = "Confirm your password.";
    } else if (password !== confirmPassword) {
      errors.confirmPassword = "Passwords do not match.";
    }

    if (!captchaToken) {
      errors.captcha = "Please complete the captcha verification.";
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) return;
    setLoading(true);

    try {
      const response = await fetch(`${BASE_URLS.user}/api/contractor/contractor_signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: companyName,
          business_registration_number: registrationNumber,
          email_id: email,
          phone_number: phoneNumber,
          password,
          captcha_token: captchaToken,
        }),
      });

      const data = await response.json();
      console.log(data);
      if (response.ok) {
        navigate("/contractor/login", {
          state: {
            message:
              "The activation link has been sent to your email. Please check your inbox to activate your account before login.",
          },
        });
        // Reset form
        setCompanyName("");
        setRegistrationNumber("");
        setEmail("");
        setPhoneNumber("");
        setPassword("");
        setConfirmPassword("");
        recaptchaRef.current.reset();
        setCaptchaToken(null);
      } else {
        setError(data.error || "Signup failed. Please try again.");
        recaptchaRef.current.reset();
        setCaptchaToken(null);
      }
    } catch (err) {
      setError("An error occurred. Please try again later.");
      recaptchaRef.current.reset();
      setCaptchaToken(null);
    } finally {
      setLoading(false);
    }
  };

  const onCaptchaChange = (token) => {
    setCaptchaToken(token);
    if (token) {
      setFieldErrors((prev) => ({ ...prev, captcha: "" }));
    }
  };
  const preventPaste = (e) => {
    e.preventDefault();
  };

  return (
    <div className="signup-container">
      <div className="signup-card">
        <h2 className="signup-title">Contractor Registration</h2>
        <p className="signup-subtitle">Join our platform as a company</p>

        {error && <p className="signup-error">{error}</p>}

        <form onSubmit={handleSubmit} className="signup-form">

          {/* ✅ Company Name Field 04-11-2025*/}
          <div className="form-group">
            <label htmlFor="companyName">
              Company Name <span className="required-asterisk">*</span>
            </label>
            <input
              type="text"
              id="companyName"
              value={companyName}
              onChange={(e) => {
                const val = e.target.value;
                setCompanyName(val);
                if (/^[A-Za-z0-9&.,\- ]+$/.test(val)) {
                  setFieldErrors((prev) => ({ ...prev, companyName: "" }));
                }
              }}
              placeholder="Enter your company name"
              disabled={loading}
            />
            {fieldErrors.companyName && (
              <span className="error-text">{fieldErrors.companyName}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="registrationNumber">
              Business Registration Number <span className="required-asterisk">*</span>
            </label>
            <input
              type="text"
              id="registrationNumber"
              value={registrationNumber}
              onChange={(e) => {
                const val = e.target.value;
                setRegistrationNumber(val);
                if (/^[A-Za-z0-9-]+$/.test(val)) {
                  setFieldErrors((prev) => ({ ...prev, registrationNumber: "" }));
                }
              }}
              placeholder="Enter your business registration number"
              disabled={loading}
            />
            {fieldErrors.registrationNumber && (
              <span className="error-text">{fieldErrors.registrationNumber}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="email">
              Email <span className="required-asterisk">*</span>
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => {
                const value = e.target.value;
                setEmail(value);
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (emailRegex.test(value)) {
                  setFieldErrors((prev) => ({ ...prev, email: "" }));
                }
              }}
              placeholder="Enter your email"
              disabled={loading}
            />
            {fieldErrors.email && (
              <span className="error-text">{fieldErrors.email}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="phoneNumber">
              Phone Number <span className="required-asterisk">*</span>
            </label>
            <input
              type="tel"
              id="phoneNumber"
              value={phoneNumber}
              onChange={(e) => {
                const val = e.target.value;
                setPhoneNumber(val);
                if (/^\d{10}$/.test(val)) {
                  setFieldErrors((prev) => ({ ...prev, phoneNumber: "" }));
                }
              }}
              placeholder="Enter your phone number"
              disabled={loading}
            />
            {fieldErrors.phoneNumber && (
              <span className="error-text">{fieldErrors.phoneNumber}</span>
            )}
          </div>

       <div className="form-group password-group">
            <label htmlFor="password">Password <span className="required-asterisk">*</span></label>
            <div className="password-wrapper">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onPaste={preventPaste}
                placeholder="Create a password"
                disabled={loading}
              />
              <span className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </span>
            </div>
            {fieldErrors.password && <span className="error-text">{fieldErrors.password}</span>}
          </div>

          <div className="form-group password-group">
            <label htmlFor="confirmPassword">Confirm Password <span className="required-asterisk">*</span></label>
            <div className="password-wrapper">
              <input
                type={showConfirmPassword ? "text" : "password"}
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => {
                  const val = e.target.value;
                  setConfirmPassword(val);
                  if (val === password) {
                    setFieldErrors((prev) => ({ ...prev, confirmPassword: "" }));
                  }
                }}
                onPaste={preventPaste}
                placeholder="Confirm your password"
                disabled={loading}
              />
              <span className="password-toggle" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </span>
            </div>
            {fieldErrors.confirmPassword && (
              <span className="error-text">{fieldErrors.confirmPassword}</span>
            )}
          </div>
          <div className="form-group captcha-group">
            <label>Verification</label>
            <div className="captcha-wrapper">
              <ReCAPTCHA
                ref={recaptchaRef}
                sitekey={RECAPTCHA_SITE_KEY}
                onChange={onCaptchaChange}
              />
            </div>
            {fieldErrors.captcha && (
              <span className="error-text">{fieldErrors.captcha}</span>
            )}
          </div>

          <button
            type="submit"
            className="signup-button"
            disabled={loading || !captchaToken}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Signing Up...
              </>
            ) : (
              "Register"
            )}
          </button>
        </form>

        <p className="login-link">
          Already registered?{" "}
          <Link to="/contractor/login" className="link">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

export default CompanySignup;
