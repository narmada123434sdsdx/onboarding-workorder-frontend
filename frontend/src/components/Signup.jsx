import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import ReCAPTCHA from 'react-google-recaptcha';
import './css/signup.css';
import { BASE_URLS } from '../api/api';

function Signup() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [captchaToken, setCaptchaToken] = useState(null);
  const recaptchaRef = useRef();
  const navigate = useNavigate();

  const RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI";

  const validateForm = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!phoneNumber.trim()) {
      errors.phoneNumber = 'Phone number is required.';
    } else if (!/^\d+$/.test(phoneNumber)) {
      errors.phoneNumber = 'Phone number must contain only digits.';
    } else if (phoneNumber.length !== 10) {
      errors.phoneNumber = 'Please enter exactly 10 digits.';
    }

    if (!email.trim()) {
      errors.email = 'Email is required.';
    } else if (!emailRegex.test(email)) {
      errors.email = 'Please enter a valid email.';
    }

    if (!password.trim()) {
      errors.password = 'Password is required.';
    } else {
      if (password.length < 8) errors.password = 'Password must be at least 8 characters.';
      else if (!/[A-Z]/.test(password)) errors.password = 'Password must contain at least one uppercase letter.';
      else if (!/[a-z]/.test(password)) errors.password = 'Password must contain at least one lowercase letter.';
      else if (!/[0-9]/.test(password)) errors.password = 'Password must contain at least one digit.';
      else if (!/[^A-Za-z0-9]/.test(password)) errors.password = 'Password must contain at least one special character.';
    }

    if (!confirmPassword.trim()) {
      errors.confirmPassword = 'Confirm your password.';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
    }

    if (!captchaToken) {
      errors.captcha = 'Please complete the captcha verification.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!validateForm()) return;

    setLoading(true);
    try {
      const response = await fetch(`${BASE_URLS.user}/api/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          phone_number: phoneNumber, 
          email, 
          password,
          captcha_token: captchaToken 
        }),
      });

      const data = await response.json();
      console.log(data);
      if (response.ok) {
        navigate('/login', {
          state: { message: "The activation link has been sent to your email. Please check your mail to activate your account before login." }
        });
        setPhoneNumber('');
        setEmail('');
        setPassword('');
        setConfirmPassword('');
        recaptchaRef.current.reset();
        setCaptchaToken(null);
      } else {
        setError(data.error || 'Signup failed. Please try again.');
        recaptchaRef.current.reset();
        setCaptchaToken(null);
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
      recaptchaRef.current.reset();
      setCaptchaToken(null);
    } finally {
      setLoading(false);
    }
  };

  const onCaptchaChange = (token) => {
    setCaptchaToken(token);
    if (token) {
      setFieldErrors((prev) => ({ ...prev, captcha: '' }));
    }
  };
  const preventPaste = (e) => {
    e.preventDefault();
  };

  return (
    <div className="signup-container">
      <div className="signup-card">
        <h2 className="signup-title">Create Account</h2>
        <p className="signup-subtitle">Join us today</p>

        {error && <p className="signup-error">{error}</p>}

        <form onSubmit={handleSubmit} className="signup-form">
          {/* Phone Number */}
          <div className="form-group">
            <label htmlFor="phoneNumber">
              Phone Number <span className="required-asterisk">*</span>
            </label>
            <input
              type="tel"
              id="phoneNumber"
              value={phoneNumber}
              onChange={(e) => {
                const value = e.target.value;
                setPhoneNumber(value);
                if (value.length === 10 && /^\d+$/.test(value)) {
                  setFieldErrors((prev) => ({ ...prev, phoneNumber: '' }));
                }
              }}
              placeholder="Enter your phone number"
              disabled={loading}
            />
            {fieldErrors.phoneNumber && <span className="error-text">{fieldErrors.phoneNumber}</span>}
          </div>

          {/* Email */}
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
                  setFieldErrors((prev) => ({ ...prev, email: '' }));
                }
              }}
              placeholder="Enter your email"
              disabled={loading}
            />
            {fieldErrors.email && <span className="error-text">{fieldErrors.email}</span>}
          </div>

          {/* Password */}
          {/* <div className="form-group password-group">
            <label htmlFor="password">Password <span className="required-asterisk">*</span> </label>
            <div className="password-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                value={password}
                onChange={(e) => {
                  const value = e.target.value;
                  setPassword(value);
                  if (value.length >= 8 && /[A-Z]/.test(value) && /[a-z]/.test(value) && /[0-9]/.test(value) && /[^A-Za-z0-9]/.test(value)) {
                    setFieldErrors((prev) => ({ ...prev, password: '' }));
                  }
                }}
                placeholder="Create a password"
                disabled={loading}
              />
              <span className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </span>
            </div>
            {fieldErrors.password && <span className="error-text">{fieldErrors.password}</span>}
          </div>

          {/* Confirm Password */}
          {/* <div className="form-group password-group">
            <label htmlFor="confirmPassword">Confirm Password <span className="required-asterisk">*</span> </label>
            <div className="password-wrapper">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => {
                  const value = e.target.value;
                  setConfirmPassword(value);
                  if (value === password) {
                    setFieldErrors((prev) => ({ ...prev, confirmPassword: '' }));
                  }
                }}
                placeholder="Confirm your password"
                disabled={loading}
              />
              <span className="password-toggle" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </span>
            </div>
            {fieldErrors.confirmPassword && <span className="error-text">{fieldErrors.confirmPassword}</span>}
          </div>  */}
          <div className="form-group password-group">
            <label htmlFor="password">Password <span className="required-asterisk">*</span> </label>
            <div className="password-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                value={password}
                onChange={(e) => {
                  const value = e.target.value;
                  setPassword(value);
                  if (value.length >= 8 && /[A-Z]/.test(value) && /[a-z]/.test(value) && /[0-9]/.test(value) && /[^A-Za-z0-9]/.test(value)) {
                    setFieldErrors((prev) => ({ ...prev, password: '' }));
                  }
                }}
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

          {/* Confirm Password */}
          <div className="form-group password-group">
            <label htmlFor="confirmPassword">Confirm Password <span className="required-asterisk">*</span> </label>
            <div className="password-wrapper">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => {
                  const value = e.target.value;
                  setConfirmPassword(value);
                  if (value === password) {
                    setFieldErrors((prev) => ({ ...prev, confirmPassword: '' }));
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
            {fieldErrors.confirmPassword && <span className="error-text">{fieldErrors.confirmPassword}</span>}
          </div>

          {/* Captcha */}
          <div className="form-group captcha-group">
            <label>Verification</label>
            <div className="captcha-wrapper">
              <ReCAPTCHA
                ref={recaptchaRef}
                sitekey={RECAPTCHA_SITE_KEY}
                onChange={onCaptchaChange}
              />
            </div>
            {fieldErrors.captcha && <span className="error-text">{fieldErrors.captcha}</span>}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="signup-button"
            disabled={loading || Object.values(fieldErrors).some((msg) => msg) || !captchaToken}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Signing Up...
              </>
            ) : (
              'Sign Up'
            )}
          </button>
        </form>

        <p className="login-link">
          Already have an account?{' '}
          <Link to="/login" className="link">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Signup;